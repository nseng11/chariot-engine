use chariot_engine_core::graph_matching::{Trade, TradeGraph};

fn main() {
    // Create a new trade graph
    let mut graph = TradeGraph::new();
    
    // Add some sample trades
    let trades = vec![
        Trade {
            user_id: "user1".to_string(),
            have_watch: "watch1".to_string(),
            have_value: 1000.0,
            min_acceptable_value: 900.0,
            max_cash_top_up: 200.0,
        },
        Trade {
            user_id: "user2".to_string(),
            have_watch: "watch2".to_string(),
            have_value: 1200.0,
            min_acceptable_value: 1000.0,
            max_cash_top_up: 300.0,
        },
        // Add more sample trades...
    ];
    
    // Add trades to graph
    for trade in trades {
        graph.add_trade(trade);
    }
    
    // Build edges and find loops
    graph.build_edges();
    let loops = graph.find_trade_loops();
    
    // Print results
    println!("Found {} potential trade loops:", loops.len());
    for trade_loop in loops {
        println!("Loop type: {}", trade_loop.loop_type);
        println!("Users: {:?}", trade_loop.users);
        println!("Efficiency: {}", trade_loop.value_efficiency);
        println!("---");
    }
} 