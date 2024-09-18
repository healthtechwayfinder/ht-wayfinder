import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

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

# Function to get data as a Pandas DataFrame from Google Sheets
def get_google_sheet_as_dataframe(sheet):
    data = sheet.get_all_values()  # Get all data from the worksheet
    df = pd.DataFrame(data[1:], columns=data[0])  # Use the first row as headers
    return df

# Function to display related observations in a table
def display_related_observations(observation_ids):
    observation_log_sheet = get_google_sheet("2024 Healthtech Identify Log", "Observation Log")
    observation_df = get_google_sheet_as_dataframe(observation_log_sheet)
    
    # Filter observations based on selected Observation IDs
    filtered_observations = observation_df[observation_df['Observation ID'].isin(observation_ids)]
    
    if not filtered_observations.empty:
        # Display the table with Observation ID and Description
        st.markdown("### Related Observations")
        st.table(filtered_observations[['Observation ID', 'Observation Description']])
    else:
        st.info("No related observations found for the selected case.")

# Function to get existing case IDs from the Case Log
def getExistingCaseIDS():
    case_log = get_google_sheet("2024 Healthtech Identify Log", "Case Log")
    case_ids = case_log.col_values(1)[1:]  # Case IDs
    case_titles = case_log.col_values(2)[1:]  # Case Titles
    return dict(zip(case_ids, case_titles))

# Display the Streamlit layout
st.set_page_config(page_title="Case and Observation Selection", page_icon="🔍", layout="wide")

st.markdown("# Select a Case")

# Load Case IDs and Titles
existing_case_ids_with_title = getExistingCaseIDS()

# Select case from dropdown
case_id_with_title = st.selectbox("Select Related Case ID", list(existing_case_ids_with_title.items()))

# Get the selected case ID and retrieve the corresponding Observation IDs
if case_id_with_title:
    case_log_sheet = get_google_sheet("2024 Healthtech Identify Log", "Case Log")
    case_df = get_google_sheet_as_dataframe(case_log_sheet)
    
    selected_case_id = case_id_with_title[0]  # Get only the case ID
    
    # Find the row where the selected Case ID exists
    case_row = case_df[case_df['Case ID'] == selected_case_id]
    
    if not case_row.empty:
        observation_ids = case_row['Observations'].values[0].split(",")  # Get the Observation IDs and split them if they are comma-separated
        observation_ids = [obs_id.strip() for obs_id in observation_ids if obs_id.strip()]  # Clean up whitespace
        
        # Display related observations in a table
        display_related_observations(observation_ids)
    else:
        st.info("No matching case found.")
