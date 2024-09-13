import streamlit as st
import pandas as pd

testvar = 42069
st.session_state['need_ID'] = testvar

# Assume you have a session state variable 'need_ID'
if 'need_ID' not in st.session_state:
    st.session_state.need_ID = 'some_value'  # replace 'some_value' with the actual value

# Assume you have a DataFrame 'df' in the session state
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame({
        'Need ID': st.session_state.need_ID,
        'A': range(1, 8),
        # 'B': range(10, 15)
    })

# Add 'need_ID' to the DataFrame
st.session_state.df['need_ID'] = st.session_state.need_ID

# Display the updated DataFrame
st.write(st.session_state.df)
