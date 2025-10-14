import streamlit as st
import sys
import os
import pandas as pd

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from RAG.retrieval_agent_hybrid import HybridRetrievalAgent

# --- Streamlit App ---

st.set_page_config(layout="wide")

st.title("🧠 Memory Retrieval Agent Demo")
st.markdown("This demo showcases the `HybridRetrievalAgent`'s ability to retrieve context from different memory stores using the `retrieve_context` method.")

# --- Agent Initialization ---
st.sidebar.header("Agent Configuration")
elderly_id = st.sidebar.text_input("Enter Elderly ID", "87654321-4321-4321-4321-019876543210")

if not elderly_id:
    st.warning("Please enter an Elderly ID to proceed.")
    st.stop()

# Use a session state to initialize the agent only once
if 'agent' not in st.session_state or st.session_state.agent.elderly_id != elderly_id:
    try:
        with st.spinner(f"Initializing Retrieval Agent for Elderly ID: {elderly_id}..."):
            st.session_state.agent = HybridRetrievalAgent(elderly_id=elderly_id)
        st.sidebar.success(f"Agent initialized for Elderly ID: {elderly_id}")
    except Exception as e:
        st.error(f"Failed to initialize agent: {e}")
        st.stop()

agent = st.session_state.agent

# --- Retrieval Interface ---
st.header("🔍 Retrieve Context")
query = st.text_area("Enter your query:", "What did I talk about with my daughter yesterday?")

if st.button("Retrieve Context"):
    if not query:
        st.warning("Please enter a query.")
    else:
        with st.spinner("Retrieving context..."):
            retrieval_results = agent.retrieve_context(query)

        if retrieval_results and retrieval_results.get("success"):
            st.success("Context retrieved successfully!")

            results = retrieval_results.get("results", {})
            ltm_results = results.get("ltm", [])
            stm_results = results.get("stm", [])
            health_results = results.get("health", [])

            col1, col2, col3 = st.columns(3)

            with col1:
                st.subheader("Long-Term Memory (LTM)")
                if ltm_results:
                    df_ltm = pd.DataFrame(ltm_results)
                    st.dataframe(df_ltm)
                else:
                    st.info("No results found in LTM.")

            with col2:
                st.subheader("Short-Term Memory (STM)")
                if stm_results:
                    df_stm = pd.DataFrame(stm_results)
                    st.dataframe(df_stm)
                else:
                    st.info("No results found in STM.")

            with col3:
                st.subheader("Healthcare Memory (HCM)")
                if health_results:
                    df_hcm = pd.DataFrame(health_results)
                    st.dataframe(df_hcm)
                else:
                    st.info("No results found in HCM.")

        else:
            st.error(f"Failed to retrieve context: {retrieval_results.get('error', 'Unknown error')}")

