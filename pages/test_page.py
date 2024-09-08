# import streamlit as st

# # Initialize session state for input and a flag for clearing the form
# if 'input1' not in st.session_state:
#     st.session_state.input1 = ''
# if 'clear' not in st.session_state:
#     st.session_state.clear = False

# # Function to clear inputs
# def clear_form():
#     st.session_state.input1 = ''
#     st.session_state.clear = True  # Set the clear flag to True

# # Create a form
# with st.form("my_form"):
#     # Reset the input if the clear flag is set
#     if st.session_state.clear:
#         st.session_state.input1 = ''
#         st.session_state.clear = False  # Reset the clear flag after clearing

#     input1 = st.text_input("Enter text 1", value=st.session_state.input1, key='input1')

#     # Form submit button
#     submitted = st.form_submit_button("Submit")

#     if submitted:
#         st.write("Text 1:", input1)
#         clear_form()  # Clear the inputs after submission

# # # You can also add a separate button to clear the form without submitting
# # if st.button("Clear Form"):
# #     clear_form()



import streamlit as st

# Initialize session state for the input if not already initialized
if 'input1' not in st.session_state:
    st.session_state.input1 = ''

# Function to clear form inputs
def clear_form():
    st.session_state.input1 = ''
    st.experimental_rerun()  # Rerun the app to reflect the cleared input

# Create a form
with st.form("my_form"):
    input1 = st.text_input("Enter text 1", value=st.session_state.input1, key='input1')

    # Form submit button
    submitted = st.form_submit_button("Submit")

    if submitted:
        st.write("Text 1:", input1)
        clear_form()  # Clear the inputs and rerun the app to
