use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};
use rand::seq::SliceRandom;
use rayon::prelude::*;

#[derive(Debug, Serialize, Deserialize)]
pub struct Trade {
    pub user_id: String,
    pub have_watch: String,
    pub have_value: f64,
    pub min_acceptable_item_value: f64,
    pub max_cash_top_up: f64,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct TradeLoop {
    pub loop_type: String,
    pub indexes: Vec<usize>,
    pub users: Vec<String>,
    pub watches: Vec<String>,
    pub values: Vec<f64>,
    pub cash_flows: Vec<f64>,
    pub total_watch_value: f64,
    pub total_cash_flow: f64,
    pub value_efficiency: f64,
}

#[pyclass]
pub struct TradeGraph {
    trades: Vec<Trade>,
    edges: Vec<Vec<usize>>,  // Adjacency list representation
}

#[pymethods]
impl TradeGraph {
    #[new]
    fn new() -> Self {
        TradeGraph {
            trades: Vec::new(),
            edges: Vec::new(),
        }
    }

    fn build_from_trades(&mut self, trades: Vec<Trade>) {
        self.trades = trades;
        let n = self.trades.len();
        self.edges = vec![Vec::new(); n];

        // Build edges in parallel using rayon
        let edge_pairs: Vec<(usize, usize)> = (0..n)
            .into_par_iter()
            .flat_map(|i| {
                let mut edges = Vec::new();
                for j in 0..n {
                    if i != j && self.is_valid_trade(i, j) {
                        edges.push((i, j));
                    }
                }
                edges
            })
            .collect();

        // Add edges to adjacency list
        for (i, j) in edge_pairs {
            self.edges[i].push(j);
        }
    }

    fn find_loops(&self, max_loops: usize) -> Vec<TradeLoop> {
        let mut loops = Vec::new();
        let mut rng = rand::thread_rng();
        
        // Find 2-way loops
        self.find_two_way_loops(&mut loops, max_loops / 2);
        
        // If we have space for more loops, find 3-way loops
        if loops.len() < max_loops {
            self.find_three_way_loops(&mut loops, max_loops - loops.len());
        }
        
        loops
    }

    fn to_python(&self, py: Python) -> PyResult<PyObject> {
        let json = serde_json::to_string(&self.trades).unwrap();
        Ok(json.to_object(py))
    }
}

impl TradeGraph {
    fn is_valid_trade(&self, from: usize, to: usize) -> bool {
        let giver = &self.trades[from];
        let receiver = &self.trades[to];
        
        giver.have_watch != receiver.have_watch &&
        giver.have_value >= receiver.min_acceptable_item_value &&
        (giver.have_value - receiver.have_value) <= receiver.max_cash_top_up
    }

    fn find_two_way_loops(&self, loops: &mut Vec<TradeLoop>, max_loops: usize) {
        for i in 0..self.trades.len() {
            if loops.len() >= max_loops {
                break;
            }
            
            for &j in &self.edges[i] {
                if i < j && self.edges[j].contains(&i) {
                    loops.push(self.create_loop_data(vec![i, j], "2-way"));
                    if loops.len() >= max_loops {
                        break;
                    }
                }
            }
        }
    }

    fn find_three_way_loops(&self, loops: &mut Vec<TradeLoop>, max_loops: usize) {
        let n = self.trades.len();
        let mut nodes: Vec<usize> = (0..n).collect();
        let mut rng = rand::thread_rng();
        
        // For large graphs, use sampling
        if n > 100 {
            let mut attempts = 0;
            let max_attempts = max_loops * 10;
            
            while loops.len() < max_loops && attempts < max_attempts {
                nodes.shuffle(&mut rng);
                let sample: Vec<_> = nodes.iter().take(3).copied().collect();
                let [a, b, c] = [sample[0], sample[1], sample[2]];
                
                if self.edges[a].contains(&b) && 
                   self.edges[b].contains(&c) && 
                   self.edges[c].contains(&a) {
                    loops.push(self.create_loop_data(vec![a, b, c], "3-way"));
                }
                
                attempts += 1;
            }
        } else {
            // For smaller graphs, check all possibilities
            for &i in &nodes {
                if loops.len() >= max_loops {
                    break;
                }
                
                for &j in &self.edges[i] {
                    if j <= i { continue; }
                    
                    for &k in &self.edges[j] {
                        if k <= j { continue; }
                        
                        if self.edges[k].contains(&i) {
                            loops.push(self.create_loop_data(vec![i, j, k], "3-way"));
                            if loops.len() >= max_loops {
                                break;
                            }
                        }
                    }
                }
            }
        }
    }

    fn create_loop_data(&self, indexes: Vec<usize>, loop_type: &str) -> TradeLoop {
        let n = indexes.len();
        let users: Vec<_> = indexes.iter().map(|&i| self.trades[i].user_id.clone()).collect();
        let watches: Vec<_> = indexes.iter().map(|&i| self.trades[i].have_watch.clone()).collect();
        let values: Vec<_> = indexes.iter().map(|&i| self.trades[i].have_value).collect();
        
        let cash_flows: Vec<_> = (0..n)
            .map(|i| values[i] - values[(i + 1) % n])
            .collect();
        
        let total_watch_value: f64 = values.iter().sum();
        let total_cash_flow: f64 = cash_flows.iter().map(|x| x.abs()).sum();
        let value_efficiency = total_watch_value / (total_watch_value + total_cash_flow);

        TradeLoop {
            loop_type: loop_type.to_string(),
            indexes,
            users,
            watches,
            values,
            cash_flows,
            total_watch_value,
            total_cash_flow,
            value_efficiency
        }
    }
} 