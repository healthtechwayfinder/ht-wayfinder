import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime, timedelta
from streamlit_extras.switch_page_button import switch_page


################## CHECK LOG IN ##################
if "logged_in" not in st.session_state:
    switch_page("streamlit app")
else:
    if st.session_state["logged_in"] == False or st.session_state["logged_in"] == 'false':
        switch_page("streamlit app")

##########################################################################################

# Set page configuration with wide mode
st.set_page_config(page_title="Weekly Observation Review", page_icon="💫", layout="wide")

st.markdown("# Weekly Observation Review")
st.write("Below are your team's cases and observations from the last 7 days. Use this space as an opportunity to debrief, ask questions, and share insights.")

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
    data = sheet.get_all_values()  # Get all data from the worksheet
    df = pd.DataFrame(data[1:], columns=data[0])  # Use the first row as headers
    return df

# Function to update "Reviewed" status in Google Sheets
def update_reviewed_status_in_sheet(sheet, relevant_observations):
    # Get the entire "Observation Log" sheet data
    all_data = sheet.get_all_values()
    
    # Find the index of the "Reviewed" column
    headers = all_data[0]
    reviewed_col_index = headers.index('Reviewed') + 1  # Convert to 1-based index for gspread
    
    # Iterate over the relevant observations and update the "Reviewed" column
    for _, row in relevant_observations.iterrows():
        observation_id = row['Observation ID']
        reviewed_status = row['Reviewed']
        
        # Find the row in the sheet that corresponds to the observation ID
        for i, sheet_row in enumerate(all_data[1:], start=2):  # Start at 2 because row 1 is headers
            if sheet_row[headers.index('Observation ID')] == observation_id:
                # Update the "Reviewed" status in Google Sheets
                sheet.update_cell(i, reviewed_col_index, 'TRUE' if reviewed_status else 'FALSE')
                break

# Google Sheets settings
sheet_name = '2024 Healthtech Identify Log'

# Load the "Case Log" and "Observation Log" data
case_log_sheet = get_google_sheet(sheet_name, 'Case Log')
observation_log_sheet = get_google_sheet(sheet_name, 'Observation Log')

case_df = get_google_sheet_as_dataframe(case_log_sheet)
observation_df = get_google_sheet_as_dataframe(observation_log_sheet)

# Convert date column in case_df to datetime (replace 'Date' with the correct column name)
case_df['Date'] = pd.to_datetime(case_df['Date'], errors='coerce')

# Filter cases from the past week
one_week_ago = datetime.now() - timedelta(days=7)
recent_cases = case_df[case_df['Date'] >= one_week_ago]

# Initialize session state for checkboxes if not already initialized
if "reviewed_observations" not in st.session_state:
    st.session_state["reviewed_observations"] = {}

# Store relevant observations to update after user interaction
observations_to_update = pd.DataFrame()

# Loop through each recent case and display it
for index, case in recent_cases.iterrows():
    st.markdown(f"#### Case ID: {case['Case ID']}")
    with st.container(border=True):
        # st.text_area("Case Details", value=f"Details: {case['Case Description']}", height=150, key=f"case_{index}")
        st.write(f"**Case Details:** {case['Case Description']}")


    # Split the Observations column (assuming comma-separated IDs)
    observation_ids = case['Observations'].split(",")  # Split by commas and remove any extra spaces
    observation_ids = [obs_id.strip() for obs_id in observation_ids if obs_id.strip()]  # Clean and filter empty values
    
    # Filter corresponding observations for the current case
    relevant_observations = observation_df[observation_df['Observation ID'].isin(observation_ids)]
    
    if not relevant_observations.empty:
        st.markdown("#### Related Observations")
        
        # Add a 'Reviewed' column with checkboxes for review
        for obs_idx, row in relevant_observations.iterrows():
            observation_id = row['Observation ID']
            reviewed_value = row['Reviewed'].lower() == 'true'  # Set checkbox based on Google Sheet data
            reviewed_checkbox = st.checkbox(f"Reviewed {observation_id}", value=reviewed_value)

            # Store the checkbox state in session_state
            st.session_state[f"reviewed_{observation_id}"] = reviewed_checkbox

            # Update the DataFrame with the reviewed status
            relevant_observations.at[obs_idx, 'Reviewed'] = reviewed_checkbox

        # Display the observations in a DataFrame
        st.dataframe(relevant_observations[['Observation ID', 'Observer', 'Observation Description', 'Insider Language', 'Reviewed']])

        # Collect the relevant observations to update later
        observations_to_update = pd.concat([observations_to_update, relevant_observations])
    else:
        st.markdown("No related observations found.")

st.markdown("---")

# Button to print the reviewed status (or handle any action after review)
if st.button("Submit Review"):
    update_reviewed_status_in_sheet(observation_log_sheet, observations_to_update)
    reviewed_count = sum([st.session_state.get(f"reviewed_{obs_id}", False) for obs_id in observations_to_update['Observation ID']])
    st.success(f"{reviewed_count} observations marked as reviewed.")






# import streamlit as st
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
# import pandas as pd
# from datetime import datetime, timedelta

# # Set page configuration with wide mode
# st.set_page_config(page_title="Weekly Observation Review", page_icon="💫", layout="wide")

# st.markdown("# Weekly Observation Review")
# st.write("Below are your team's cases and observations from the last 7 days. Use this space as an opportunity to debrief, ask questions, and share insights.")

# # Google Sheets credentials
# creds_dict = {
#     "type": st.secrets["gwf_service_account"]["type"],
#     "project_id": st.secrets["gwf_service_account"]["project_id"],
#     "private_key_id": st.secrets["gwf_service_account"]["private_key_id"],
#     "private_key": st.secrets["gwf_service_account"]["private_key"].replace('\\n', '\n'),  # Fix formatting
#     "client_email": st.secrets["gwf_service_account"]["client_email"],
#     "client_id": st.secrets["gwf_service_account"]["client_id"],
#     "auth_uri": st.secrets["gwf_service_account"]["auth_uri"],
#     "token_uri": st.secrets["gwf_service_account"]["token_uri"],
#     "auth_provider_x509_cert_url": st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
#     "client_x509_cert_url": st.secrets["gwf_service_account"]["client_x509_cert_url"],
# }

# # Function to get Google Sheets connection
# def get_google_sheet(sheet_name, worksheet_name):
#     scope = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.metadata.readonly",
#     ]
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#     client = gspread.authorize(creds)
#     sheet = client.open(sheet_name).worksheet(worksheet_name)
#     return sheet

# # Function to convert Google Sheets data to a Pandas DataFrame
# def get_google_sheet_as_dataframe(sheet):
#     data = sheet.get_all_values()  # Get all data from the worksheet
#     df = pd.DataFrame(data[1:], columns=data[0])  # Use the first row as headers
#     return df

# # Function to update "Reviewed" status in Google Sheets
# def update_reviewed_status_in_sheet(sheet, relevant_observations):
#     # Get the entire "Observation Log" sheet data
#     all_data = sheet.get_all_values()
    
#     # Find the index of the "Reviewed" column
#     headers = all_data[0]
#     reviewed_col_index = headers.index('Reviewed') + 1  # Convert to 1-based index for gspread
    
#     # Iterate over the relevant observations and update the "Reviewed" column
#     for _, row in relevant_observations.iterrows():
#         observation_id = row['Observation ID']
#         reviewed_status = row['Reviewed']
        
#         # Find the row in the sheet that corresponds to the observation ID
#         for i, sheet_row in enumerate(all_data[1:], start=2):  # Start at 2 because row 1 is headers
#             if sheet_row[headers.index('Observation ID')] == observation_id:
#                 # Update the "Reviewed" status in Google Sheets
#                 sheet.update_cell(i, reviewed_col_index, 'TRUE' if reviewed_status else 'FALSE')
#                 break

# # Google Sheets settings
# sheet_name = '2024 Healthtech Identify Log'

# # Load the "Case Log" and "Observation Log" data
# case_log_sheet = get_google_sheet(sheet_name, 'Case Log')
# observation_log_sheet = get_google_sheet(sheet_name, 'Observation Log')

# case_df = get_google_sheet_as_dataframe(case_log_sheet)
# observation_df = get_google_sheet_as_dataframe(observation_log_sheet)

# # Convert date column in case_df to datetime (replace 'Date' with the correct column name)
# case_df['Date'] = pd.to_datetime(case_df['Date'], errors='coerce')

# # Filter cases from the past week
# one_week_ago = datetime.now() - timedelta(days=7)
# recent_cases = case_df[case_df['Date'] >= one_week_ago]

# # st.markdown("### Cases in the last week")

# # Initialize session state for checkboxes if not already initialized
# if "reviewed_observations" not in st.session_state:
#     st.session_state["reviewed_observations"] = {}

# # Store relevant observations to update after user interaction
# observations_to_update = pd.DataFrame()

# # Loop through each recent case and display it
# for index, case in recent_cases.iterrows():
#     st.markdown(f"#### Case ID: {case['Case ID']}")
#     st.text_area("Case Details", value=f"Details: {case['Case Description']}", height=150, key=f"case_{index}")

#     # Split the Observations column (assuming comma-separated IDs)
#     observation_ids = case['Observations'].split(",")  # Split by commas and remove any extra spaces
#     observation_ids = [obs_id.strip() for obs_id in observation_ids if obs_id.strip()]  # Clean and filter empty values
    
#     # Filter corresponding observations for the current case
#     relevant_observations = observation_df[observation_df['Observation ID'].isin(observation_ids)]
    
#     if not relevant_observations.empty:
#         st.markdown("#### Related Observations")
        
#         # Add a 'Reviewed' column with checkboxes for review
#         relevant_observations['Reviewed'] = relevant_observations.apply(lambda row: st.checkbox(f"Reviewed {row['Observation ID']}", value=st.session_state.get(f"reviewed_{row['Observation ID']}", False)), axis=1)

#         # Display observations as a DataFrame
#         st.dataframe(relevant_observations[['Observation ID', 'Observation Description', 'Reviewed']])

#         # Store the checkbox state in session_state
#         for obs_id in relevant_observations['Observation ID']:
#             st.session_state[f"reviewed_{obs_id}"] = relevant_observations[relevant_observations['Observation ID'] == obs_id]['Reviewed'].values[0]

#         # Collect the relevant observations to update
#         observations_to_update = pd.concat([observations_to_update, relevant_observations])
#     else:
#         st.markdown("No related observations found.")

# st.markdown("---")

# # Button to print the reviewed status (or handle any action after review)
# if st.button("Submit Review"):
#     update_reviewed_status_in_sheet(observation_log_sheet, observations_to_update)
#     reviewed_count = sum([st.session_state.get(f"reviewed_{obs_id}", False) for obs_id in observations_to_update['Observation ID']])
#     st.success(f"{reviewed_count} observations marked as reviewed.")

















# import streamlit as st
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
# import pandas as pd
# from datetime import datetime, timedelta

# # Set page configuration
# st.set_page_config(page_title="Weekly Observation Review", page_icon="💫", layout="wide")

# st.markdown("# Weekly Observation Review")
# st.write("Below are your team's cases and observations from the last 7 days. Use this space as an opportunity to debrief, ask questions, and share insights.")


# # Google Sheets credentials
# creds_dict = {
#     "type": st.secrets["gwf_service_account"]["type"],
#     "project_id": st.secrets["gwf_service_account"]["project_id"],
#     "private_key_id": st.secrets["gwf_service_account"]["private_key_id"],
#     "private_key": st.secrets["gwf_service_account"]["private_key"].replace('\\n', '\n'),  # Fix formatting
#     "client_email": st.secrets["gwf_service_account"]["client_email"],
#     "client_id": st.secrets["gwf_service_account"]["client_id"],
#     "auth_uri": st.secrets["gwf_service_account"]["auth_uri"],
#     "token_uri": st.secrets["gwf_service_account"]["token_uri"],
#     "auth_provider_x509_cert_url": st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
#     "client_x509_cert_url": st.secrets["gwf_service_account"]["client_x509_cert_url"],
# }

# # Function to get Google Sheets connection
# def get_google_sheet(sheet_name, worksheet_name):
#     scope = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.metadata.readonly",
#     ]
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#     client = gspread.authorize(creds)
#     sheet = client.open(sheet_name).worksheet(worksheet_name)
#     return sheet

# # Function to convert Google Sheets data to a Pandas DataFrame
# def get_google_sheet_as_dataframe(sheet):
#     data = sheet.get_all_values()  # Get all data from the worksheet
#     df = pd.DataFrame(data[1:], columns=data[0])  # Use the first row as headers
#     return df

# # Function to update "Reviewed" status in Google Sheets
# def update_reviewed_status_in_sheet(sheet, observations_df):
#     # Get the entire "Observation Log" sheet data
#     all_data = sheet.get_all_values()
    
#     # Find the index of the "Reviewed" column
#     headers = all_data[0]
#     reviewed_col_index = headers.index('Reviewed') + 1  # Convert to 1-based index for gspread
    
#     # Iterate over the relevant observations and update the "Reviewed" column
#     for _, row in observations_df.iterrows():
#         observation_id = row['Observation ID']
#         reviewed_status = row['Reviewed']
        
#         # Find the row in the sheet that corresponds to the observation ID
#         for i, sheet_row in enumerate(all_data[1:], start=2):  # Start at 2 because row 1 is headers
#             if sheet_row[headers.index('Observation ID')] == observation_id:
#                 # Update the "Reviewed" status in Google Sheets
#                 sheet.update_cell(i, reviewed_col_index, 'TRUE' if reviewed_status else 'FALSE')
#                 break

# # Google Sheets settings
# sheet_name = '2024 Healthtech Identify Log'

# # Load the "Case Log" and "Observation Log" data
# case_log_sheet = get_google_sheet(sheet_name, 'Case Log')
# observation_log_sheet = get_google_sheet(sheet_name, 'Observation Log')

# case_df = get_google_sheet_as_dataframe(case_log_sheet)
# observation_df = get_google_sheet_as_dataframe(observation_log_sheet)

# # Convert date column in case_df to datetime (replace 'Date' with the correct column name)
# case_df['Date'] = pd.to_datetime(case_df['Date'], errors='coerce')

# # Filter cases from the past week
# one_week_ago = datetime.now() - timedelta(days=7)
# recent_cases = case_df[case_df['Date'] >= one_week_ago]

# # st.markdown("### Cases in the last week")

# # Initialize session state for checkboxes if not already initialized
# if "reviewed_observations" not in st.session_state:
#     st.session_state["reviewed_observations"] = {}

# # Loop through each recent case and display it
# for index, case in recent_cases.iterrows():
#     st.markdown(f"#### Case ID: {case['Case ID']}")
#     st.text_area("Case Details", value=f"Details: {case['Case Description']}", height=150, key=f"case_{index}")

#     # Split the Observations column (assuming comma-separated IDs)
#     observation_ids = case['Observations'].split(",")  # Split by commas and remove any extra spaces
#     observation_ids = [obs_id.strip() for obs_id in observation_ids if obs_id.strip()]  # Clean and filter empty values
    
#     # Filter corresponding observations for the current case
#     relevant_observations = observation_df[observation_df['Observation ID'].isin(observation_ids)]
    
#     if not relevant_observations.empty:
#         st.markdown("#### Related Observations")
        
#         # Add a 'Reviewed' column with checkboxes for review
#         relevant_observations['Reviewed'] = relevant_observations.apply(lambda row: st.checkbox(f"Reviewed {row['Observation ID']}", value=st.session_state.get(f"reviewed_{row['Observation ID']}", False)), axis=1)

#         # Display observations as a DataFrame
#         st.dataframe(relevant_observations[['Observation ID', 'Observation Description', 'Reviewed']])

#         # Store the checkbox state in session_state
#         for obs_id in relevant_observations['Observation ID']:
#             st.session_state[f"reviewed_{obs_id}"] = relevant_observations[relevant_observations['Observation ID'] == obs_id]['Reviewed'].values[0]
#     else:
#         st.markdown("No related observations found.")

# st.markdown("---")

# # Button to print the reviewed status (or handle any action after review)
# if st.button("Submit Review"):
#     update_reviewed_status_in_sheet(observation_log_sheet, observation_df)
#     reviewed_count = sum([st.session_state.get(f"reviewed_{obs_id}", False) for obs_id in observation_df['Observation ID']])
#     st.success(f"{reviewed_count} observations marked as reviewed.")
    
















# import streamlit as st
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
# import pandas as pd
# from datetime import datetime, timedelta

# # Set page configuration
# st.set_page_config(page_title="Weekly Case and Observation Review", page_icon="📒", layout="wide")

# st.markdown("# Weekly Observation Review")

# # Google Sheets credentials
# creds_dict = {
#     "type": st.secrets["gwf_service_account"]["type"],
#     "project_id": st.secrets["gwf_service_account"]["project_id"],
#     "private_key_id": st.secrets["gwf_service_account"]["private_key_id"],
#     "private_key": st.secrets["gwf_service_account"]["private_key"].replace('\\n', '\n'),  # Fix formatting
#     "client_email": st.secrets["gwf_service_account"]["client_email"],
#     "client_id": st.secrets["gwf_service_account"]["client_id"],
#     "auth_uri": st.secrets["gwf_service_account"]["auth_uri"],
#     "token_uri": st.secrets["gwf_service_account"]["token_uri"],
#     "auth_provider_x509_cert_url": st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
#     "client_x509_cert_url": st.secrets["gwf_service_account"]["client_x509_cert_url"],
# }

# # Function to get Google Sheets connection
# def get_google_sheet(sheet_name, worksheet_name):
#     scope = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.metadata.readonly",
#     ]
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#     client = gspread.authorize(creds)
#     sheet = client.open(sheet_name).worksheet(worksheet_name)
#     return sheet

# # Function to convert Google Sheets data to a Pandas DataFrame
# def get_google_sheet_as_dataframe(sheet):
#     data = sheet.get_all_values()  # Get all data from the worksheet
#     df = pd.DataFrame(data[1:], columns=data[0])  # Use the first row as headers
#     return df

# # Google Sheets settings
# sheet_name = '2024 Healthtech Identify Log'

# # Load the "Case Log" and "Observation Log" data
# case_log_sheet = get_google_sheet(sheet_name, 'Case Log')
# observation_log_sheet = get_google_sheet(sheet_name, 'Observation Log')

# case_df = get_google_sheet_as_dataframe(case_log_sheet)
# observation_df = get_google_sheet_as_dataframe(observation_log_sheet)

# # Convert date column in case_df to datetime (replace 'Date' with the correct column name)
# case_df['Date'] = pd.to_datetime(case_df['Date'], errors='coerce')

# # Filter cases from the past week
# one_week_ago = datetime.now() - timedelta(days=7)
# recent_cases = case_df[case_df['Date'] >= one_week_ago]

# st.markdown("### Cases in the last week")

# # Loop through each recent case and display it
# for index, case in recent_cases.iterrows():
#     st.markdown(f"#### Case ID: {case['Case ID']}")
#     st.text_area("Case Details", value=f"Case ID: {case['Case ID']}\nDetails: {case['Case Description']}", height=150, key=f"case_{index}")

#     # Filter corresponding observations for the current case
#     observation_ids = case['Observations'].split(",")  # Assume observation IDs are comma-separated
#     relevant_observations = observation_df[observation_df['Observation ID'].isin(observation_ids)]
    
#     if not relevant_observations.empty:
#         st.markdown("#### Related Observations")
        
#         # Add a 'Reviewed' column with checkboxes for review
#         relevant_observations['Reviewed'] = relevant_observations.apply(lambda row: st.checkbox(f"Reviewed {row['Observation ID']}", value=st.session_state.get(f"reviewed_{row['Observation ID']}", False)), axis=1)

#         # Display observations as a DataFrame
#         st.dataframe(relevant_observations[['Observation ID', 'Observation Description', 'Reviewed']])

#         # Store the checkbox state in session_state
#         for obs_id in relevant_observations['Observation ID']:
#             st.session_state[f"reviewed_{obs_id}"] = relevant_observations[relevant_observations['Observation ID'] == obs_id]['Reviewed'].values[0]
#     else:
#         st.markdown("No related observations found.")

# st.markdown("---")

# # Button to print the reviewed status (or handle any action after review)
# if st.button("Submit Review"):
#     reviewed_count = sum([st.session_state.get(f"reviewed_{obs_id}", False) for obs_id in observation_df['Observation ID']])
#     st.success(f"{reviewed_count} observations marked as reviewed.")























# import streamlit as st
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
# import pandas as pd
# from datetime import datetime, timedelta

# # Set page configuration
# st.set_page_config(page_title="Weekly Case and Observation Review", page_icon="📒", layout="wide")

# st.markdown("# Weekly Observation Review")

# # Google Sheets credentials
# creds_dict = {
#     "type": st.secrets["gwf_service_account"]["type"],
#     "project_id": st.secrets["gwf_service_account"]["project_id"],
#     "private_key_id": st.secrets["gwf_service_account"]["private_key_id"],
#     "private_key": st.secrets["gwf_service_account"]["private_key"].replace('\\n', '\n'),  # Fix formatting
#     "client_email": st.secrets["gwf_service_account"]["client_email"],
#     "client_id": st.secrets["gwf_service_account"]["client_id"],
#     "auth_uri": st.secrets["gwf_service_account"]["auth_uri"],
#     "token_uri": st.secrets["gwf_service_account"]["token_uri"],
#     "auth_provider_x509_cert_url": st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
#     "client_x509_cert_url": st.secrets["gwf_service_account"]["client_x509_cert_url"],
# }

# # Function to get Google Sheets connection
# def get_google_sheet(sheet_name, worksheet_name):
#     scope = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.metadata.readonly",
#     ]
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#     client = gspread.authorize(creds)
#     sheet = client.open(sheet_name).worksheet(worksheet_name)
#     return sheet

# # Function to convert Google Sheets data to a Pandas DataFrame
# def get_google_sheet_as_dataframe(sheet):
#     # Get all data from the worksheet
#     data = sheet.get_all_values()
#     # Convert to a Pandas DataFrame
#     df = pd.DataFrame(data[1:], columns=data[0])  # Use the first row as headers
#     return df

# # Google Sheets settings
# sheet_name = '2024 Healthtech Identify Log'

# # Load the "Case Log" and "Observation Log" data
# case_log_sheet = get_google_sheet(sheet_name, 'Case Log')
# observation_log_sheet = get_google_sheet(sheet_name, 'Observation Log')

# case_df = get_google_sheet_as_dataframe(case_log_sheet)
# st.write("Columns in Case Log:", case_df.columns)

# observation_df = get_google_sheet_as_dataframe(observation_log_sheet)

# # Convert date column in case_df to datetime
# case_df['Date'] = pd.to_datetime(case_df['Date'])

# # Filter cases from the past week
# one_week_ago = datetime.now() - timedelta(days=7)
# recent_cases = case_df[case_df['Date'] >= one_week_ago]

# st.markdown("### Cases in the last week")

# # Display each recent case in a text box
# for index, case in recent_cases.iterrows():
#     st.markdown(f"#### Case ID: {case['Case ID']}")
#     st.text_area("Case Details", value=f"Case ID: {case['Case ID']}\nDetails: {case['Case Description']}", height=150, key=f"case_{index}")

# # Map Observation IDs from recent cases to the Observation Log
# observation_ids = recent_cases['Observations'].unique()
# observations_for_cases = observation_df[observation_df['Observation ID'].isin(observation_ids)]

# st.markdown("### Corresponding Observations")

# # Initialize session state for checkboxes if not already initialized
# if "reviewed_observations" not in st.session_state:
#     st.session_state["reviewed_observations"] = {}

# # Display observations with checkboxes for review status
# for index, observation in observations_for_cases.iterrows():
#     observation_id = observation['Observation ID']
#     col1, col2 = st.columns([8, 2])
    
#     with col1:
#         st.write(f"**Observation ID: {observation_id}**")
#         st.write(f"Details: {observation['Observation Description']}")
    
#     with col2:
#         # Checkbox for marking as reviewed
#         checked = st.checkbox("Reviewed", value=st.session_state["reviewed_observations"].get(observation_id, False), key=f"obs_{index}")
#         st.session_state["reviewed_observations"][observation_id] = checked

# st.markdown("---")

# # Button to print the reviewed status (or handle any action after review)
# if st.button("Submit Review"):
#     reviewed_count = sum(st.session_state["reviewed_observations"].values())
#     st.success(f"{reviewed_count} observations marked as reviewed.")
