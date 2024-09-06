
import streamlit as st

with st.form(key="my_form"):
    text_input = st.text_input(label="Need Statement:")
    submit_button = st.form_submit_button(label="Submit")

    if submit_button:
        if text_input:
            need_statement = text_input
            st.write("Need statement recorded!")
            # st.write(f'You entered: {need_statement}')


        else:
            st.warning("Please enter a need statement!")

