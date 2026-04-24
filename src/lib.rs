//! Python bindings for the Ktav configuration format.
//!
//! Compiled into the `ktav._core` CPython extension. The pure-Python layer
//! under `python/ktav/__init__.py` re-exports everything a user is meant
//! to touch; this file focuses on the FFI boundary itself.
//!
//! ## Type mapping
//!
//! | Ktav               | Python      |
//! |--------------------|-------------|
//! | `null`             | `None`      |
//! | `true` / `false`   | `bool`      |
//! | `:i <digits>`      | `int`       |
//! | `:f <number>`      | `float`     |
//! | bare scalar        | `str`       |
//! | `[ ... ]`          | `list`      |
//! | `{ ... }`          | `dict`      |
//!
//! The format keeps numbers as strings at the `Value` level by design —
//! this layer does the marker-aware conversion so the Python side gets
//! native `int` / `float` where markers asked for them.

use ktav::render;
use ktav::value::{ObjectMap, Scalar, Value};
use pyo3::create_exception;
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict, PyFloat, PyInt, PyList, PyString, PyTuple};
use rustc_hash::FxBuildHasher;

create_exception!(_core, KtavError, pyo3::exceptions::PyException);
create_exception!(_core, KtavDecodeError, KtavError);
create_exception!(_core, KtavEncodeError, KtavError);

/// Map a `ktav::Value` to a native Python object.
fn value_to_py<'py>(py: Python<'py>, value: &Value) -> PyResult<Bound<'py, PyAny>> {
    Ok(match value {
        Value::Null => py.None().into_bound(py),
        Value::Bool(b) => b.into_pyobject(py)?.to_owned().into_any(),
        Value::Integer(s) => {
            // Fast path: most config integers (ports, timeouts, counts)
            // fit in i64 — `into_pyobject` routes straight to
            // `PyLong_FromLongLong`, no string parsing. Arbitrary-precision
            // literals fall back to `int(str)` so bigint round-trip holds.
            if let Ok(v) = s.as_str().parse::<i64>() {
                v.into_pyobject(py)?.into_any()
            } else {
                py.get_type::<PyInt>().call1((s.as_str(),)).map_err(|_| {
                    KtavDecodeError::new_err(format!("Invalid Integer literal: {}", s.as_str()))
                })?
            }
        }
        Value::Float(s) => {
            let v: f64 = s.as_str().parse().map_err(|_| {
                KtavDecodeError::new_err(format!("Invalid Float literal: {}", s.as_str()))
            })?;
            v.into_pyobject(py)?.into_any()
        }
        Value::String(s) => s.as_str().into_pyobject(py)?.into_any(),
        Value::Array(items) => {
            let list = PyList::empty(py);
            for item in items {
                list.append(value_to_py(py, item)?)?;
            }
            list.into_any()
        }
        Value::Object(obj) => {
            let dict = PyDict::new(py);
            for (k, v) in obj.iter() {
                dict.set_item(k.as_str(), value_to_py(py, v)?)?;
            }
            dict.into_any()
        }
    })
}

/// Map a native Python object to a `ktav::Value`.
///
/// Order matters: `bool` is a subclass of `int` in Python, so the bool
/// branch must come first — otherwise `True` is silently encoded as
/// Integer `"1"`, which is not what the user wrote.
fn py_to_value(obj: &Bound<'_, PyAny>) -> PyResult<Value> {
    if obj.is_none() {
        return Ok(Value::Null);
    }
    if let Ok(b) = obj.cast::<PyBool>() {
        return Ok(Value::Bool(b.is_true()));
    }
    if let Ok(i) = obj.cast::<PyInt>() {
        // Gate the fast path on `cast::<PyInt>` first — calling
        // `extract::<i64>` on an arbitrary object is not free (it can
        // invoke `__int__`, which for a string or list means a full
        // TypeError roundtrip). Once we know `i` is an `int`, the extract
        // is just `PyLong_AsLongLongAndOverflow` — cheap and overflow-safe.
        if let Ok(v) = i.extract::<i64>() {
            let mut buf = itoa::Buffer::new();
            return Ok(Value::Integer(Scalar::from(buf.format(v))));
        }
        // Arbitrary-precision branch: round-trip through Python's str form.
        let s: String = i.str()?.extract()?;
        return Ok(Value::Integer(Scalar::from(s)));
    }
    if let Ok(f) = obj.cast::<PyFloat>() {
        let v: f64 = f.extract()?;
        if v.is_nan() || v.is_infinite() {
            return Err(KtavEncodeError::new_err(
                "NaN / Infinity is not representable in Ktav 0.1.0",
            ));
        }
        return Ok(Value::Float(Scalar::from(format_float(v))));
    }
    if let Ok(s) = obj.cast::<PyString>() {
        // `to_str` is gated on `!Py_LIMITED_API || Py_3_10`; we target
        // abi3-py39 so it's unavailable. `to_cow` is always there.
        return Ok(Value::String(Scalar::from(s.to_cow()?.as_ref())));
    }
    if let Ok(list) = obj.cast::<PyList>() {
        let mut arr = Vec::with_capacity(list.len());
        for item in list.iter() {
            arr.push(py_to_value(&item)?);
        }
        return Ok(Value::Array(arr));
    }
    if let Ok(tuple) = obj.cast::<PyTuple>() {
        let mut arr = Vec::with_capacity(tuple.len());
        for item in tuple.iter() {
            arr.push(py_to_value(&item)?);
        }
        return Ok(Value::Array(arr));
    }
    if let Ok(dict) = obj.cast::<PyDict>() {
        // Preallocate — avoids repeated rehashing as the map grows.
        let mut map = ObjectMap::with_capacity_and_hasher(dict.len(), FxBuildHasher);
        for (k, v) in dict.iter() {
            let key_py = k
                .cast::<PyString>()
                .map_err(|_| KtavEncodeError::new_err("Object keys must be strings"))?;
            let key_cow = key_py.to_cow()?;
            map.insert(Scalar::from(key_cow.as_ref()), py_to_value(&v)?);
        }
        return Ok(Value::Object(map));
    }
    let class_name = obj
        .get_type()
        .name()
        .ok()
        .and_then(|b| b.to_cow().ok().map(|c| c.into_owned()))
        .unwrap_or_else(|| "unknown".to_string());
    Err(KtavEncodeError::new_err(format!(
        "Unsupported Python type for Ktav: {class_name}"
    )))
}

/// Format `f64` with a mandatory decimal point in the mantissa — Ktav's
/// Float grammar requires `N.N` at a minimum, but `ryu` emits `1e100`
/// without one for large values. Inserts `.0` right before the exponent.
fn format_float(v: f64) -> String {
    let mut buf = ryu::Buffer::new();
    let s = buf.format(v);
    let bytes = s.as_bytes();
    let mut e_pos: Option<usize> = None;
    let mut has_dot = false;
    for (i, &b) in bytes.iter().enumerate() {
        if b == b'.' {
            has_dot = true;
        } else if b == b'e' || b == b'E' {
            e_pos = Some(i);
            break;
        }
    }
    match (e_pos, has_dot) {
        (_, true) => s.to_string(),
        (Some(pos), false) => {
            let mut out = String::with_capacity(s.len() + 2);
            out.push_str(&s[..pos]);
            out.push_str(".0");
            out.push_str(&s[pos..]);
            out
        }
        (None, false) => {
            let mut out = String::with_capacity(s.len() + 2);
            out.push_str(s);
            out.push_str(".0");
            out
        }
    }
}

/// Parse a Ktav document and return the equivalent Python value.
#[pyfunction]
#[pyo3(text_signature = "(s, /)")]
fn loads<'py>(py: Python<'py>, s: &str) -> PyResult<Bound<'py, PyAny>> {
    let value = ktav::parse(s).map_err(|e| KtavDecodeError::new_err(e.to_string()))?;
    value_to_py(py, &value)
}

/// Serialize a Python value as a Ktav document. The top-level value must
/// be a `dict` — Ktav documents are objects.
#[pyfunction]
#[pyo3(text_signature = "(obj, /)")]
fn dumps(obj: &Bound<'_, PyAny>) -> PyResult<String> {
    let value = py_to_value(obj)?;
    if !matches!(value, Value::Object(_)) {
        return Err(KtavEncodeError::new_err(
            "Top-level Ktav value must be a dict",
        ));
    }
    render::render(&value).map_err(|e| KtavEncodeError::new_err(e.to_string()))
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add("__spec_version__", "0.1.0")?;

    m.add_function(wrap_pyfunction!(loads, m)?)?;
    m.add_function(wrap_pyfunction!(dumps, m)?)?;

    let py = m.py();
    m.add("KtavError", py.get_type::<KtavError>())?;
    m.add("KtavDecodeError", py.get_type::<KtavDecodeError>())?;
    m.add("KtavEncodeError", py.get_type::<KtavEncodeError>())?;

    Ok(())
}
