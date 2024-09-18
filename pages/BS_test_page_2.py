import time
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from datetime import date
import logging
logging.basicConfig(level=logging.INFO)

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Set page configuration
st.set_page_config(page_title="Create a New Need Statement", page_icon=":pencil2:")
st.markdown("# Create a New Need Statement")
st.write("Use this tool to record needs as you draft them. Select the date that the need was generated, and a unique identifier will auto-populate. In the next box, select all related observations.")

# Access the credentials from Streamlit secrets
creds_dict = {
    "type": st.secrets["gwf_service_account"]["type"],
    "project_id": st.secrets["gwf_service_account"]["project_id"],
    "private_key_id": st.secrets["gwf_service_account"]["private_key_id"],
    "private_key": st.secrets["gwf_service_account"]["private_key"],
    "client_email": st.secrets["gwf_service_account"]["client_email"],
    "client_id": st.secrets["gwf_service_account"]["client_id"],
    "auth_uri": st.secrets["gwf_service_account"]["auth_uri"],
    "token_uri": st.secrets["gwf_service_account"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["gwf_service_account"]["client_x509_cert_url"],
}

# Initialize session state for the selected observation
if 'obs_id_with_title' not in st.session_state:
    st.session_state.obs_id_with_title = ''

# Function to get Google Sheets connection
def get_google_sheet(sheet_name, worksheet_name):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).worksheet(worksheet_name)
    return sheet

# Function to get existing observation IDs and titles from the Observation Log
def getExistingObsIDS():
    obs_log = get_google_sheet("2024 Healthtech Identify Log", "Observation Log")
    obs_ids = obs_log.col_values(1)[1:]  # Observation IDs
    obs_titles = obs_log.col_values(2)[1:]  # Observation Descriptions

    existing_obs_ids_with_title = dict(zip(obs_ids, obs_titles))
    return existing_obs_ids_with_title

# Function to display the selected observation's description
def display_selected_observation(selected_obs_id):
    obs_log = get_google_sheet("2024 Healthtech Identify Log", "Observation Log")
    df = pd.DataFrame(obs_log.get_all_records())

    # Get the observation description based on the selected Observation ID
    if selected_obs_id:
        selected_observation = df[df['Observation ID'] == selected_obs_id]
        if not selected_observation.empty:
            observation_description = selected_observation.iloc[0]['Observation Description']
            st.markdown(f"### Selected Observation Description:\n{observation_description}")
        else:
            st.info("No description available for this observation.")
    else:
        st.info("Please select an observation.")

# Fetch observation IDs and titles
existing_obs_ids_with_title = getExistingObsIDS()

# Dropdown to select Observation ID
selected_obs_id_with_title = st.selectbox("Related Observation ID", existing_obs_ids_with_title)

# Extract Observation ID from the selected option
selected_obs_id = selected_obs_id_with_title.split(" - ")[0] if selected_obs_id_with_title else None

# Display the selected observation's description below the dropdown
display_selected_observation(selected_obs_id)

# Other form elements (for creating the need statement)
col1, col2 = st.columns(2)

# date
with col1:
    st.date_input("Need Date", date.today(), on_change=update_need_ID, key="need_date")

# need ID
with col2:
    if 'need_ID' not in st.session_state:
        update_need_ID()
    # Display the need ID
    st.text_input("Need ID (auto-generated):", value=st.session_state['need_ID'], disabled=True)

# Create the form
with st.form("my_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.text_input("Problem:", key='problem')

    with col2:
        st.text_input("Population:", key='population')

    with col3:
        st.text_input("Outcome:", key='outcome')

    st.text_input("Need Statement:", key='need_statement')
    st.text_input("Notes:", key='notes')

    # Form submit button with a callback function
    submitted = st.form_submit_button("Submit", on_click=submit_form)

