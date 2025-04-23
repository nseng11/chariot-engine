from typing import Dict, List
import pandas as pd

class TradeValidator:
    def __init__(self, max_cash_flow: float = float('inf'),
                 min_efficiency: float = 0.3,
                 max_value_disparity: float = 0.5):
        self.max_cash_flow = max_cash_flow
        self.min_efficiency = min_efficiency
        self.max_value_disparity = max_value_disparity

    def validate_trade(self, trade: Dict) -> tuple[bool, List[str]]:
        """Validate a trade against defined rules"""
        issues = []
        
        # Check cash flow limits
        if trade['total_cash_flow'] > self.max_cash_flow:
            issues.append(f"Cash flow {trade['total_cash_flow']} exceeds limit {self.max_cash_flow}")
            
        # Check value efficiency
        if trade['value_efficiency'] < self.min_efficiency:
            issues.append(f"Value efficiency {trade['value_efficiency']} below minimum {self.min_efficiency}")
            
        # Check value disparity
        value_disparity = trade['max_value_diff'] / trade['avg_watch_value']
        if value_disparity > self.max_value_disparity:
            issues.append(f"Value disparity {value_disparity:.2f} exceeds maximum {self.max_value_disparity}")
            
        # Validate cash flow balance
        if abs(trade['net_cash_flow']) > 0.01:  # Allow for small rounding errors
            issues.append(f"Cash flows don't balance: net flow = {trade['net_cash_flow']}")
            
        return len(issues) == 0, issues

def validate_trade_set(trades_df: pd.DataFrame, validator: TradeValidator) -> pd.DataFrame:
    """Validate a set of trades and add validation status"""
    validation_results = []
    
    for _, trade in trades_df.iterrows():
        is_valid, issues = validator.validate_trade(trade)
        validation_results.append({
            'trade_id': trade['trade_id'],
            'is_valid': is_valid,
            'issues': '; '.join(issues) if issues else 'None'
        })
    
    return pd.DataFrame(validation_results) 