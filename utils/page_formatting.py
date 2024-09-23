import streamlit as st

def add_investigator_formatting():
    st.set_page_config(page_title="Observation Investigator", page_icon="🤖")

    st.markdown("""
        <style>
        div.stButton > button {
            background-color: #a51c30;
            color: white;
            font-size: 16px;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
        }
        div.stButton > button:hover {
            background-color: #2c4a70;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)

    st.markdown("# Observation Investigator")
    st.write("Use this tool to find relationships between cases, summarize elements in observations, and plan for future observations.")