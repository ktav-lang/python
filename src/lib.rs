//! Python bindings for the Ktav configuration format.
//!
//! Compiled into the `ktav._core` CPython extension. The pure-Python layer
//! under `python/ktav/__init__.py` re-exports everything a user is meant
//! to touch; this file focuses on the FFI boundary itself.
//!
//! ## Type mapping
//!
//! | Ktav                        | Python      |
//! |-----------------------------|-------------|
//! | `null`                      | `None`      |
//! | `true` / `false`            | `bool`      |
//! | integer literal (§ 3.6)     | `int`       |
//! | float literal (§ 3.6)       | `float`     |
//! | bare / `::` scalar          | `str`       |
//! | `[ ... ]` / `[i, …]`        | `list`      |
//! | `{ ... }` / `{k: v, …}`     | `dict`      |
//!
//! Under spec 0.5.0 types are inferred from the scalar's lexical form
//! (§ 3.6). The raw `::` marker forces a String even for digit-only bodies.

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
                "NaN / Infinity is not representable in Ktav",
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

/// Render a top-level Value as a Ktav document string, implementing the
/// spec § 5.9.3 disambiguation rule:
///
/// - An empty top-level Array renders as `[]\n` per § 5.9.3.
/// - When a top-level Array's first item is a non-empty Array or non-empty
///   Object (which would render starting with a lone `[` or `{`, causing
///   the parser to misidentify it as the root opener), the whole top-level
///   Array is wrapped in explicit `[\n…\n]\n` brackets with each item
///   indented by 4 spaces (one indent level).
///
/// All other cases delegate directly to `render::render`.
fn render_top_level(value: &Value) -> ktav::Result<String> {
    match value {
        Value::Array(items) => {
            if items.is_empty() {
                return Ok("[]\n".to_string());
            }
            let needs_wrap = matches!(
                items.first(),
                Some(Value::Array(a)) if !a.is_empty()
            ) || matches!(
                items.first(),
                Some(Value::Object(o)) if !o.is_empty()
            );
            if needs_wrap {
                let bare = render::render(value)?;
                let mut out = String::with_capacity(bare.len() + 32);
                out.push_str("[\n");
                for line in bare.lines() {
                    out.push_str("    ");
                    out.push_str(line);
                    out.push('\n');
                }
                out.push_str("]\n");
                Ok(out)
            } else {
                render::render(value)
            }
        }
        _ => render::render(value),
    }
}

/// Coerce every scalar in `value` to a String, mirroring
/// `ktav::render::to_string_force_strings` but without the top-level
/// Array disambiguation gap.
fn force_strings_top_level(value: &Value) -> Value {
    match value {
        Value::Null => Value::String(Scalar::from("null")),
        Value::Bool(true) => Value::String(Scalar::from("true")),
        Value::Bool(false) => Value::String(Scalar::from("false")),
        Value::Integer(s) | Value::Float(s) | Value::String(s) => Value::String(s.clone()),
        Value::Array(items) => Value::Array(items.iter().map(force_strings_top_level).collect()),
        Value::Object(obj) => {
            let mut out = ObjectMap::with_capacity_and_hasher(obj.len(), FxBuildHasher);
            for (k, v) in obj {
                out.insert(k.clone(), force_strings_top_level(v));
            }
            Value::Object(out)
        }
    }
}

/// Serialize a Python value as a Ktav document. The top-level value must
/// be a `dict` or a `list` / `tuple` (spec § 5.0.1, added 0.1.1).
/// Top-level Arrays render as bare item-per-line — no surrounding
/// `[...]` brackets.
#[pyfunction]
#[pyo3(text_signature = "(obj, /)")]
fn dumps(obj: &Bound<'_, PyAny>) -> PyResult<String> {
    let value = py_to_value(obj)?;
    if !matches!(value, Value::Object(_) | Value::Array(_)) {
        return Err(KtavEncodeError::new_err(
            "Top-level Ktav value must be a dict or a list/tuple",
        ));
    }
    render_top_level(&value).map_err(|e| KtavEncodeError::new_err(e.to_string()))
}

/// Emit the canonical (normalised) form of a Python value as a Ktav document
/// (spec § 5.9). The output is byte-deterministic across all compliant
/// implementations: numbers are normalised, redundant whitespace is stripped,
/// and inline forms are expanded to multi-line. The top-level value must be a
/// `dict` or a `list` / `tuple`.
#[pyfunction]
#[pyo3(text_signature = "(obj, /)")]
fn emit_canonical(obj: &Bound<'_, PyAny>) -> PyResult<String> {
    let value = py_to_value(obj)?;
    if !matches!(value, Value::Object(_) | Value::Array(_)) {
        return Err(KtavEncodeError::new_err(
            "Top-level Ktav value must be a dict or a list/tuple",
        ));
    }
    ktav::emit_canonical(&value).map_err(|e| KtavEncodeError::new_err(e.to_string()))
}

/// Serialize a Python value as a Ktav document with **every scalar
/// coerced to a String**. Typed integers, typed floats, booleans, and
/// `None` are flattened to their textual form and emitted via the raw
/// `::` marker so the output round-trips back through the parser as
/// the same string scalars. Compounds (dict / list) preserve their
/// structure; only leaf scalars are coerced.
///
/// Useful for "everything is a string" downstream consumers — e.g.
/// environment variables, or diffs where the textual form is the
/// canonical source of truth.
#[pyfunction]
#[pyo3(text_signature = "(obj, /)")]
fn dumps_force_strings(obj: &Bound<'_, PyAny>) -> PyResult<String> {
    let value = py_to_value(obj)?;
    if !matches!(value, Value::Object(_) | Value::Array(_)) {
        return Err(KtavEncodeError::new_err(
            "Top-level Ktav value must be a dict or a list/tuple",
        ));
    }
    // to_string_force_strings coerces scalars and then calls render::render
    // internally, which doesn't handle the top-level Array disambiguation.
    // We replicate the coercion here then route through render_top_level.
    let coerced = force_strings_top_level(&value);
    render_top_level(&coerced).map_err(|e| KtavEncodeError::new_err(e.to_string()))
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add("__spec_version__", "0.5.0")?;

    m.add_function(wrap_pyfunction!(loads, m)?)?;
    m.add_function(wrap_pyfunction!(dumps, m)?)?;
    m.add_function(wrap_pyfunction!(emit_canonical, m)?)?;
    m.add_function(wrap_pyfunction!(dumps_force_strings, m)?)?;

    let py = m.py();
    m.add("KtavError", py.get_type::<KtavError>())?;
    m.add("KtavDecodeError", py.get_type::<KtavDecodeError>())?;
    m.add("KtavEncodeError", py.get_type::<KtavEncodeError>())?;

    Ok(())
}
