use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Trade {
    pub user_id: String,
    pub have_watch: String,
    pub have_value: f64,
    pub min_acceptable_value: f64,
    pub max_cash_top_up: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TradeLoop {
    pub loop_type: String,
    pub users: Vec<String>,
    pub watches: Vec<String>,
    pub values: Vec<f64>,
    pub cash_flows: Vec<f64>,
    pub total_watch_value: f64,
    pub total_cash_flow: f64,
    pub value_efficiency: f64,
    pub relative_fairness_score: f64,
} 