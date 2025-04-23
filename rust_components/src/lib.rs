pub mod graph_matching;
pub mod validation;
pub mod trade_simulation;
pub mod user_generation;

#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pymodule]
fn chariot_engine_core(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<graph_matching::TradeGraph>()?;
    m.add_class::<validation::TradeValidator>()?;
    m.add_class::<trade_simulation::TradeSimulator>()?;
    m.add_class::<user_generation::UserGenerator>()?;
    Ok(())
} 