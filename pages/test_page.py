import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Establish a connection to the Google sheets spreadsheet.
conn = st.connection("gsheets", type=GSheetsConnection)

# Fetch Existing fields
existing_data = conn.read(worksheet="Waste", usecols=list(range(13)), ttl=5)
existing_data = existing_data.dropna(how="all")

# Data Entry Form:
with st.form(key="waste_form"):
    facility_manager_name = st.text_input(label="What is your Name and Surname? *")
    mixed_waste = st.text_input(label="How much mixed waste[kg] have you disposed of?")
    organic_or_wet_waste = st.text_input(label="How much organic/Wet waste[kg] have you disposed of?")

    # Mark mandatory fields
    st.markdown("**required*")
    submit_button = st.form_submit_button(label="Submit waste disposal details")

    if submit_button:
        # check if all mandatory fields have been filled
        if not facility_manager_name or not mixed_waste or not organic_or_wet_waste:
            st.warning("Please ensure that all the mandatory fields have been filled out")
            st.stop()
        else:
            # add new row with filled data:
            waste_data = pd.DataFrame(
                [
                    {   "Manager Name": facility_manager_name,
                        "Mixed waste": mixed_waste,
                        "Organic/Wet waste": organic_or_wet_waste,
                    }
                ]
            )

            updated_df = pd.concat([existing_data, waste_data], ignore_index=True)

            # Update google sheet
            conn.update(worksheet="Waste", data=updated_df)





# import streamlit as st

# with st.form(key="my_form"):
#     text_input = st.text_input(label="Need Statement:")
#     submit_button = st.form_submit_button(label="Submit")

#     if submit_button:
#         if text_input:
#             need_statement = text_input
#             st.write("Need statement recorded!")
#             # st.write(f'You entered: {need_statement}')


#         else:
#             st.warning("Please enter a need statement!")

