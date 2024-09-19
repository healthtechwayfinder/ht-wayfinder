import time
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Optional
from datetime import date

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load credentials from Streamlit secrets
creds_dict = {
    "type" : st.secrets["gwf_service_account"]["type"],
    "project_id" : st.secrets["gwf_service_account"]["project_id"],
    "private_key_id" : st.secrets["gwf_service_account"]["private_key_id"],
    "private_key" : st.secrets["gwf_service_account"]["private_key"],
    "client_email" : st.secrets["gwf_service_account"]["client_email"],
    "client_id" : st.secrets["gwf_service_account"]["client_id"],
    "auth_uri" : st.secrets["gwf_service_account"]["auth_uri"],
    "token_uri" : st.secrets["gwf_service_account"]["token_uri"],
    "auth_provider_x509_cert_url" : st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url" : st.secrets["gwf_service_account"]["client_x509_cert_url"],
    "universe_domain": st.secrets["gwf_service_account"]["universe_domain"],
}

# Initialize session state variables
for key in ["observation", "result", "observation_summary", "observation_tags", "rerun"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# Function to connect to Google Sheets
def get_google_sheet(sheet_name, worksheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(credentials)
    sheet = client.open(sheet_name).worksheet(worksheet_name)
    return sheet

# Function to get observation IDs from the Google Sheet
def get_observation_ids():
    sheet = get_google_sheet("2024 Healthtech Identify Log", "Observation Log")
    
    # Fetch relevant columns from the sheet
    observation_ids = sheet.col_values(1)[1:]  # Skip header
    observation_titles = sheet.col_values(2)[1:]  # Titles
    
    # Debug: Log the raw data
    st.write("Raw Observation IDs:", observation_ids)
    st.write("Raw Observation Titles:", observation_titles)
    
    observation_ids_with_title = dict(zip(observation_ids, observation_titles))
    
    # Create formatted list with ID - title format
    formatted_observations = [f"{obs_id} - {title}" for obs_id, title in observation_ids_with_title.items()]
    
    st.write("Formatted Observations:", formatted_observations)  # Debugging step
    
    return formatted_observations, observation_ids_with_title

# Correct the list of observation IDs to strings
observations = [
    "OB2409100015", "OB2409180003", "OB2409190002", "OB2409190003", 
    "OB2409190004", "OB2409190005", "OB2409190006", "OB2409190007"
]

# Function to filter and return observation data for the given list of observation IDs
def get_filtered_observation_data(observations, observation_data):
    st.write("Observations List (for filtering):", observations)  # Debugging step
    st.write("Observation Data (from Google Sheet):", observation_data)  # Debugging step
    filtered_data = {obs_id: observation_data[obs_id] for obs_id in observations if obs_id in observation_data}
    
    st.write("Filtered Data:", filtered_data)  # Debugging step
    
    return filtered_data

# Get the observation IDs and titles from Google Sheets
formatted_observations, observation_ids_with_title = get_observation_ids()

# Apply the filter to get the formatted observations
filtered_observations = get_filtered_observation_data(observations, observation_ids_with_title)

# Streamlit UI for Observation ID Selection
st.title("Observation ID Selection")

# Multi-select dropdown with observation IDs
selected_observation_ids = st.multiselect("Select Observation IDs:", list(filtered_observations.keys()))

# Display the selected Observation IDs
if selected_observation_ids:
    st.write("You selected the following Observation IDs:", selected_observation_ids)
