use pyo3::prelude::*;
use std::cell::RefCell;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

struct TlsProbe(Arc<AtomicBool>);

impl Drop for TlsProbe {
    fn drop(&mut self) {
        self.0.store(true, Ordering::Release);
    }
}

thread_local! {
    static TLS_PROBE: RefCell<Option<TlsProbe>> = const { RefCell::new(None) };
}

#[pyfunction]
fn tls_drop_probe() -> bool {
    let dropped = Arc::new(AtomicBool::new(false));
    let marker = Arc::clone(&dropped);
    let worker = std::thread::spawn(move || {
        TLS_PROBE.with(|slot| *slot.borrow_mut() = Some(TlsProbe(marker)));
    });
    if worker.join().is_err() {
        return false;
    }
    dropped.load(Ordering::Acquire)
}

#[pyfunction]
fn panic_probe() {
    panic!("musllinux unwind probe");
}

#[pymodule]
fn _unwind_probe(module: &Bound<'_, PyModule>) -> PyResult<()> {
    module.add_function(wrap_pyfunction!(panic_probe, module)?)?;
    module.add_function(wrap_pyfunction!(tls_drop_probe, module)?)
}
