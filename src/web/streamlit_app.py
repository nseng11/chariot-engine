import streamlit as st
import pandas as pd
import json
import os
import glob
from datetime import datetime
import plotly.express as px
import sys
from pathlib import Path
import zipfile
import io

# Add the src directory to the Python path
src_path = str(Path(__file__).parent.parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from run_periodic_simulation import run_multi_period_simulation

def create_streamlit_app():
    st.set_page_config(page_title="Chariot Engine Simulation", layout="wide")
    
    # Title and description
    st.title("🎯 Chariot Engine Trade Simulation")
    st.markdown("""
    This simulation demonstrates the trading dynamics of watch enthusiasts in a peer-to-peer marketplace.
    Adjust the parameters in the sidebar to explore different scenarios.
    """)
    
    # Sidebar configuration
    st.sidebar.header("Simulation Parameters")
    
    initial_users = st.sidebar.slider(
        "Initial Users", 
        min_value=5, 
        max_value=15,
        value=15,
        help="Number of users at the start of period 1"
    )
    
    growth_rate = st.sidebar.slider(
        "Growth Rate", 
        min_value=0,
        max_value=20,
        value=15,
        help="Rate at which new users are added each period (%)"
    ) / 100  # Convert percentage to decimal for the simulation
    
    num_periods = st.sidebar.slider(
        "Number of Periods", 
        min_value=1, 
        max_value=12,
        value=12,
        help="Total number of trading periods to simulate"
    )
    
    # Run simulation button
    if st.sidebar.button("🚀 Run Simulation"):
        with st.spinner("Running simulation..."):
            # Create config for this run
            config = {
                "initial_users": initial_users,
                "growth_rate": growth_rate,
                "num_periods": num_periods,
                "catalog_path": "seed_catalogs_w/watch_catalog.csv"
            }
            
            # Save config temporarily
            os.makedirs("configs", exist_ok=True)
            with open("configs/temp_config.json", "w") as f:
                json.dump(config, f)
            
            # Run simulation
            run_multi_period_simulation("configs/temp_config.json")
            
            # Load results
            latest_run = max(glob.glob("simulations/run_*"), key=os.path.getctime)
            results_df = pd.read_csv(f"{latest_run}/period_summary.csv")
            
            # Calculate total unique users and matched users
            total_unique_users = results_df['New Users'].sum() + results_df['Start Users'].iloc[0]
            total_matched_users = results_df['Users Matched'].sum()
            
            # Display results
            st.success("✅ Simulation completed successfully!")
            
            # First row of metrics
            st.subheader("📈 Trade Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("2-Way Trades", f"{results_df['2-Way Trades'].sum():,}")
            with col2:
                st.metric("3-Way Trades", f"{results_df['3-Way Trades'].sum():,}")
            with col3:
                st.metric("Total Trades", f"{results_df['Total Trades'].sum():,}")

            # Second row of metrics            
            st.subheader("👥 User Summary")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Users Created", f"{total_unique_users:,}")
            with col2:
                st.metric("Total Users Matched", f"{total_matched_users:,}")
            with col3:
                st.metric("Final User Pool", f"{results_df['End Users'].iloc[-1]:,}")
            with col4:
                success_rate = (total_matched_users / total_unique_users * 100)
                st.metric("Match Success Rate", f"{success_rate:.1f}%")

            # Show the charts next
            st.subheader("📊 Trading Activity Over Time")
            fig_trades = px.line(results_df, x="Period", 
                               y=["2-Way Trades", "3-Way Trades", "Total Trades"],
                               title="Trade Volume by Type")
            st.plotly_chart(fig_trades, use_container_width=True)
            fig_users = px.line(results_df, x="Period",
                              y=["Start Users", "New Users", "Total Pool", "End Users"],
                              title="User Flow Analysis")
            st.plotly_chart(fig_users, use_container_width=True)

            # Now show the detailed results table
            st.subheader("📋 Detailed Period Summary")
            display_columns = [
                "Period", "Start Users", "New Users", "Total Pool",
                "2-Way Trades", "3-Way Trades", "Total Trades",
                "Users Matched", "End Users"
            ]
            st.dataframe(
                results_df[display_columns].style.highlight_max(axis=0),
                use_container_width=True
            )

            # Download buttons remain at the end
            st.subheader("Download Results")
            col1, col2 = st.columns(2)
            with col1:
                with open(f"{latest_run}/period_summary.csv", "rb") as f:
                    st.download_button(
                        label="📊 Download Summary CSV",
                        data=f,
                        file_name="period_summary.csv",
                        mime="text/csv"
                    )
            with col2:
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for root, dirs, files in os.walk(latest_run):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, os.path.dirname(latest_run))
                            zip_file.write(file_path, arcname)
                zip_buffer.seek(0)
                zip_data = zip_buffer.getvalue()
                run_timestamp = os.path.basename(latest_run).replace('run_', '')
                st.download_button(
                    label="📁 Download Full Simulation",
                    data=zip_data,
                    file_name=f"simulation_run_{run_timestamp}.zip",
                    mime="application/zip"
                )

if __name__ == "__main__":
    create_streamlit_app()