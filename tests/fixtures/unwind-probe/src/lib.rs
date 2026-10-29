use pyo3::prelude::*;

#[pyfunction]
fn panic_probe() {
    panic!("musllinux unwind probe");
}

#[pymodule]
fn _unwind_probe(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(panic_probe, module)?)
}
