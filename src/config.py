from dataclasses import dataclass
from typing import Optional
import yaml

@dataclass
class TradeConfig:
    min_acceptable_value: float
    max_cash_top_up: float
    min_efficiency: float
    max_value_disparity: float
    fairness_threshold: float

@dataclass
class SimulationConfig:
    max_rounds: int
    min_trades_per_round: int
    trade_config: TradeConfig
    output_directory: str
    generate_reports: bool
    save_visualizations: bool

def load_config(config_path: str) -> SimulationConfig:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    
    trade_config = TradeConfig(**config_data['trade_config'])
    return SimulationConfig(**config_data['simulation'], trade_config=trade_config) 