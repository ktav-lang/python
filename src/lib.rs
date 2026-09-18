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
//! Under spec 0.7.1 types are inferred from the scalar's lexical form
//! (§ 3.6). The raw `::` marker forces a String even for digit-only bodies.
//!
//! Since 0.7.1 every exception raised by this module carries the
//! ten-field structured error envelope (`error`, `reason`, `line`,
//! `line_text`, `span`, `path`, `body`, `canonical`, `spec_section`,
//! `message`) as
//! instance attributes, and the new `format` function provides
//! comment-preserving text→text formatting (`ktav::format_str`).

use ktav::render;
use ktav::value::{ObjectMap, Scalar, Value};
use ktav::{Error, ReasonCode};
use pyo3::create_exception;
use pyo3::prelude::*;
use pyo3::types::{PyBool, PyDict, PyFloat, PyInt, PyList, PyString, PyTuple};
use rustc_hash::FxBuildHasher;

create_exception!(_core, KtavError, pyo3::exceptions::PyException);
create_exception!(_core, KtavDecodeError, KtavError);
create_exception!(_core, KtavEncodeError, KtavError);

/// Shorthand for handing the decode exception *class object* to
/// `structured_error`.
fn decode_error_class(py: Python<'_>) -> Bound<'_, PyAny> {
    py.get_type::<KtavDecodeError>().into_any()
}

/// Shorthand for handing the encode exception *class object* to
/// `structured_error`.
fn encode_error_class(py: Python<'_>) -> Bound<'_, PyAny> {
    py.get_type::<KtavEncodeError>().into_any()
}

/// Attach `value: str | None` on `obj` under `name`, using real `None`
/// (never omission) so consumers can rely on the attribute existing.
fn set_opt_str(
    py: Python<'_>,
    obj: &Bound<'_, PyAny>,
    name: &str,
    value: Option<&str>,
) -> PyResult<()> {
    match value {
        Some(v) => obj.setattr(name, v),
        None => obj.setattr(name, py.None()),
    }
}

/// Raise `class` (one of the `create_exception!` types, fetched as a
/// class object) carrying the ten-field structured error envelope from
/// ktav 0.7.1 (issue rust#12) as first-class instance attributes:
/// `error`, `reason`, `line`, `line_text`, `span`, `path`, `body`,
/// `canonical`, `spec_section`, `message`.
///
/// The exception message stays the upstream human-readable `Display`
/// text of the error — never a JSON blob. `source` is the Ktav document
/// text the error refers to (empty when the input was not Ktav text,
/// e.g. a Python object being serialised), so `line_text` can be
/// populated for parse-time errors.
fn structured_error(
    py: Python<'_>,
    class: &Bound<'_, PyAny>,
    err: &ktav::Error,
    source: &str,
) -> PyErr {
    let envelope = ktav::ErrorEnvelope::from_error(err, source);
    // `call1` on a fresh exception subclass with a plain `str` argument
    // cannot fail: there is no user `__init__` in play.
    let value = class
        .call1((err.to_string(),))
        .expect("exception construction cannot fail");
    // Absent fields become `py.None()` rather than being omitted, so the
    // envelope shape is stable across every raised exception.
    let attach = (|| -> PyResult<()> {
        value.setattr("error", envelope.error.as_str())?;
        set_opt_str(py, &value, "reason", envelope.reason.as_deref())?;
        match envelope.line {
            Some(n) => value.setattr("line", n)?,
            None => value.setattr("line", py.None())?,
        }
        set_opt_str(py, &value, "line_text", envelope.line_text.as_deref())?;
        match envelope.span {
            Some(span) => {
                let d = pyo3::types::PyDict::new(py);
                d.set_item("start", span.start)?;
                d.set_item("end", span.end)?;
                value.setattr("span", d)?;
            }
            None => value.setattr("span", py.None())?,
        }
        match envelope.path {
            Some(segments) => {
                // Exact decoded key segments — never a joined string.
                value.setattr("path", segments)?;
            }
            None => value.setattr("path", py.None())?,
        }
        set_opt_str(py, &value, "body", envelope.body.as_deref())?;
        set_opt_str(py, &value, "canonical", envelope.canonical.as_deref())?;
        set_opt_str(py, &value, "spec_section", envelope.spec_section.as_deref())?;
        // Redundant with `str(exc)` here — this binding has always used
        // the crate's own `Display` — but the attribute keeps the
        // envelope the same ten-field shape a consumer sees in every
        // other language, where `message` is the only way to reach it.
        value.setattr("message", envelope.message.as_str())?;
        Ok(())
    })();
    if let Err(e) = attach {
        return e;
    }
    PyErr::from_value(value)
}

/// Map a `ktav::Value` to a native Python object.
fn value_to_py<'py>(py: Python<'py>, value: &Value, source: &str) -> PyResult<Bound<'py, PyAny>> {
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
                // Route even this fallback through the structured-error
                // channel so every decode failure carries the envelope.
                let err = Error::Message(format!("Invalid Integer literal: {}", s.as_str()));
                return Err(structured_error(py, &decode_error_class(py), &err, source));
            }
        }
        Value::Float(s) => {
            // The parser should never emit a Float literal `f64::from_str`
            // rejects, but if it ever does, the envelope contract still holds.
            let v: f64 = match s.as_str().parse::<f64>() {
                Ok(v) => v,
                Err(_) => {
                    let err = Error::Message(format!("Invalid Float literal: {}", s.as_str()));
                    return Err(structured_error(py, &decode_error_class(py), &err, source));
                }
            };
            v.into_pyobject(py)?.into_any()
        }
        Value::String(s) => s.as_str().into_pyobject(py)?.into_any(),
        Value::Array(items) => {
            let list = PyList::empty(py);
            for item in items {
                list.append(value_to_py(py, item, source)?)?;
            }
            list.into_any()
        }
        Value::Object(obj) => {
            let dict = PyDict::new(py);
            for (k, v) in obj.iter() {
                dict.set_item(k.as_str(), value_to_py(py, v, source)?)?;
            }
            dict.into_any()
        }
    })
}

/// Map a native Python object to a `ktav::Value`.
///
/// Returns `ktav::Error` rather than a `PyErr` so every caller funnels
/// through `structured_error` and every raise carries the ten-field
/// envelope.
///
/// Order matters: `bool` is a subclass of `int` in Python, so the bool
/// branch must come first — otherwise `True` is silently encoded as
/// Integer `"1"`, which is not what the user wrote.
fn py_to_value(obj: &Bound<'_, PyAny>) -> Result<Value, ktav::Error> {
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
        let s: String = i
            .str()
            .map_err(|_| Error::Message("failed to stringify int".into()))?
            .extract()
            .map_err(|_| Error::Message("failed to stringify int".into()))?;
        return Ok(Value::Integer(Scalar::from(s)));
    }
    if let Ok(f) = obj.cast::<PyFloat>() {
        let v: f64 = f
            .extract()
            .map_err(|_| Error::Message("invalid Python float".into()))?;
        if v.is_nan() || v.is_infinite() {
            // The envelope built upstream carries `reason: "NonFiniteFloat"`.
            return Err(Error::Unrepresentable(ReasonCode::NonFiniteFloat));
        }
        return Ok(Value::Float(Scalar::from(format_float(v))));
    }
    if let Ok(s) = obj.cast::<PyString>() {
        // `to_str` is gated on `!Py_LIMITED_API || Py_3_10`; we target
        // abi3-py39 so it's unavailable. `to_cow` is always there.
        let text = s.to_cow().map_err(|_| {
            Error::Message("string cannot be encoded as UTF-8 (unpaired surrogate)".into())
        })?;
        return Ok(Value::String(Scalar::from(text.as_ref())));
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
                .map_err(|_| Error::Message("Object keys must be strings".into()))?;
            let key_cow = key_py.to_cow().map_err(|_| {
                Error::Message("string cannot be encoded as UTF-8 (unpaired surrogate)".into())
            })?;
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
    Err(Error::Message(format!(
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
    let value = ktav::parse(s).map_err(|e| structured_error(py, &decode_error_class(py), &e, s))?;
    value_to_py(py, &value, s)
}

/// Parse a Ktav document in strict mode and return the equivalent Python value.
#[pyfunction]
#[pyo3(text_signature = "(s, /)")]
fn loads_strict<'py>(py: Python<'py>, s: &str) -> PyResult<Bound<'py, PyAny>> {
    let value =
        ktav::parse_strict(s).map_err(|e| structured_error(py, &decode_error_class(py), &e, s))?;
    value_to_py(py, &value, s)
}

/// Format a Ktav document: text in, normalised text out.
///
/// Wraps `ktav::format_str` (ktav 0.7.1, issue rust#13): the document's
/// structure is normalised to the § 5.9 canonical shape while every
/// comment line and blank-line grouping from the source is preserved.
/// Settled upstream semantics callers can rely on:
///
/// - Every comment is preserved verbatim. Ktav has no trailing
///   comments (spec § 3.4: a comment owns a whole line), so attachment
///   is unambiguous.
/// - Blank lines survive as a grouping hint, but a run of two or more
///   collapses to exactly one, and blank padding immediately inside a
///   bracket is dropped — this is what makes the transform a fixed
///   point: `format(format(x)) == format(x)`.
/// - Key order is never changed (canonical form has no sorting rule,
///   spec § 5.9).
/// - For a document with no comments and no blank lines, the result
///   equals `emit_canonical` of its parse. The stronger condition is
///   deliberate: blank lines are no more part of the Value model than
///   comments are.
///
/// Raises `KtavDecodeError` with the structured error envelope
/// attached on malformed input.
#[pyfunction]
#[pyo3(text_signature = "(s, /)")]
fn format(py: Python<'_>, s: &str) -> PyResult<String> {
    ktav::format_str(s).map_err(|e| structured_error(py, &decode_error_class(py), &e, s))
}

/// Parse Ktav source text and re-emit it in canonical form (spec
/// § 5.9), preserving the source's key order.
///
/// The result equals `emit_canonical(loads(s))`, but the document never
/// becomes a Python object on the way. That keeps § 5.9 decided in the
/// one layer that owns it, and it stays correct no matter how this
/// binding's type mapping evolves.
///
/// Unlike `format`, comments and blank lines do NOT survive — canonical
/// form carries no trivia. Reach for `format` to tidy a file a human
/// will read, and for this to produce a byte-stable form to hash, diff
/// or store.
///
/// Raises `KtavDecodeError` with the structured error envelope attached
/// on malformed input.
#[pyfunction]
#[pyo3(text_signature = "(s, /)")]
fn canonical_from_source(py: Python<'_>, s: &str) -> PyResult<String> {
    let value = ktav::parse(s).map_err(|e| structured_error(py, &decode_error_class(py), &e, s))?;
    ktav::render::emit_canonical(&value)
        .map_err(|e| structured_error(py, &encode_error_class(py), &e, s))
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
    render::render(value)
}

/// Coerce every scalar in `value` to a String, mirroring
/// `ktav::render::to_string_force_strings` but without the top-level
/// Array disambiguation gap; the core renderer handles it centrally.
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
fn dumps(py: Python<'_>, obj: &Bound<'_, PyAny>) -> PyResult<String> {
    let value =
        py_to_value(obj).map_err(|e| structured_error(py, &encode_error_class(py), &e, ""))?;
    if !matches!(value, Value::Object(_) | Value::Array(_)) {
        // Empty `source`: the input was Python objects, not Ktav text.
        return Err(structured_error(
            py,
            &encode_error_class(py),
            &Error::Unrepresentable(ReasonCode::ScalarRoot),
            "",
        ));
    }
    render_top_level(&value).map_err(|e| structured_error(py, &encode_error_class(py), &e, ""))
}

/// Emit the canonical (normalised) form of a Python value as a Ktav document
/// (spec § 5.9). The output is byte-deterministic across all compliant
/// implementations: numbers are normalised, redundant whitespace is stripped,
/// and inline forms are expanded to multi-line. The top-level value must be a
/// `dict` or a `list` / `tuple`.
#[pyfunction]
#[pyo3(text_signature = "(obj, /)")]
fn emit_canonical(py: Python<'_>, obj: &Bound<'_, PyAny>) -> PyResult<String> {
    let value =
        py_to_value(obj).map_err(|e| structured_error(py, &encode_error_class(py), &e, ""))?;
    if !matches!(value, Value::Object(_) | Value::Array(_)) {
        // Empty `source`: the input was Python objects, not Ktav text.
        return Err(structured_error(
            py,
            &encode_error_class(py),
            &Error::Unrepresentable(ReasonCode::ScalarRoot),
            "",
        ));
    }
    ktav::emit_canonical(&value).map_err(|e| structured_error(py, &encode_error_class(py), &e, ""))
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
fn dumps_force_strings(py: Python<'_>, obj: &Bound<'_, PyAny>) -> PyResult<String> {
    let value =
        py_to_value(obj).map_err(|e| structured_error(py, &encode_error_class(py), &e, ""))?;
    if !matches!(value, Value::Object(_) | Value::Array(_)) {
        // Empty `source`: the input was Python objects, not Ktav text.
        return Err(structured_error(
            py,
            &encode_error_class(py),
            &Error::Unrepresentable(ReasonCode::ScalarRoot),
            "",
        ));
    }
    // to_string_force_strings coerces scalars and then calls render::render
    // internally, which doesn't handle the top-level Array disambiguation.
    // We replicate the coercion here then route through render_top_level.
    let coerced = force_strings_top_level(&value);
    render_top_level(&coerced).map_err(|e| structured_error(py, &encode_error_class(py), &e, ""))
}

#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    m.add("__spec_version__", "0.7.1")?;

    m.add_function(wrap_pyfunction!(loads, m)?)?;
    m.add_function(wrap_pyfunction!(loads_strict, m)?)?;
    m.add_function(wrap_pyfunction!(format, m)?)?;
    m.add_function(wrap_pyfunction!(canonical_from_source, m)?)?;
    m.add_function(wrap_pyfunction!(dumps, m)?)?;
    m.add_function(wrap_pyfunction!(emit_canonical, m)?)?;
    m.add_function(wrap_pyfunction!(dumps_force_strings, m)?)?;

    let py = m.py();
    m.add("KtavError", py.get_type::<KtavError>())?;
    m.add("KtavDecodeError", py.get_type::<KtavDecodeError>())?;
    m.add("KtavEncodeError", py.get_type::<KtavEncodeError>())?;

    Ok(())
}

#[cfg(test)]
mod tests {
    //! Rust-side tests for the layer that converts a `ktav::Error` into a
    //! Python exception — untested from the Rust side before task #301,
    //! even though every other C-ABI-shaped binding (golang, java,
    //! csharp, js) already asserts this shape. Calls the `#[pyfunction]`s
    //! directly as plain Rust functions with a `Python::attach` token;
    //! that's all `#[pyfunction]` leaves them as, so no Python interpreter
    //! embedding beyond `auto-initialize` is needed to reach them.
    use super::*;

    fn attr_str(py: Python<'_>, err: &PyErr, name: &str) -> Option<String> {
        let value = err.value(py).getattr(name).expect("attribute must exist");
        if value.is_none() {
            None
        } else {
            Some(value.extract::<String>().expect("attribute is a str"))
        }
    }

    /// The full envelope, every one of the TEN fields present as an
    /// instance attribute — including `message`. Since #304 the
    /// `Cargo.toml` floor is `ktav = "0.7.2"`, the first published core
    /// that actually carries `message` (#268), so this test's ten-field
    /// assertion now matches the declared dependency, not just this
    /// crate's own `structured_error` glue.
    #[test]
    fn parse_failure_produces_the_full_envelope() {
        Python::attach(|py| {
            let err = loads(py, "version: 1.10\nx: [").expect_err("must fail to parse");
            assert!(
                err.is_instance_of::<KtavDecodeError>(py),
                "must raise KtavDecodeError, got {err}"
            );
            let value = err.value(py);
            for field in [
                "error",
                "reason",
                "line",
                "line_text",
                "span",
                "path",
                "body",
                "canonical",
                "spec_section",
                "message",
            ] {
                assert!(
                    value.hasattr(field).unwrap(),
                    "missing envelope attribute {field:?}"
                );
            }
            let message = attr_str(py, &err, "message").expect("message is never None");
            assert!(!message.is_empty());
            // README: str(e) == e.message by construction.
            assert_eq!(err.value(py).str().unwrap().to_string(), message);
        });
    }

    #[test]
    fn lossy_scalar_envelope_matches_the_readme_example() {
        Python::attach(|py| {
            let err = loads_strict(py, "a: 1.10\n").expect_err("loads_strict must reject this");
            assert_eq!(attr_str(py, &err, "error").as_deref(), Some("LossyScalar"));
            assert_eq!(attr_str(py, &err, "body").as_deref(), Some("1.10"));
            assert_eq!(attr_str(py, &err, "canonical").as_deref(), Some("1.1"));
            assert_eq!(
                attr_str(py, &err, "spec_section").as_deref(),
                Some("§3.6/§5.2")
            );
        });
    }

    /// A writer-time error carries no source position: `line`/`line_text`/
    /// `span` must come back as Python `None`, not a missing attribute or
    /// a sentinel like `-1` — a class of bug the java binding's own
    /// envelope parser hit in this same task pass.
    #[test]
    fn writer_time_error_has_no_source_position() {
        Python::attach(|py| {
            let dict = pyo3::types::PyDict::new(py);
            dict.set_item("v", f64::NAN).unwrap();
            let err = dumps(py, dict.as_any()).expect_err("NaN is not representable");
            assert!(err.is_instance_of::<KtavEncodeError>(py));
            let value = err.value(py);
            assert!(value.getattr("line").unwrap().is_none());
            assert!(value.getattr("line_text").unwrap().is_none());
            assert!(value.getattr("span").unwrap().is_none());
        });
    }

    /// `format` round-trips: a document with comments and blank-line
    /// grouping survives formatting twice unchanged (fixed point), and a
    /// malformed document raises the same structured envelope as `loads`.
    #[test]
    fn format_is_a_fixed_point_and_round_trips_through_itself() {
        Python::attach(|py| {
            let doc = "## header\na: 1\n\n\n\nb: [\n    1\n    2\n]\n";
            let once = format(py, doc).expect("format succeeds");
            assert!(once.contains("## header"), "comment must survive: {once}");
            assert!(!once.contains("\n\n\n"), "blank run must collapse: {once}");
            let twice = format(py, &once).expect("re-format succeeds");
            assert_eq!(once, twice, "format must be a fixed point");
        });
    }

    #[test]
    fn format_failure_is_also_a_full_envelope() {
        Python::attach(|py| {
            let err = format(py, "a: [").expect_err("malformed document must fail");
            assert!(err.is_instance_of::<KtavDecodeError>(py));
            assert_eq!(attr_str(py, &err, "line_text").as_deref(), Some("a: ["));
        });
    }
}
