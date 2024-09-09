import streamlit as st

# Function to clear form inputs
def clear_form():
    st.session_state.input1 = ''

# Function to handle form submission
def submit_form():
    # You can add any form submission logic here
   # st.write("Text 1:", st.session_state.input1)
    st.text_input(label="There is a need for...", st.session_state.input1)

    # Clear the form after submission
    clear_form()

# Initialize the session state for the input if it doesn't exist
if 'input1' not in st.session_state:
    st.session_state.input1 = ''

# Create the form
with st.form("my_form"):
    # Text input tied to session state
    st.text_input("Enter text 1", key='input1')

    # Form submit button with a callback function
    submitted = st.form_submit_button("Submit", on_click=submit_form)

#
