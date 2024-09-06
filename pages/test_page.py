import streamlit as st
import pandas as pd

with st.form(key="my_form"):
    text_input = st.text_input(label="Enter some text")
    submit_button = st.form_submit_button(label="Submit")

    if submit_button:
        if not text_input:
            st.warning("Please ensure that the text box has been filled out")
            st.stop()
        else:
            # add new row with filled data:
            new_data = pd.DataFrame(
                [
                    {"Text Input": text_input}
                ]
            )

            # Assume existing_data is your existing DataFrame
            updated_df = pd.concat([existing_data, new_data], ignore_index=True)

            # Update google sheet
            # Assume conn is your connection to the Google Sheet
            conn.update(worksheet="Your Worksheet Name", data=updated_df)
