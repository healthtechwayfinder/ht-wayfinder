import streamlit as st
from streamlit_extras.switch_page_button import switch_page

def check_login():
    if "logged_in" not in st.session_state:
        switch_page("streamlit app")
    else:
        if st.session_state["logged_in"] == False or st.session_state["logged_in"] == 'false':
            switch_page("streamlit app")