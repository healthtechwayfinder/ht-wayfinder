import streamlit as st

def clear_text_input():
    st.session_state.text_input = ''

if 'text_input' not in st.session_state:
    st.session_state.text_input = ''

text_input = st.text_input("Your message here", value=st.session_state.text_input, key="text_input")

if st.button("Submit"):
    # Do something with the text input
    clear_text_input()  # Clear the text input after form submission


