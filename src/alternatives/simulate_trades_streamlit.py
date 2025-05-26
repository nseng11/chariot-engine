"""
Streamlit Interface for Alternative Trade Simulation
================================================

This module provides a Streamlit interface for running the alternative trade simulation,
mirroring the functionality of the original simulation but with the new end-state based approach.
"""

import streamlit as st
import pandas as pd
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Use relative imports from current directory
from simulate_trades_alt import simulate_trade_loops_alt
from end_state_tracking import EndStateTracker
from user_preferences import UserPreferenceManager
from trade_prioritization import TradePrioritizer
from user_decision_model import UserDecisionModel
from watch_attributes import WatchAttributeManager

def generate_user_data(period: int, initial_users: int, growth_rate: float) -> pd.DataFrame:
    """Generate user data for a given period based on growth parameters."""
    # Calculate number of users for this period
    num_users = int(initial_users * (1 + growth_rate) ** (period - 1))
    
    # Generate random user IDs
    user_ids = [f"user_{i:04d}" for i in range(num_users)]
    
    # Generate random watch IDs (assuming we have 100 watch models)
    watch_ids = [f"watch_{np.random.randint(1, 101):03d}" for _ in range(num_users)]
    
    # Generate random watch values between $1,000 and $50,000
    watch_values = np.random.uniform(1000, 50000, num_users).round(2)
    
    # Generate random max cash top up between 0 and 40% of watch value (increased from 20%)
    max_cash_top_ups = (watch_values * np.random.uniform(0, 0.4, num_users)).round(2)
    
    # Generate min acceptable value (70-100% of current watch value) (lowered from 80%)
    min_acceptable_values = (watch_values * np.random.uniform(0.7, 1.0, num_users)).round(2)
    
    # Create DataFrame
    df = pd.DataFrame({
        'user_id': user_ids,
        'watch_id': watch_ids,
        'watch_value': watch_values,
        'have_watch': watch_ids,  # Each user has their own watch initially
        'have_value': watch_values,  # Value of current watch
        'max_cash_top_up': max_cash_top_ups,  # Maximum cash user is willing to add
        'min_acceptable_value': min_acceptable_values,  # Minimum value user will accept
        'executed_trade': 0,  # Whether user has executed a trade
        'trade_id': None,  # ID of executed trade if any
        'loop_id': None,  # ID of loop if any
        'unique_matches_count': 0  # Number of unique matches for this user
    })
    
    return df

def generate_loop_data(user_data: pd.DataFrame) -> pd.DataFrame:
    """Generate trade loop data based on user data."""
    loops = []
    loop_id = 1
    
    # First generate 2-way trades
    for i in range(len(user_data)):
        for j in range(i + 1, len(user_data)):
            user1 = user_data.iloc[i]
            user2 = user_data.iloc[j]
            
            # Calculate cash flows
            cash_flow1 = user2['watch_value'] - user1['watch_value']
            cash_flow2 = user1['watch_value'] - user2['watch_value']
            
            # Calculate value efficiency
            total_watch_value = user1['watch_value'] + user2['watch_value']
            total_cash_flow = abs(cash_flow1) + abs(cash_flow2)
            value_efficiency = total_watch_value / (total_watch_value + total_cash_flow)
            
            # Add all potential trades without value efficiency threshold
            loops.append({
                'loop_id': loop_id,
                'user_id': user1['user_id'],
                'watch_id': user2['watch_id'],
                'watch_value': user2['watch_value'],
                'loop_type': '2-way',
                'user_1': user1['user_id'],
                'user_2': user2['user_id'],
                'watch_1': user1['have_watch'],
                'watch_2': user2['have_watch'],
                'value_1': user1['watch_value'],
                'value_2': user2['watch_value'],
                'cash_flow_1': cash_flow1,
                'cash_flow_2': cash_flow2,
                'total_watch_value': total_watch_value,
                'total_cash_flow': total_cash_flow,
                'value_efficiency': value_efficiency,
                'received_watch_1': user2['have_watch'],
                'received_watch_2': user1['have_watch']
            })
            loop_id += 1
    
    # Then generate 3-way trades
    for i in range(len(user_data)):
        for j in range(i + 1, len(user_data)):
            for k in range(j + 1, len(user_data)):
                user1 = user_data.iloc[i]
                user2 = user_data.iloc[j]
                user3 = user_data.iloc[k]
                
                # Calculate cash flows
                cash_flow1 = user2['watch_value'] - user1['watch_value']
                cash_flow2 = user3['watch_value'] - user2['watch_value']
                cash_flow3 = user1['watch_value'] - user3['watch_value']
                
                # Calculate value efficiency
                total_watch_value = user1['watch_value'] + user2['watch_value'] + user3['watch_value']
                total_cash_flow = abs(cash_flow1) + abs(cash_flow2) + abs(cash_flow3)
                value_efficiency = total_watch_value / (total_watch_value + total_cash_flow)
                
                # Add all potential trades without value efficiency threshold
                print(f"Generated 3-way trade with users {user1['user_id']}, {user2['user_id']}, {user3['user_id']} and efficiency {value_efficiency:.3f}")
                loops.append({
                    'loop_id': loop_id,
                    'user_id': user1['user_id'],
                    'watch_id': user2['watch_id'],
                    'watch_value': user2['watch_value'],
                    'loop_type': '3-way',
                    'user_1': user1['user_id'],
                    'user_2': user2['user_id'],
                    'user_3': user3['user_id'],
                    'watch_1': user1['have_watch'],
                    'watch_2': user2['have_watch'],
                    'watch_3': user3['have_watch'],
                    'value_1': user1['watch_value'],
                    'value_2': user2['watch_value'],
                    'value_3': user3['watch_value'],
                    'cash_flow_1': cash_flow1,
                    'cash_flow_2': cash_flow2,
                    'cash_flow_3': cash_flow3,
                    'total_watch_value': total_watch_value,
                    'total_cash_flow': total_cash_flow,
                    'value_efficiency': value_efficiency,
                    'received_watch_1': user2['have_watch'],
                    'received_watch_2': user3['have_watch'],
                    'received_watch_3': user1['have_watch']
                })
                loop_id += 1
    
    return pd.DataFrame(loops)

def load_config(config_path: str) -> Dict:
    """Load simulation configuration"""
    with open(config_path, 'r') as f:
        return json.load(f)

def save_results(results: pd.DataFrame, output_dir: str, config: Dict):
    """Save comprehensive simulation results"""
    os.makedirs(output_dir, exist_ok=True)
    
    # Save main results
    results.to_csv(os.path.join(output_dir, 'simulation_results.csv'), index=False)
    
    # Save period summary
    period_summary = pd.DataFrame([{
        'Period': config['parameters']['period'],
        'Initial Users': config['parameters']['initial_users'],
        'Growth Rate': config['parameters']['growth_rate'],
        'Total Trades': len(results),
        '2-Way Trades': len(results[results['loop_type'] == '2-way']),
        '3-Way Trades': len(results[results['loop_type'] == '3-way']),
        'Total Cash Flow': results['total_cash_flow'].sum(),
        'Average Cash Flow': results['total_cash_flow'].mean(),
        'Value Efficiency': results['value_efficiency'].mean(),
        'Users Involved': len(set([user for users in results['users'] for user in users]))
    }])
    period_summary.to_csv(os.path.join(output_dir, 'period_summary.csv'), index=False)
    
    # Save user tracking
    user_tracking = pd.DataFrame([{
        'user_id': user,
        'trades_executed': len(results[results['users'].apply(lambda x: user in x)]),
        'total_cash_flow': results[results['users'].apply(lambda x: user in x)]['total_cash_flow'].sum(),
        'average_value_efficiency': results[results['users'].apply(lambda x: user in x)]['value_efficiency'].mean()
    } for user in set([user for users in results['users'] for user in users])])
    user_tracking.to_csv(os.path.join(output_dir, 'user_tracking.csv'), index=False)
    
    # Save config
    with open(os.path.join(output_dir, 'config.json'), 'w') as f:
        json.dump(config, f, indent=2)

def main():
    st.set_page_config(
        page_title="Chariot Engine - Alternative Trade Simulation",
        page_icon="⌚",
        layout="wide"
    )
    
    st.title("⌚ Chariot Engine - Alternative Trade Simulation")
    st.write("This simulation uses an end-state based approach with competitive bidding.")
    
    # Create two columns for the main layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.header("Simulation Parameters")
        
        # User growth parameters
        st.subheader("User Growth")
        initial_users = st.number_input(
            "Initial Number of Users",
            min_value=1,
            max_value=10000,
            value=10,
            step=1,
            help="Number of users at the start of the simulation"
        )
        
        growth_rate = st.slider(
            "Period-over-Period Growth Rate",
            min_value=0.0,
            max_value=0.5,
            value=0.1,
            step=0.01,
            help="Expected growth rate of users per period (e.g., 0.1 = 10% growth)"
        )
        
        # Period selection
        st.subheader("Simulation Periods")
        end_period = st.number_input(
            "Simulate Until Period",
            min_value=1,
            max_value=12,
            value=12,
            step=1,
            help="Last period to simulate (simulation starts from period 1)"
        )
        
        # Calculate expected user counts
        start_users = initial_users  # Period 1
        end_users = int(initial_users * (1 + growth_rate) ** (end_period - 1))
        st.info(f"User count will grow from {start_users:,} to {end_users:,} users")
        
        # Market conditions
        st.subheader("Market Conditions")
        market_volatility = st.slider(
            "Market Volatility",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="Higher values indicate more volatile market conditions"
        )
        
        competition_level = st.slider(
            "Competition Level",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="Higher values indicate more competitive trading environment"
        )
        
        # User behavior
        st.subheader("User Behavior")
        acceptance_threshold = st.slider(
            "Acceptance Threshold",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="Base probability for users to accept trades"
        )
        
        overbid_factor = st.slider(
            "Overbid Factor",
            min_value=0.0,
            max_value=0.2,
            value=0.1,
            step=0.01,
            help="Maximum percentage users will overbid"
        )
        
        # Simulation controls
        st.subheader("Simulation Controls")
        if st.button("Run Simulation", type="primary"):
            with st.spinner("Running simulation..."):
                try:
                    # Create timestamped run folder
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    run_folder = f"simulations/run_{timestamp}"
                    
                    # Initialize tracking variables
                    all_results = []
                    user_history_tracker = {}
                    user_trade_log = []
                    trade_counter = [0]
                    
                    # Run simulation for each period
                    for period in range(1, end_period + 1):
                        st.write(f"Simulating period {period}...")
                        
                        # Create data directory if it doesn't exist
                        data_dir = Path(f"data/period_{period}")
                        data_dir.mkdir(parents=True, exist_ok=True)
                        
                        # Generate user and loop data
                        user_data = generate_user_data(period, initial_users, growth_rate)
                        loop_data = generate_loop_data(user_data)
                        
                        # Save generated data
                        user_data.to_csv(data_dir / f"period_{period}_users.csv", index=False)
                        loop_data.to_csv(data_dir / f"period_{period}_loops.csv", index=False)
                        
                        # Update config with user parameters
                        config = {
                            "paths": {
                                "user_data": str(data_dir / f"period_{period}_users.csv"),
                                "matching_data": str(data_dir / f"period_{period}_loops.csv"),
                                "output_dir": f"{run_folder}/period_{period}_alt",
                                "catalog_path": "data/watch_catalog.csv"
                            },
                            "simulation_type": "alternative",
                            "version": "1.0.0",
                            "parameters": {
                                "period": period,
                                "initial_users": initial_users,
                                "growth_rate": growth_rate,
                                "market_volatility": market_volatility,
                                "competition_level": competition_level,
                                "acceptance_threshold": acceptance_threshold,
                                "overbid_factor": overbid_factor
                            },
                            "timestamp": timestamp
                        }
                        
                        # Run simulation for this period
                        results = simulate_trade_loops_alt(
                            user_csv_path=config['paths']['user_data'],
                            loop_csv_path=config['paths']['matching_data'],
                            output_dir=config['paths']['output_dir'],
                            catalog_path=config['paths']['catalog_path'],
                            user_trade_log=user_trade_log,
                            user_history_tracker=user_history_tracker,
                            period=period,
                            timestamp=timestamp,
                            trade_counter=trade_counter
                        )
                        
                        if results is not None and isinstance(results, pd.DataFrame) and not results.empty:
                            # Add period information to results
                            results['period'] = period
                            all_results.append(results)
                            
                            # Save period results
                            save_results(results, config['paths']['output_dir'], config)
                    
                    if not all_results:
                        st.error("No trades were executed in any period")
                        return
                        
                    # Combine all results
                    combined_results = pd.concat(all_results, ignore_index=True)
                    
                    # Save aggregate results
                    aggregate_summary = pd.DataFrame([{
                        "total_users_generated": end_users,
                        "users_accepted_trade": len(set([user for users in combined_results['users'] for user in users])),
                        "total_2way_trades": len(combined_results[combined_results['loop_type'] == '2-way']),
                        "total_3way_trades": len(combined_results[combined_results['loop_type'] == '3-way']),
                        "total_trades_executed": len(combined_results),
                        "percent_users_traded": round(100 * len(set([user for users in combined_results['users'] for user in users])) / end_users, 2),
                        "avg_users_per_trade": round(
                            (2 * len(combined_results[combined_results['loop_type'] == '2-way']) + 
                             3 * len(combined_results[combined_results['loop_type'] == '3-way'])) / 
                            len(combined_results), 2
                        ),
                        "num_periods": end_period,
                        "initial_users": initial_users,
                        "growth_rate": growth_rate
                    }])
                    
                    # Save aggregate results
                    aggregate_summary.to_csv(os.path.join(run_folder, "aggregate_summary.csv"), index=False)
                    combined_results.to_csv(os.path.join(run_folder, "all_executed_trades.csv"), index=False)
                    
                    # Save user trade log if it's not empty
                    if user_trade_log:
                        pd.DataFrame(user_trade_log).to_csv(os.path.join(run_folder, "user_trade_log.csv"), index=False)
                    
                    # Store results in session state
                    st.session_state.results = combined_results
                    st.session_state.config = config
                    st.session_state.run_folder = run_folder
                    st.session_state.aggregate_summary = aggregate_summary
                    st.session_state.user_trade_log = user_trade_log
                    
                    st.success(f"Simulation completed successfully! Results saved to {run_folder}")
                    
                except Exception as e:
                    st.error(f"Error running simulation: {str(e)}")
    
    with col2:
        st.header("Simulation Results")
        
        if 'results' in st.session_state:
            # Period-by-Period Summary
            st.subheader("📊 Period-by-Period Summary")
            
            # Create period summary DataFrame
            period_summaries = []
            previous_period_users = set()  # Track users who remain from previous period
            
            for period in range(1, end_period + 1):
                # Calculate new users for this period based on growth rate
                if period == 1:
                    # First period: start with 0 initial users, add initial_users as new users
                    initial_users_count = 0
                    new_users_count = initial_users
                else:
                    # Subsequent periods: previous period's non-trading users become initial users
                    initial_users_count = len(previous_period_users)
                    # Calculate new users based on growth rate
                    new_users_count = int(initial_users * (1 + growth_rate) ** (period - 1))
                
                # Get results for this period
                period_results = st.session_state.results[st.session_state.results['period'] == period]
                
                # Calculate users who traded this period
                if not period_results.empty:
                    # Extract unique users from the 'users' column
                    users_in_trades = len(set([user.strip("'[] ") for users in period_results['users'] for user in users.split(',')]))
                else:
                    users_in_trades = 0
                
                # Calculate users who remain (didn't trade)
                total_users = initial_users_count + new_users_count
                remaining_users = total_users - users_in_trades
                
                # Calculate participation and retention rates
                participation_rate = (users_in_trades / total_users * 100) if total_users > 0 else 0
                retention_rate = (remaining_users / total_users * 100) if total_users > 0 else 0
                
                # Store period results
                period_results = {
                    'period': period,
                    'initial_users': initial_users_count,  # Users from previous period
                    'new_users': new_users_count,  # New users this period
                    'users_in_trades': users_in_trades,  # Users who traded
                    'final_users': remaining_users,  # Users who didn't trade
                    'participation_rate': participation_rate,  # Percentage of users who traded
                    'retention_rate': retention_rate  # Percentage of users who didn't trade
                }
                period_summaries.append(period_results)
                
                # Update previous period users for next iteration
                previous_period_users = set([f"user_{i:04d}" for i in range(remaining_users)])
            
            period_summary_df = pd.DataFrame(period_summaries)
            
            # Format the summary table - only format columns that exist
            if 'total_cash_flow' in period_summary_df.columns:
                period_summary_df['Total Cash Flow'] = period_summary_df['total_cash_flow'].map('${:,.2f}'.format)
            if 'avg_cash_flow' in period_summary_df.columns:
                period_summary_df['Avg Cash Flow'] = period_summary_df['avg_cash_flow'].map('${:,.2f}'.format)
            if 'value_efficiency' in period_summary_df.columns:
                period_summary_df['Avg Value Efficiency'] = period_summary_df['value_efficiency'].map('{:.1%}'.format)
            
            # Format rates as percentages
            period_summary_df['Participation Rate'] = period_summary_df['participation_rate'].map('{:.1f}%'.format)
            period_summary_df['Retention Rate'] = period_summary_df['retention_rate'].map('{:.1f}%'.format)
            
            # Reorder columns for better readability - only include columns that exist
            column_order = [
                'period',
                'initial_users',
                'new_users',
                'users_in_trades',
                'final_users',
                'participation_rate',
                'retention_rate'
            ]
            # Add optional columns if they exist
            optional_columns = [
                'total_cash_flow',
                'avg_cash_flow',
                'value_efficiency'
            ]
            column_order.extend([col for col in optional_columns if col in period_summary_df.columns])
            
            period_summary_df = period_summary_df[column_order]
            
            # Display the summary table with a caption
            st.caption("User population changes and trading activity for each period")
            st.dataframe(period_summary_df, use_container_width=True)
            
            # Add period-by-period visualizations
            col_period1, col_period2 = st.columns(2)
            
            with col_period1:
                # User tracking over time
                fig_users = go.Figure()
                fig_users.add_trace(go.Scatter(
                    x=period_summary_df['period'],
                    y=period_summary_df['initial_users'],
                    name='Initial Users',
                    line=dict(color='blue')
                ))
                fig_users.add_trace(go.Scatter(
                    x=period_summary_df['period'],
                    y=period_summary_df['users_in_trades'],
                    name='Users in Trades',
                    line=dict(color='green')
                ))
                fig_users.add_trace(go.Scatter(
                    x=period_summary_df['period'],
                    y=period_summary_df['final_users'],
                    name='Final Users',
                    line=dict(color='red')
                ))
                fig_users.update_layout(
                    title='User Population Over Time',
                    xaxis_title='Period',
                    yaxis_title='Number of Users',
                    showlegend=True
                )
                st.plotly_chart(fig_users, use_container_width=True)
            
            with col_period2:
                # User retention visualization
                fig_retention = go.Figure()
                fig_retention.add_trace(go.Bar(
                    x=period_summary_df['period'],
                    y=period_summary_df['users_in_trades'],
                    name='Users in Trades',
                    marker_color='green'
                ))
                fig_retention.add_trace(go.Bar(
                    x=period_summary_df['period'],
                    y=period_summary_df['users_in_trades'],
                    name='Users in Trades',
                    marker_color='green'
                ))
                fig_retention.update_layout(
                    title='User Retention and Trading Activity',
                    xaxis_title='Period',
                    yaxis_title='Number of Users',
                    barmode='stack',
                    showlegend=True
                )
                st.plotly_chart(fig_retention, use_container_width=True)
            
            # Add participation and retention rates visualization
            col_period3, col_period4 = st.columns(2)
            
            with col_period3:
                # Participation rate over time
                fig_participation = go.Figure()
                fig_participation.add_trace(go.Scatter(
                    x=period_summary_df['period'],
                    y=period_summary_df['participation_rate'],  # Use numeric value directly
                    name='Participation Rate',
                    line=dict(color='purple')
                ))
                fig_participation.update_layout(
                    title='User Participation Rate Over Time',
                    xaxis_title='Period',
                    yaxis_title='Participation Rate (%)',
                    yaxis_tickformat='.1%',
                    showlegend=True
                )
                st.plotly_chart(fig_participation, use_container_width=True)
            
            with col_period4:
                # Retention rate over time
                fig_retention_rate = go.Figure()
                fig_retention_rate.add_trace(go.Scatter(
                    x=period_summary_df['period'],
                    y=period_summary_df['retention_rate'],  # Use numeric value directly
                    name='Retention Rate',
                    line=dict(color='orange')
                ))
                fig_retention_rate.update_layout(
                    title='User Retention Rate Over Time',
                    xaxis_title='Period',
                    yaxis_title='Retention Rate (%)',
                    yaxis_tickformat='.1%',
                    showlegend=True
                )
                st.plotly_chart(fig_retention_rate, use_container_width=True)
            
            # Trade Summary
            st.subheader("📈 Overall Trade Summary")
            col3, col4, col5 = st.columns(3)
            
            with col3:
                total_trades = len(st.session_state.results)
                st.metric("Total Executed Trades", f"{total_trades}")
            
            with col4:
                avg_cash_flow = st.session_state.results['total_cash_flow'].mean()
                st.metric("Average Cash Flow", f"${avg_cash_flow:,.2f}")
            
            with col5:
                total_users = len(set([user for users in st.session_state.results['users'] for user in users]))
                st.metric("Total Users Involved", f"{total_users}")
            
            # User Summary
            st.subheader("👥 User Summary")
            col6, col7, col8 = st.columns(3)
            
            with col6:
                avg_trades_per_user = total_trades / total_users if total_users > 0 else 0
                st.metric("Average Trades per User", f"{avg_trades_per_user:.2f}")
            
            with col7:
                avg_value_efficiency = st.session_state.results['value_efficiency'].mean()
                st.metric("Average Value Efficiency", f"{avg_value_efficiency:.2%}")
            
            with col8:
                success_rate = (total_trades / len(st.session_state.results)) * 100
                st.metric("Trade Success Rate", f"{success_rate:.1f}%")
            
            # Visualizations
            st.subheader("📊 Trading Activity Analysis")
            
            # Trade type distribution
            trade_types = st.session_state.results['loop_type'].value_counts()
            fig_trade_types = px.pie(
                values=trade_types.values,
                names=trade_types.index,
                title="Distribution of Trade Types"
            )
            st.plotly_chart(fig_trade_types, use_container_width=True)
            
            # Cash flow distribution
            fig_cash_flow = px.histogram(
                st.session_state.results,
                x='total_cash_flow',
                title="Distribution of Cash Flows",
                labels={'total_cash_flow': 'Cash Flow ($)'}
            )
            st.plotly_chart(fig_cash_flow, use_container_width=True)
            
            # Value efficiency distribution
            fig_efficiency = px.histogram(
                st.session_state.results,
                x='value_efficiency',
                title="Distribution of Value Efficiency",
                labels={'value_efficiency': 'Value Efficiency'}
            )
            st.plotly_chart(fig_efficiency, use_container_width=True)
            
            # Trading activity over time
            if 'period' in st.session_state.results.columns:
                trades_by_period = st.session_state.results.groupby('period').size()
                fig_trades_over_time = px.line(
                    x=trades_by_period.index,
                    y=trades_by_period.values,
                    title="Trading Activity Over Time",
                    labels={'x': 'Period', 'y': 'Number of Trades'}
                )
                st.plotly_chart(fig_trades_over_time, use_container_width=True)
            
            # Detailed results
            st.subheader("📋 Detailed Results")
            st.dataframe(st.session_state.results)
            
            # Download buttons
            st.subheader("Download Results")
            col9, col10, col11, col12 = st.columns(4)
            
            with col9:
                csv = st.session_state.results.to_csv(index=False)
                st.download_button(
                    label="Download All Trades",
                    data=csv,
                    file_name="all_executed_trades.csv",
                    mime="text/csv"
                )
            
            with col10:
                csv = st.session_state.aggregate_summary.to_csv(index=False)
                st.download_button(
                    label="Download Aggregate Summary",
                    data=csv,
                    file_name="aggregate_summary.csv",
                    mime="text/csv"
                )
            
            with col11:
                if hasattr(st.session_state, 'user_trade_log') and st.session_state.user_trade_log:
                    user_trade_log_df = pd.DataFrame(st.session_state.user_trade_log)
                    csv = user_trade_log_df.to_csv(index=False)
                    st.download_button(
                        label="Download User Trade Log",
                        data=csv,
                        file_name="user_trade_log.csv",
                        mime="text/csv"
                    )
            
            with col12:
                st.download_button(
                    label="Download All Results",
                    data=json.dumps({
                        "config": st.session_state.config,
                        "aggregate_summary": st.session_state.aggregate_summary.to_dict('records')[0],
                        "total_trades": len(st.session_state.results),
                        "total_users": total_users
                    }, indent=2),
                    file_name="simulation_summary.json",
                    mime="application/json"
                )
            
            # Show run information
            st.subheader("Run Information")
            st.json(st.session_state.config)
        else:
            st.info("Run the simulation to see results")
    
    # Display simulation information in an expander
    with st.expander("About This Simulation"):
        st.write("""
        This alternative simulation uses:
        - End-state based trading
        - Competitive bidding system
        - Cash flow prioritization
        - User preference management
        """)
        
        st.subheader("Components")
        components = {
            "End State Tracking": "Tracks unique end states for each user",
            "User Preferences": "Manages user preferences and bids",
            "Trade Prioritization": "Prioritizes trades based on cash flow",
            "User Decision Model": "Models realistic user decisions",
            "Watch Attributes": "Manages watch characteristics"
        }
        
        for component, description in components.items():
            st.write(f"**{component}**: {description}")

if __name__ == "__main__":
    main() 