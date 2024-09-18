












import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Set page configuration
st.set_page_config(page_title="View Logs", page_icon="📒", layout="wide")
# title
st.markdown("# View Logs")
# description
st.write("Use this page to view your logged information. Toggle between logs using the dropdown.")


# Define the Google Sheets credentials and scope
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




# //// WIP //// WIP //// WIP //// Function to append an Observation ID to the "Observations" column in the Case Log worksheet //// WIP //// WIP //// WIP //// WIP //// WIP ////
def append_observation_to_case(case_log_sheet, case_id, new_observation_id):
    # Get all data from the Case Log sheet
    all_data = case_log_sheet.get_all_values()
    
    # Find the index of the columns
    headers = all_data[0]
    case_id_col_index = headers.index('Case ID') + 1  # Convert to 1-based index for gspread
    observations_col_index = headers.index('Observations') + 1  # Convert to 1-based index
    
    # Find the row with the matching Case ID
    for i, row in enumerate(all_data[1:], start=2):  # Start at 2 because row 1 is headers
        if row[headers.index('Case ID')] == case_id:
            # Get the existing observations (if any)
            existing_observations = row[headers.index('Observations')]
            if existing_observations:
                existing_observations_list = [obs.strip() for obs in existing_observations.split(",") if obs.strip()]
            else:
                existing_observations_list = []
            
            # Check if the new Observation ID already exists
            if new_observation_id not in existing_observations_list:
                # Append the new Observation ID to the list
                updated_observations = existing_observations_list + [new_observation_id]
                
                # Update the cell in Google Sheets with the new value
                case_log_sheet.update_cell(i, observations_col_index, ", ".join(updated_observations))
                st.success(f"Observation ID '{new_observation_id}' has been added to Case ID '{case_id}'.")
            else:
                st.info(f"Observation ID '{new_observation_id}' already exists for Case ID '{case_id}'.")
            return
    st.error(f"Case ID '{case_id}' not found in the Case Log.")




# # Function to append an Observation ID to the "Observations" column in the Case Log worksheet
# def append_observation_to_case(case_log_sheet, case_id, new_observation_id):
#     # Get all data from the Case Log sheet
#     all_data = case_log_sheet.get_all_values()
    
#     # Find the index of the columns
#     headers = all_data[0]
#     case_id_col_index = headers.index('Case ID') + 1  # Convert to 1-based index for gspread
#     observations_col_index = headers.index('Observations') + 1  # Convert to 1-based index
    
#     # Find the row with the matching Case ID
#     for i, row in enumerate(all_data[1:], start=2):  # Start at 2 because row 1 is headers
#         if row[headers.index('Case ID')] == case_id:
#             # Get the existing observations (if any)
#             existing_observations = row[headers.index('Observations')]
#             if existing_observations:
#                 existing_observations_list = [obs.strip() for obs in existing_observations.split(",") if obs.strip()]
#             else:
#                 existing_observations_list = []
            
#             # Check if the new Observation ID already exists
#             if new_observation_id not in existing_observations_list:
#                 # Append the new Observation ID to the list
#                 updated_observations = existing_observations_list + [new_observation_id]
                
#                 # Update the cell in Google Sheets with the new value
#                 case_log_sheet.update_cell(i, observations_col_index, ", ".join(updated_observations))
#                 st.success(f"Observation ID '{new_observation_id}' has been added to Case ID '{case_id}'.")
#             else:
#                 st.info(f"Observation ID '{new_observation_id}' already exists for Case ID '{case_id}'.")
#             return
#     st.error(f"Case ID '{case_id}' not found in the Case Log.")




# import streamlit as st
# import pandas as pd

# testvar = 42069
# st.session_state['need_ID'] = testvar

# # Assume you have a session state variable 'need_ID'
# if 'need_ID' not in st.session_state:
#     st.session_state.need_ID = 'some_value'  # replace 'some_value' with the actual value

# # Assume you have a DataFrame 'df' in the session state
# if 'df' not in st.session_state:
#     st.session_state.df = pd.DataFrame({
#         'Need ID': st.session_state.need_ID,
#         'A': range(1, 8),
#         # 'B': range(10, 15)
#     })

# # Add 'need_ID' to the DataFrame
# st.session_state.df['need_ID'] = st.session_state.need_ID

# # Display the updated DataFrame
# st.write(st.session_state.df)
