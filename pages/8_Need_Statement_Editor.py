# ////////////////////// IMPORTS ////////////////////// IMPORTS ////////////////////// IMPORTS //////////////////////
import time
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from datetime import date
import logging
logging.basicConfig(level=logging.INFO)

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
# from langchain.callbacks import get_openai_callback
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnableLambda
from langchain.prompts import PromptTemplate
from langchain_pinecone import PineconeVectorStore

import gspread
from oauth2client.service_account import ServiceAccountCredentials


from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

import json
import os
import csv

import pandas as pd
import ast  # Import ast to handle conversion of string to list


# ////////////////////// INITIALIZATIONS ////////////////////// INITIALIZATIONS ////////////////////// INITIALIZATIONS ////////////////////// 

OPENAI_API_KEY = st.secrets["openai_key"]

# Access the credentials from Streamlit secrets
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

# Initialize the session state for the input if it doesn't exist
if 'need_ID_with_preview' not in st.session_state:
    st.session_state['need_ID_with_preview'] = ''

if 'need_statement' not in st.session_state:
    st.session_state['need_statement'] = ''

if 'problem_var' not in st.session_state:
    st.session_state['problem_var'] = ""

if 'population_var' not in st.session_state:
    st.session_state['population_var'] = ""

if 'outcome_var' not in st.session_state:
    st.session_state['outcome_var'] = ""

if 'notes' not in st.session_state:
    st.session_state['notes'] = ""

if 'notes' not in st.session_state:
    st.session_state['notes'] = ""


if 'related_observation_ID_w_title' not in st.session_state:
    st.session_state['related_observation_ID_w_title'] = ""

if 'result' not in st.session_state:
    st.session_state['result'] = ""

if 'rerun' not in st.session_state:
    st.session_state['rerun'] = False

if 'selected_need_ID' not in st.session_state:
    st.session_state['selected_need_ID'] = ""

# ////////////////////// FUNCTIONS ////////////////////// FUNCTIONS ////////////////////// FUNCTIONS ////////////////////// 

def getExistingNeedIDS(df):
    # Assume `df` is the DataFrame that corresponds to the "Need Statement Log" Google Sheet
    # Extract the "need_ID" column (first column) and "preview" column (third column)
    need_ids = df['need_ID'].tolist()  # Extract all values in the need_ID column
    need_previews = df['need_statement'].tolist()  # Extract all values in the preview column

    # Combine the need IDs and their previews into a dictionary
    existing_need_ids_with_preview = dict(zip(need_ids, need_previews))

    # Create strings in the format "need_ID - preview"
    existing_need_ids_with_preview = [f"{need_id} - {preview}" for need_id, preview in existing_need_ids_with_preview.items()]

    print("Existing Observation IDS: ")
    print(existing_need_ids_with_preview)
    return existing_need_ids_with_preview

# Function to connect to Google Sheets
def get_google_sheet(sheet_name, worksheet_name):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).worksheet(worksheet_name)
    return sheet

# Fetch need details based on selected need ID
def fetch_need_details(selected_need_ID, need_df):
    # Iterate over rows of the DataFrame using iterrows()
    for index, row in need_df.iterrows():
        # Access the value using row["need_ID"]
        if "need_ID" in row and row["need_ID"].strip() == selected_need_ID.strip():
            return row.to_dict()  # Convert the row to a dictionary for easy handling
    
    st.error(f"Need ID {selected_need_ID} not found.")
    return None


# Update case details in Google Sheets
def update_need(selected_need_ID, updated_need_data):
    # i = 2
    try:
        sheet = get_google_sheet("2024 Healthtech Identify Log", "Need Statement Log")
        data = sheet.get_all_records()

       
        # Find the row corresponding to the selected_need_ID and update it
        for i, row in enumerate(data, start=2):  # Skip header row
            if row["need_ID"] == st.session_state['selected_need_ID']:
                # Update the necessary fields (Assuming the updated_need_data has the same keys as Google Sheets columns)
                for key, value in updated_need_data.items():
                    sheet.update_cell(i, list(row.keys()).index(key) + 1, value)
                return True
        return False
    except Exception as e:
        st.write("Update failed")

        print(f"Error updating case: {e}")
        return False


# FUNCTIONS here for observation ID handling ///////////////////////////

# Connect to Google Sheets using Streamlit secrets
def connect_to_google_sheet():
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
        "universe_domain": st.secrets["gwf_service_account"]["universe_domain"],
    }

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client1 = gspread.authorize(creds)
    return client1

# Initialize Google Sheets connection
client1 = connect_to_google_sheet()
sheet_name1 = "2024 Healthtech Identify Log"

# Load the Google Sheet
sheet1 = client1.open(sheet_name1)


# Load data from the specific worksheets
def load_data(sheet1, worksheet_name1):
    worksheet1 = sheet1.worksheet(worksheet_name1)
    data = worksheet1.get_all_records()
    return pd.DataFrame(data)

def display_selected_observations(selected_obs_ids, obs_log_df):
   
    # Iterate over all selected Observation IDs and display the corresponding description
    for obs_id in selected_obs_ids:
        clean_obs_id = obs_id.split(" - ")[0]  # Extract only the Observation ID
        selected_observation = obs_log_df[obs_log_df['Observation ID'] == clean_obs_id]
        if not selected_observation.empty:
            observation_description = selected_observation.iloc[0]['Observation Description']
            st.markdown(f"### {clean_obs_id} Description:\n{observation_description}")
        else:
            st.info(f"No description available for {obs_id}.")





# ////////////////////// CODE ON PAGE ////////////////////// CODE ON PAGE ////////////////////// CODE ON PAGE //////////////////////

st.set_page_config(page_title="Need Statement Editor", page_icon=":pencil:")

st.markdown("# Edit a Need Statement")
st.write("Use this tool to edit your need statements. Be sure to include notes about your revisions.")


# Fetch data from sheets
need_statement_df = load_data(sheet1, "Need Statement Log")
observation_log_df = load_data(sheet1, "Observation Log")

# select from a list of needs
existing_need_ids_with_preview = getExistingNeedIDS(need_statement_df)




# Step 1: Fetch and display need IDs in a dropdown
if not existing_need_ids_with_preview:
    st.error("No needs found.")
else:
    # get ID from the dropdown value
    st.session_state['need_ID_with_preview'] = st.selectbox("Select Need Statement", existing_need_ids_with_preview)
    st.session_state['selected_need_ID'] = st.session_state.need_ID_with_preview.split(" - ")[0]

# Step 2: Fetch and display need details for the selected need
    if  st.session_state['need_ID_with_preview']:
        need_details = fetch_need_details(st.session_state['selected_need_ID'], need_statement_df)
        # st.write(need_details)
        with st.expander("View Original Need Statement Details", expanded=False):
            st.write(need_details)

        if need_details:
           
            
            # amend code here for observation ID handling ///////////////////////////
            
            
            # Fetch observation_IDs associated with the selected need_ID
            matching_row = need_statement_df[need_statement_df['need_ID'] == st.session_state['selected_need_ID']]
            
            if not matching_row.empty:
                # Get the observation_IDs as a string and convert it into a list
                observation_ids_str = matching_row.iloc[0]['observation_ID']
                st.write(f"Raw observation_ids_str: {observation_ids_str}")  # Debugging statement

                
                # Split the string by commas to convert it into a list
                observation_ids = [obs_id.strip() for obs_id in observation_ids_str.split(',')]
                st.write(f"Parsed observation_ids list: {observation_ids}")  # Debugging statement

        
                # Find the Observation Titles corresponding to each observation_ID
                observation_ids_with_title = []
                for obs_id in observation_ids:
                    obs_row = observation_log_df[observation_log_df['Observation ID'] == obs_id]
                    if not obs_row.empty:
                        observation_title = obs_row.iloc[0]['Observation Title']
                        observation_ids_with_title.append(f"{obs_id} - {observation_title}")

                 # Make sure observation_ids_with_title is a list even if there's only one item
                if isinstance(observation_ids_with_title, str):
                    observation_ids_with_title = [observation_ids_with_title]
                    st.write(f"Final observation_ids_with_title: {observation_ids_with_title}")


                
                # Create a master list of all observations with ID and Title
                all_observations = [f"{row['Observation ID']} - {row['Observation Title']}" for _, row in observation_log_df.iterrows()]
                
                # Multiselect dropdown for the user to refine or add to their selection
                st.session_state['related_observation_ID_w_title'] = st.multiselect(
                    "Select Observation IDs with Titles:", 
                    options=all_observations, 
                    default=observation_ids_with_title
                )

                display_selected_observations(st.session_state['related_observation_ID_w_title'], observation_log_df)
                # Remove titles from the selected observation IDs
                selected_observation_ids = [obs.split(" - ")[0].strip() for obs in st.session_state['related_observation_ID_w_title']]
        
                # Store them in the need_details dictionary
                need_details["observation_ID"] = selected_observation_ids

        
            else:
                st.warning("No matching observations found for the selected Need ID.")


            # amend code here for observation ID handling ///////////////////////////

            
            problem_var = st.text_input("Problem", need_details.get("problem", ""))
            population_var = st.text_input("Population", need_details.get("population", ""))
            outcome_var = st.text_input("Outcome", need_details.get("outcome", ""))
            need_statement = st.text_input("Need Statement", need_details.get("need_statement", ""))
            # tags = st.text_input("Tags", need_details.get("Tags", ""))
            notes = st.text_area("Notes", need_details.get("notes", ""))
            
    
             # Get and validate the date field
            need_date_str = need_details.get("need_date", "")
            try:
                        # Try to parse the date from ISO format, or default to today's date
                case_date = date.fromisoformat(need_date_str) if need_date_str else date.today()
            except ValueError:
                case_date = date.today()
    
            case_date_input = st.date_input("Date (YYYY/MM/DD)", case_date)
            
                
# Step 3: Save changes
            if st.button("Save Changes"):
                updated_need_data = {
                    "need_date": case_date_input.isoformat(),
                    "need_statement": need_statement,
                    "problem": problem_var,
                    "population": population_var,
                    "outcome": outcome_var,
                    "observation_ID": ', '.join(selected_observation_ids),  # Convert list to comma-separated string
                    "notes": notes,
                }
                
                if update_need(st.session_state['selected_need_ID'], updated_need_data):
                    st.success(f"Changes to '{st.session_state['selected_need_ID']}' saved successfully!")
                else:
                    st.error(f"Failed to save changes to '{st.session_state['selected_need_ID']}'.")


# ////////////////////// DRAFT ////////////////////// DRAFT ////////////////////// DRAFT ////////////////////// 




# ////////////////////// NOTES ////////////////////// NOTES ////////////////////// NOTES ////////////////////// 



















#  OLD OLD OLD OLD OLD OLD OL DOL DOLD O LDOLDO ODL DOL DOL DO LDO LDO LDOLDO LDOLOLD OLD OLD






# # ////////////////////// IMPORTS ////////////////////// IMPORTS ////////////////////// IMPORTS //////////////////////
# import time
# import streamlit as st
# from streamlit_extras.switch_page_button import switch_page
# from datetime import date
# import logging
# logging.basicConfig(level=logging.INFO)

# from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# from langchain.chains import LLMChain
# from langchain.output_parsers import PydanticOutputParser
# # from langchain.callbacks import get_openai_callback
# from langchain.schema import StrOutputParser
# from langchain.schema.runnable import RunnableLambda
# from langchain.prompts import PromptTemplate
# from langchain_pinecone import PineconeVectorStore

# import gspread
# from oauth2client.service_account import ServiceAccountCredentials


# from pydantic import BaseModel, Field
# from typing import Optional
# from datetime import date, datetime

# import json
# import os
# import csv

# import pandas as pd

# # ////////////////////// INITIALIZATIONS ////////////////////// INITIALIZATIONS ////////////////////// INITIALIZATIONS ////////////////////// 

# OPENAI_API_KEY = st.secrets["openai_key"]

# # Access the credentials from Streamlit secrets
# creds_dict = {
#     "type" : st.secrets["gwf_service_account"]["type"],
#     "project_id" : st.secrets["gwf_service_account"]["project_id"],
#     "private_key_id" : st.secrets["gwf_service_account"]["private_key_id"],
#     "private_key" : st.secrets["gwf_service_account"]["private_key"],
#     "client_email" : st.secrets["gwf_service_account"]["client_email"],
#     "client_id" : st.secrets["gwf_service_account"]["client_id"],
#     "auth_uri" : st.secrets["gwf_service_account"]["auth_uri"],
#     "token_uri" : st.secrets["gwf_service_account"]["token_uri"],
#     "auth_provider_x509_cert_url" : st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
#     "client_x509_cert_url" : st.secrets["gwf_service_account"]["client_x509_cert_url"],
#     "universe_domain": st.secrets["gwf_service_account"]["universe_domain"],
# }

# # Initialize the session state for the input if it doesn't exist
# if 'need_ID_with_preview' not in st.session_state:
#     st.session_state['need_ID_with_preview'] = ''

# # if 'need_ID' not in st.session_state:
# #     st.session_state.need_ID = ''

# if 'need_statement' not in st.session_state:
#     st.session_state['need_statement'] = ''

# if 'problem_var' not in st.session_state:
#     st.session_state['problem_var'] = ""

# if 'population_var' not in st.session_state:
#     st.session_state['population_var'] = ""

# if 'outcome_var' not in st.session_state:
#     st.session_state['outcome_var'] = ""

# if 'notes' not in st.session_state:
#     st.session_state['notes'] = ""

# if 'observation_ID' not in st.session_state:
#     st.session_state['observation_ID'] = ""

# if 'result' not in st.session_state:
#     st.session_state['result'] = ""

# if 'rerun' not in st.session_state:
#     st.session_state['rerun'] = False

# if 'selected_need_ID' not in st.session_state:
#     st.session_state['selected_need_ID'] = ""

# # ////////////////////// FUNCTIONS ////////////////////// FUNCTIONS ////////////////////// FUNCTIONS ////////////////////// 


# # get need IDs with preview
# def getExistingNeedIDS():
#     scope = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.metadata.readonly"
#         ]
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#     client = gspread.authorize(creds)
#     need_log = client.open("2024 Healthtech Identify Log").worksheet("Need Statement Log")
#     need_ids = need_log.col_values(1)[1:]
#     need_previews = need_log.col_values(3)[1:]

#     # find all observation ids with the same date
#     existing_need_ids_with_preview = dict(zip(need_ids, need_previews))

#     # make strings with case id - preview
#     existing_need_ids_with_preview = [f"{need_ids} - {need_previews}" for need_ids, need_previews in existing_need_ids_with_preview.items()]

#     print("Existing Observation IDS: ")
#     print(existing_need_ids_with_preview)
#     return existing_need_ids_with_preview

# # Function to connect to Google Sheets
# def get_google_sheet(sheet_name, worksheet_name):
#     scope = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.metadata.readonly",
#     ]
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#     client = gspread.authorize(creds)
#     sheet = client.open(sheet_name).worksheet(worksheet_name)
#     return sheet

# # Fetch case details based on selected case ID
# def fetch_need_details(selected_need_ID):
#     sheet = get_google_sheet("2024 Healthtech Identify Log", "Need Statement Log")
#     need_data = sheet.get_all_records()

#     for row in need_data:
#         if "need_ID" in row and row["need_ID"].strip() == st.session_state['selected_need_ID'].strip():
#             return row
    
#     st.error(f"Need ID {st.session_state['selected_need_ID']} not found.")
#     return None


# # Update case details in Google Sheets
# def update_need(selected_need_ID, updated_need_data):
#     # i = 2
#     try:
#         sheet = get_google_sheet("2024 Healthtech Identify Log", "Need Statement Log")
#         data = sheet.get_all_records()

       
#         # Find the row corresponding to the selected_need_ID and update it
#         for i, row in enumerate(data, start=2):  # Skip header row
#             if row["need_ID"] == st.session_state['selected_need_ID']:
#                 # Update the necessary fields (Assuming the updated_need_data has the same keys as Google Sheets columns)
#                 for key, value in updated_need_data.items():
#                     sheet.update_cell(i, list(row.keys()).index(key) + 1, value)
#                 return True
#         return False
#     except Exception as e:
#         print(f"Error updating case: {e}")
#         return False



# def getExistingObsIDS():
#     scope = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.metadata.readonly"
#         ]
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#     client = gspread.authorize(creds)
#     obs_log = client.open("2024 Healthtech Identify Log").worksheet("Observation Log")
#     obs_ids = obs_log.col_values(1)[1:]
#     # obs_descrip = obs_log.col_values(5)[1:]
#     obs_titles = obs_log.col_values(2)[1:]

#     # find all observation ids with the same date
#     existing_obs_ids_with_title = dict(zip(obs_ids, obs_titles))

#     # make strings with case id - title
#     existing_obs_ids_with_title = [f"{case_id} - {case_title}" for case_id, case_title in existing_obs_ids_with_title.items()]

#     # existing_obs_descrip = dict(zip(obs_ids, obs_descrip))


#     print("Existing Observation IDS: ")
#     print(existing_obs_ids_with_title)
#     return existing_obs_ids_with_title


# def display_selected_observation(selected_obs_id):
#     obs_log = get_google_sheet("2024 Healthtech Identify Log", "Observation Log")
#     df = pd.DataFrame(obs_log.get_all_records())

#     # Get the observation description based on the selected Observation ID
#     if selected_obs_id:
#         selected_observation = df[df['Observation ID'] == selected_obs_id]
#         if not selected_observation.empty:
#             observation_description = selected_observation.iloc[0]['Observation Description']
#             st.markdown(f"### {selected_obs_id} Description:\n{observation_description}")
#             # st.markdown(f"### Selected Observation Description:\n{observation_description}")
#         else:
#             st.info("No description available for this observation.")
#     else:
#         st.info("Please select an observation.")



# # ////////////////////// CODE ON PAGE ////////////////////// CODE ON PAGE ////////////////////// CODE ON PAGE //////////////////////

# st.set_page_config(page_title="Need Statement Editor", page_icon=":pencil:")

# st.markdown("# Edit a Need Statement")
# st.write("Use this tool to edit your need statements. Be sure to include notes about your revisions.")




# # Dropdown menu for selecting action
# # action = st.selectbox("Choose an action", ["Add New Case", "Edit Existing Case"])


# # select from a list of needs
# existing_need_ids_with_preview = getExistingNeedIDS()

# # st.session_state['need_ID']

# # if selected_need_ID: #may need to make this session state whatever

# # Step 1: Fetch and display need IDs in a dropdown
# if not existing_need_ids_with_preview:
#     st.error("No needs found.")
# else:
#     # get ID from the dropdown value
#     st.session_state['need_ID_with_preview'] = st.selectbox("Select Need Statement", existing_need_ids_with_preview)
#     st.session_state['selected_need_ID'] = st.session_state.need_ID_with_preview.split(" - ")[0]

# # Step 2: Fetch and display need details for the selected need
#     if  st.session_state['need_ID_with_preview']:
#         need_details = fetch_need_details(st.session_state['selected_need_ID'])

#         #adding this for observation handling
#       #  need_details = fetch_observation_details(st.session_state['selected_need_ID'])



#         # need_details = fetch_need_details(need_to_edit)
#         if need_details:
#             # # Debug: Print the case details (optional)
#             # st.write(f"Editing case: {need_details}")
#             # Editable fields for the selected case
#             #case_date = st.date_input("Date", date.fromisoformat(need_details.get("Date", str(date.today()))))
#             # case_description = st.text_area("Case Description", need_details.get("Case Description", ""))
#             related_observation_ID = st.text_input("Observation", need_details.get("observation_ID", ""))
#             problem_var = st.text_input("Problem", need_details.get("problem", ""))
#             population_var = st.text_input("Population", need_details.get("population", ""))
#             outcome_var = st.text_input("Outcome", need_details.get("outcome", ""))
#             need_statement = st.text_input("Need Statement", need_details.get("need_statement", ""))
#             # tags = st.text_input("Tags", need_details.get("Tags", ""))
#             notes = st.text_area("Notes", need_details.get("notes", ""))
#             existing_obs_ids_with_title = getExistingObsIDS()
#             # st.session_state['obs_id_with_title'] = st.selectbox("Related Observation ID", existing_obs_ids_with_title)

# #  INSTEAD of ABOVE -- fetch observation ID from the sheet

# # df_descrips = pd.DataFrame(existing_obs_descrip)

#             # if st.session_state['obs_id_with_title']:
#             #     selected_obs_id = st.session_state['obs_id_with_title'].split(" - ")[0] if st.session_state['obs_id_with_title'] else None
#             #     display_selected_observation(selected_obs_id)


    
#              # Get and validate the date field
#             need_date_str = need_details.get("need_date", "")
#             try:
#                         # Try to parse the date from ISO format, or default to today's date
#                 case_date = date.fromisoformat(need_date_str) if need_date_str else date.today()
#             except ValueError:
#                 case_date = date.today()
    
#             case_date_input = st.date_input("Date (YYYY/MM/DD)", case_date)
            
                
# # Step 3: Save changes
#             if st.button("Save Changes"):
#                 updated_need_data = {
#                     "need_date": case_date_input.isoformat(),
#                     "need_statement": need_statement,
#                     "problem": problem_var,
#                     "population": population_var,
#                     "outcome": outcome_var,
#                     "notes": notes,
#                 }
                
#                 if update_need(st.session_state['selected_need_ID'], updated_need_data):
#                     st.success(f"Changes to '{st.session_state['selected_need_ID']}' saved successfully!")
#                 else:
#                     st.error(f"Failed to save changes to '{st.session_state['selected_need_ID']}'.")


# # ////////////////////// DRAFT ////////////////////// DRAFT ////////////////////// DRAFT ////////////////////// 




# # ////////////////////// NOTES ////////////////////// NOTES ////////////////////// NOTES ////////////////////// 













