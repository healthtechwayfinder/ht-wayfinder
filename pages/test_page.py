import streamlit as st

# Initialize the session state for the text inputs
if 'input1' not in st.session_state:
    st.session_state.input1 = ''
if 'input2' not in st.session_state:
    st.session_state.input2 = ''

# Function to clear inputs
def clear_form():
    st.session_state.input1 = ''
    st.session_state.input2 = ''

# Create a form
with st.form("my_form"):
    input1 = st.text_input("Enter text 1", value=st.session_state.input1, key='input1')
    input2 = st.text_input("Enter text 2", value=st.session_state.input2, key='input2')
    
    # Form submit button
    submitted = st.form_submit_button("Submit")
    
    if submitted:
        st.write("Text 1:", input1)
        st.write("Text 2:", input2)
        
        # Clear the inputs after submission
        clear_form()
