import time
import pandas as pd
from typing import Callable, Dict, Any

def benchmark_simulation(
    rust_sim_fn: Callable,
    python_sim_fn: Callable,
    config_path: str
) -> Dict[str, Any]:
    """
    Benchmark Rust vs Python implementations.
    """
    results = {}
    
    # Benchmark Rust implementation
    start_time = time.time()
    rust_sim_fn(config_path)
    rust_time = time.time() - start_time
    
    # Benchmark Python implementation
    start_time = time.time()
    python_sim_fn(config_path)
    python_time = time.time() - start_time
    
    results = {
        'rust_time': rust_time,
        'python_time': python_time,
        'speedup': python_time / rust_time
    }
    
    return results

if __name__ == "__main__":
    from src.run_periodic_simulation import run_multi_period_simulation as python_sim
    from src_rust.run_periodic_simulation_rust import run_multi_period_simulation_rust as rust_sim
    
    config_path = "configs/config_run_periodic.json"
    results = benchmark_simulation(rust_sim, python_sim, config_path)
    
    print("\n🏃 Performance Comparison:")
    print(f"Python Implementation: {results['python_time']:.2f}s")
    print(f"Rust Implementation: {results['rust_time']:.2f}s")
    print(f"Speedup: {results['speedup']:.2f}x") 