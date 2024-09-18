import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime, timedelta

# Set page configuration
st.set_page_config(page_title="Weekly Case and Observation Review", page_icon="📒", layout="wide")

st.markdown("# Weekly Observation Review")

# Google Sheets credentials
creds_dict = {
    "type": st.secrets["gwf_service_account"]["type"],
    "project_id": st.secrets["gwf_service_account"]["project_id"],
    "private_key_id": st.secrets["gwf_service_account"]["private_key_id"],
    "private_key": st.secrets["gwf_service_account"]["private_key"].replace('\\n', '\n'),  # Fix formatting
    "client_email": st.secrets["gwf_service_account"]["client_email"],
    "client_id": st.secrets["gwf_service_account"]["client_id"],
    "auth_uri": st.secrets["gwf_service_account"]["auth_uri"],
    "token_uri": st.secrets["gwf_service_account"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["gwf_service_account"]["client_x509_cert_url"],
}

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

# Function to convert Google Sheets data to a Pandas DataFrame
def get_google_sheet_as_dataframe(sheet):
    # Get all data from the worksheet
    data = sheet.get_all_values()
    # Convert to a Pandas DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])  # Use the first row as headers
    return df

# Google Sheets settings
sheet_name = '2024 Healthtech Identify Log'

# Load the "Case Log" and "Observation Log" data
case_log_sheet = get_google_sheet(sheet_name, 'Case Log')
observation_log_sheet = get_google_sheet(sheet_name, 'Observation Log')

case_df = get_google_sheet_as_dataframe(case_log_sheet)
st.write("Columns in Case Log:", case_df.columns)

observation_df = get_google_sheet_as_dataframe(observation_log_sheet)

# Convert date column in case_df to datetime
case_df['date'] = pd.to_datetime(case_df['date'])

# Filter cases from the past week
one_week_ago = datetime.now() - timedelta(days=7)
recent_cases = case_df[case_df['date'] >= one_week_ago]

st.markdown("### Cases in the last week")

# Display each recent case in a text box
for index, case in recent_cases.iterrows():
    st.markdown(f"#### Case ID: {case['case_ID']}")
    st.text_area("Case Details", value=f"Observation ID: {case['observation_ID']}\nDetails: {case['case_details']}", height=150, key=f"case_{index}")

# Map observation_IDs from recent cases to the Observation Log
observation_ids = recent_cases['observation_ID'].unique()
observations_for_cases = observation_df[observation_df['observation_ID'].isin(observation_ids)]

st.markdown("### Corresponding Observations")

# Initialize session state for checkboxes if not already initialized
if "reviewed_observations" not in st.session_state:
    st.session_state["reviewed_observations"] = {}

# Display observations with checkboxes for review status
for index, observation in observations_for_cases.iterrows():
    observation_id = observation['observation_ID']
    col1, col2 = st.columns([8, 2])
    
    with col1:
        st.write(f"**Observation ID: {observation_id}**")
        st.write(f"Details: {observation['observation_details']}")
    
    with col2:
        # Checkbox for marking as reviewed
        checked = st.checkbox("Reviewed", value=st.session_state["reviewed_observations"].get(observation_id, False), key=f"obs_{index}")
        st.session_state["reviewed_observations"][observation_id] = checked

st.markdown("---")

# Button to print the reviewed status (or handle any action after review)
if st.button("Submit Review"):
    reviewed_count = sum(st.session_state["reviewed_observations"].values())
    st.success(f"{reviewed_count} observations marked as reviewed.")
