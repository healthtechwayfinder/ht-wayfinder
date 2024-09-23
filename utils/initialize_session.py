import streamlit as st
from utils.google_sheet_utils import create_new_chat_sheet

def initialize_investigator_session():
    # # Create a new sheet for the chat thread if not already created
    if "chat_sheet" not in st.session_state:
        st.session_state.chat_sheet = create_new_chat_sheet()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])