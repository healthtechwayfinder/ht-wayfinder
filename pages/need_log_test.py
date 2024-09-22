import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

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
    client = gspread.authorize(creds)
    return client

# Initialize Google Sheets connection
client = connect_to_google_sheet()
sheet_name = "2024 Healthtech Identify Log"

# Load the Google Sheet
sheet = client.open(sheet_name)

# Load data from the specific worksheets
def load_data(sheet, worksheet_name):
    worksheet = sheet.worksheet(worksheet_name)
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

# Fetch data from sheets
need_statement_df = load_data(sheet, "Need Statement Log")
observation_log_df = load_data(sheet, "Observation Log")

# Streamlit interface
st.title("Healthtech Identify Log System")

# Dropdown for selecting need_ID
need_id_selected = st.selectbox("Select a need_ID:", need_statement_df['need_ID'].unique())

if need_id_selected:
    # Fetch observation_IDs associated with the selected need_ID
    matching_row = need_statement_df[need_statement_df['need_ID'] == need_id_selected]
    
    if not matching_row.empty:
        observation_ids_str = matching_row.iloc[0]['observation_ID']
        observation_ids = observation_ids_str.split(',')

        # Find the Observation Titles corresponding to the observation_IDs
        observation_titles = []
        for obs_id in observation_ids:
            obs_row = observation_log_df[observation_log_df['Observation ID'] == obs_id.strip()]
            if not obs_row.empty:
                observation_titles.append(obs_row.iloc[0]['Observation Title'])
        
        # Combine observation_IDs and Titles
        observation_ids_with_title = [f"{obs_id.strip()} - {title}" for obs_id, title in zip(observation_ids, observation_titles)]

        # Get all observation IDs and Titles for the master list
        all_observations = [f"{row['Observation ID']} - {row['Observation Title']}" for _, row in observation_log_df.iterrows()]
        
        # Multiselect dropdown for user to select more or refine selection
        selected_observations = st.multiselect(
            "Select Observation IDs with Titles:", 
            options=all_observations, 
            default=observation_ids_with_title
        )
        
        # Remove titles from the selected observation IDs
        selected_observation_ids = [obs.split(" - ")[0].strip() for obs in selected_observations]

        # Store them in the need_details dictionary
        need_details = {"observation_ID": selected_observation_ids}
        
        st.write("Selected Observation IDs:", need_details.get("observation_ID"))

    else:
        st.warning("No matching observations found for the selected need_ID.")





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
#     sheet1 = client.open(sheet_name).worksheet(worksheet_name)
#     return sheet1

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
#         sheet2 = get_google_sheet("2024 Healthtech Identify Log", "Need Statement Log")
#         data = sheet2.get_all_records()

       
#         # Find the row corresponding to the selected_need_ID and update it
#         for i, row in enumerate(data, start=2):  # Skip header row
#             if row["need_ID"] == st.session_state['selected_need_ID']:
#                 # Update the necessary fields (Assuming the updated_need_data has the same keys as Google Sheets columns)
#                 for key, value in updated_need_data.items():
#                     sheet2.update_cell(i, list(row.keys()).index(key) + 1, value)
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


# # Create an expander
# need_instructions = st.expander("Click for instructions...")

# # Add text to the expander
# need_instructions.write("Use this tool to edit your need statements. Be sure to include notes about your revisions.")
# # st.write("Use this tool to edit your need statements. Be sure to include notes about your revisions.")




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




# ////////////////////// NOTES ////////////////////// NOTES ////////////////////// NOTES ////////////////////// 





















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



# st.set_page_config(page_title="Create a New Need Statement", page_icon=":pencil2:")
# st.markdown("# Create a New Need Statement")
# st.write("Use this tool to record needs as you draft them. Select the date that the need was generated, and a unique identifier will auto-populate. In the next box, select all related observations.")
# st.write("Start by outlining the problem, population, and outcome, and then enter the whole statement in the corresponding text box. In the last box, add any relevant notes -- things like how you might want to workshop the statement, specific insights, assumptions in the statement that need validation, or opportunities for improvement or more research.")



# need_csv = "need.csv"
# OPENAI_API_KEY = st.secrets["openai_key"]

# # Access the credentials from Streamlit secrets
# #test
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

# # Recorded variables:
# # need_date
# # need_ID
# # observation_ID
# # need_statement
# # problem
# # population
# # outcome

# # Initialize the session state for the input if it doesn't exist


# if 'obs_id_with_title' not in st.session_state:
#     st.session_state.obs_id_with_title = ''

# if 'need_statement' not in st.session_state:
#     st.session_state.need_statement = ''

# if 'problem' not in st.session_state:
#     st.session_state['problem'] = ""

# if 'population' not in st.session_state:
#     st.session_state['population'] = ""

# if 'outcome' not in st.session_state:
#     st.session_state['outcome'] = ""

# if 'notes' not in st.session_state:
#     st.session_state['notes'] = ""

# if 'observation_ID' not in st.session_state:
#     st.session_state['observation_ID'] = ""

# if 'result' not in st.session_state:
#     st.session_state['result'] = ""

# if 'rerun' not in st.session_state:
#     st.session_state['rerun'] = False

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

# def addToGoogleSheets(need_dict):
#     try:
#         scope = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.metadata.readonly"
#         ]
#         creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#         client = gspread.authorize(creds)
#         need_sheet = client.open("2024 Healthtech Identify Log").worksheet('Need Statement Log')

#         headers = need_sheet.row_values(1)

#         # Prepare the row data matching the headers
#         row_to_append = []
#         for header in headers:
#             if header in need_dict:
#                 value = need_dict[header]
#                 if value is None:
#                     row_to_append.append("")
#                 else:
#                     row_to_append.append(str(need_dict[header]))
#             else:
#                 row_to_append.append("")  # Leave cell blank if header not in dictionary

#         # Append the row to the sheet
#         need_sheet.append_row(row_to_append)
#         return True
#     except Exception as e:
#         print("Error adding to Google Sheets: ", e)
#         return False
#     # variables recorded: 'need_ID', 'need_date', 'need_statement', 'problem', 'population', 'outcome', 'observation_ID'


# # put in correct format & call function to upload to google sheets
# def recordNeed(need_ID, need_date, need_statement, problem, population, outcome, observation_ID, notes):
    
#     all_need_keys = ['need_ID', 'need_date', 'need_statement', 'problem', 'population', 'outcome', 'observation_ID', 'notes'] # + need_keys
#     need_values = [need_ID, need_date, need_statement, problem, population, outcome, observation_ID, notes] # + [parsed_need[key] for key in need_keys]
#     need_dict = dict(zip(all_need_keys, need_values))

#     status = addToGoogleSheets(need_dict)

#     return status
    

# # Initialize or retrieve the clear_need counters dictionary from session state
# if 'need_counters' not in st.session_state:
#     st.session_state['need_counters'] = {}




# # New function for getting observation IDs
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




# # Function to generate need ID with the format NSYYMMDDxxxx
# def generate_need_ID(need_date, counter):
#     return f"NS{need_date.strftime('%y%m%d')}{counter:04d}"

# # Function to update need ID when the date changes
# def update_need_ID():
#     obs_date_str = st.session_state['need_date'].strftime('%y%m%d')

#     # get all need ids from the sheets and update the counter
#     scope = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.metadata.readonly"
#         ]
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#     client = gspread.authorize(creds)
#     need_sheet = client.open("2024 Healthtech Identify Log").worksheet('Need Statement Log')
#     column_values = need_sheet.col_values(1) 

#     # find all need ids with the same date
#     obs_date_ids = [obs_id for obs_id in column_values if obs_id.startswith(f"NS{obs_date_str}")]
#     obs_date_ids.sort()

#     # get the counter from the last need id
#     if len(obs_date_ids) > 0:
#         counter = int(obs_date_ids[-1][-4:])+1
#     else:
#         counter = 1

#     st.session_state['need_ID'] = generate_need_ID(st.session_state['need_date'], counter)

# # Fetch the observation IDs from the Google Sheet
# # observation_ID_list = getObservationIDs()



# # Function to clear form inputs
# def clear_form():
#     st.session_state.need_statement = ''
#     st.session_state.problem = ''
#     st.session_state.population = ''
#     st.session_state.outcome = ''
#     st.session_state.notes = ''



# # Function to handle form submission
# def submit_form():
#     # split the observation ID from the descriptive title
#     st.session_state['observation_ID'] = st.session_state.obs_id_with_title.split(" - ")[0]

#     # refresh the need ID once again, make sure the need ID is UTD in case anyone else has submitted one while this need statement was being authored
#     update_need_ID()

#     # send input to google sheets    
#     recordNeed(st.session_state['need_ID'], st.session_state['need_date'], st.session_state['need_statement'], st.session_state['problem'], st.session_state['population'], st.session_state['outcome'], st.session_state['observation_ID'], st.session_state['notes'])
#     update_need_ID()
    
#     # Clear the form after sending to sheets
#     clear_form()
    
#     # lil confirmation message
#     st.write('<p style="color:green;">Need statement recorded!</p>', unsafe_allow_html=True)


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

# # prepare list of observations and prompt user to pick one
# existing_obs_ids_with_title = getExistingObsIDS()
# st.session_state['obs_id_with_title'] = st.selectbox("Related Observation ID", existing_obs_ids_with_title)

# # df_descrips = pd.DataFrame(existing_obs_descrip)

# if st.session_state['obs_id_with_title']:
#     selected_obs_id = st.session_state['obs_id_with_title'].split(" - ")[0] if st.session_state['obs_id_with_title'] else None
#     display_selected_observation(selected_obs_id)

    
#     # df_descrips = pd.DataFrame(existing_obs_descrip)
#     # st.dataframe(df_descrips)


# col1, col2 = st.columns(2)

# # date
# with col1:
#     st.date_input("Need Date", date.today(), on_change=update_need_ID, key="need_date")
    
# # need ID
# with col2:
#     if 'need_ID' not in st.session_state:
#         update_need_ID()
#     # Display the need ID
#     st.text_input("Need ID (auto-generated):", value=st.session_state['need_ID'], disabled=True)
    
#     # enter relevant observation IDs
# # with col3:
#     # observation_ID = st.multiselect("Relevant Observations (multi-select):", observation_ID_list)
    

# # Create the form
# with st.form("my_form"):
#     # Text input tied to session state
    
#     col1, col2, col3 = st.columns(3)

#     with col1:
#         st.text_input("Problem:", key='problem')

#     # population
#     with col2:
#         st.text_input("Population:", key='population')
    
#     # enter relevant observation IDs & outcome text
#     with col3:
#         # observation_ID = st.multiselect("Relevant Observations (multi-select):", observation_ID_list)
#         st.text_input("Outcome:", key='outcome')

#     # enter need statement
#     st.text_input("Need Statement:", key='need_statement')
#     st.text_input("Notes:", key='notes')

#     # Form submit button with a callback function
#     submitted = st.form_submit_button("Submit", on_click=submit_form)



# # yet unsure of what the rest of this does:

# with col3:
#     # Button to Clear the Observation Text Area
#     # st.button("Clear Observation", on_click=clear_text) 
#     # Container for result display
#     result_container = st.empty()
    

   
    
    
# st.markdown(st.session_state['result'], unsafe_allow_html=True)

# if st.session_state['rerun']:
#     time.sleep(3)
#     #clear_need()
#     st.session_state['rerun'] = False
#     st.rerun()
    
    

# st.markdown("---")


# # st.markdown("---")
# # Apply custom CSS to make the button blue
# st.markdown("""
#     <style>
#     div.stButton > button {
#         background-color: #A51C30;
#         color: white;
#         font-size: 16px;
#         padding: 10px 20px;
#         border: none;
#         border-radius: 5px;
#     }
#     div.stButton > button:hover {
#         background-color: #E7485F;
#         color: white;
#     }
#     </style>
#     """, unsafe_allow_html=True)



# # Create a button using Streamlit's native functionality
# st.markdown("<br>", unsafe_allow_html=True)

# if st.button("Back to Dashboard"):
#     switch_page("Dashboard")
































# # import streamlit as st
# # from streamlit_extras.switch_page_button import switch_page

# # from pydantic import BaseModel, Field
# # from typing import Optional
# # import csv
# # import os

# # from streamlit_cookies_manager import CookieManager

# # import time
# # from datetime import date
# # import logging
# # logging.basicConfig(level=logging.INFO)

# # import gspread
# # from oauth2client.service_account import ServiceAccountCredentials

# # st.set_page_config(page_title="HealthTech Wayfinder", page_icon="📍", layout="wide")







# # st.markdown("# H1 Heading")
# # st.markdown("## H2 Heading")
# # st.markdown("### H3 Heading")
# # st.markdown("#### H4 Heading")
# # st.markdown("##### H5 Heading")
# # st.markdown("###### H6 Heading")





# # if "worksheet_name" not in st.session_state:
# #     st.session_state["worksheet_name"] = "Sheet1"

# # if "user_note" not in st.session_state:
# #     st.session_state["user_note"] = ""

# # # Define the Google Sheets credentials and scope
# # creds_dict = {
# #     "type" : st.secrets["gwf_service_account"]["type"],
# #     "project_id" : st.secrets["gwf_service_account"]["project_id"],
# #     "private_key_id" : st.secrets["gwf_service_account"]["private_key_id"],
# #     "private_key" : st.secrets["gwf_service_account"]["private_key"].replace('\\n', '\n'),  # Fix formatting
# #     "client_email" : st.secrets["gwf_service_account"]["client_email"],
# #     "client_id" : st.secrets["gwf_service_account"]["client_id"],
# #     "auth_uri" : st.secrets["gwf_service_account"]["auth_uri"],
# #     "token_uri" : st.secrets["gwf_service_account"]["token_uri"],
# #     "auth_provider_x509_cert_url" : st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
# #     "client_x509_cert_url" : st.secrets["gwf_service_account"]["client_x509_cert_url"],
# #     "universe_domain": st.secrets["gwf_service_account"]["universe_domain"],
# # }

# # # Google Sheets settings
# # sheet_name = 'Team Scratchpad'
# # users = ["Deb", "Kyle", "Lois", "Ryan"]

# # # Initialize the CookieManager and check its status
# # cookies = CookieManager()

# # if not cookies.ready():
# #     # While cookies are being processed, show a placeholder to avoid the box flickering
# #     st.warning("Loading... please wait while we initialize.")
# #     st.stop()  # Stop the script execution until cookies are ready

# # # Function to get Google Sheets connection
# # def get_google_sheet(sheet_name, worksheet_name):
# #     scope = [
# #         "https://www.googleapis.com/auth/spreadsheets",
# #         "https://www.googleapis.com/auth/drive.metadata.readonly",
# #     ]
# #     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
# #     client = gspread.authorize(creds)
# #     sheet = client.open(sheet_name).worksheet(worksheet_name)
# #     return sheet

# # # Function to read the note from Google Sheets
# # def read_note_from_gsheet(sheet_name, worksheet_name):
# #     sheet = get_google_sheet(sheet_name, worksheet_name)
# #     try:
# #         note = sheet.cell(1, 1).value  # Read the content of cell A1
# #     except:
# #         note = ""
# #     return note

# # # Function to save the note to Google Sheets
# # def save_note_to_gsheet(note, sheet_name, worksheet_name):
# #     sheet = get_google_sheet(sheet_name, worksheet_name)
# #     sheet.update_cell(1, 1, note)  # Save the content to cell A1

# # # Callback function to update the note when user selection changes
# # def update_note():
# #     worksheet_name = worksheet_mapping[st.session_state["selected_user"]]
# #     st.session_state["note"] = read_note_from_gsheet(sheet_name, worksheet_name)

# # # Main app content starts here
# # st.markdown("# Welcome!")

# # # Function to handle logout
# # def log_out():
# #     # Clear session state to log out
# #     for key in list(st.session_state.keys()):
# #         del st.session_state[key]
    
# #     # Clear cookies if used for login
# #     if "logged_in" in cookies:
# #         cookies["logged_in"] = None  # Clear the logged_in cookie by setting it to None
# #         cookies.save()  # Save changes to the browser

# #     # Redirect to the main URL of your app
# #     st.markdown('<meta http-equiv="refresh" content="0; url=https://healthtech-wayfinder.streamlit.app/">', unsafe_allow_html=True)

# # # Layout
# # col1, col2, col3 = st.columns([2, 2, 1])

# # with col1:
# #     st.markdown('<h1 style="font-size:30px;">Observation Tools</h1>', unsafe_allow_html=True)
# #     with st.container():
# #         if st.button("🏥 Record a New Case"):
# #             switch_page("Case_Logger")
        
# #         if st.button("🔍 Record a New Observation"):
# #             switch_page("Observation_Logger")
    
# #         if st.button("❓ Chat with Observations"):
# #             switch_page("Observation_Investigator")
    
# #         if st.button("📒 View Observation, Case, & Need Logs"):
# #             switch_page("Cases_&_Observations_Dataset")
            
# #         if st.button("📊 View Glossary"):
# #             switch_page("Glossary")

# # with col2:
# #     st.markdown('<h1 style="font-size:30px;">Need Statement Tools</h1>', unsafe_allow_html=True)
# #     with st.container():
# #         if st.button(":pencil2: Create a Need Statement"):
# #             switch_page("Need_Statement_Logger")

# #         if st.button(":pencil: Edit a Need Statement"):
# #             switch_page("Need_Statement_Editor")

# # with col3:
# #     st.markdown('<h1 style="font-size:30px;">Notes</h1>', unsafe_allow_html=True)
    
# #     worksheet_mapping = {
# #         "Deb": "Sheet1",
# #         "Kyle": "Sheet2",
# #         "Lois": "Sheet3",
# #         "Ryan": "Sheet4"
# #     }

# #     # User selection dropdown
# #     if "selected_user" not in st.session_state:
# #         st.session_state["selected_user"] = users[0]
    
# #     st.selectbox(
# #         "Select User", 
# #         users, 
# #         key="selected_user", 
# #         on_change=update_note
# #     )

# #     # Initialize the note if not set
# #     if "note" not in st.session_state:
# #         update_note()

# #     # Display the text area for notes
# #     user_note = st.text_area("Add Notes", value=st.session_state["note"], height=300)

# #     # Save the note when the button is pressed
# #     if st.button("Save Note"):
# #         worksheet_name = worksheet_mapping[st.session_state["selected_user"]]
# #         st.session_state["note"] = user_note  # Update session state
# #         save_note_to_gsheet(user_note, sheet_name, worksheet_name)
# #         st.success(f"Note updated!")

# # st.markdown("---")



















# # # import time
# # # import streamlit as st
# # # from datetime import date
# # # import logging
# # # logging.basicConfig(level=logging.INFO)

# # # import gspread
# # # from oauth2client.service_account import ServiceAccountCredentials

# # # # Define the Google Sheets credentials and scope
# # # creds_dict = {
# # #     "type" : st.secrets["gwf_service_account"]["type"],
# # #     "project_id" : st.secrets["gwf_service_account"]["project_id"],
# # #     "private_key_id" : st.secrets["gwf_service_account"]["private_key_id"],
# # #     "private_key" : st.secrets["gwf_service_account"]["private_key"].replace('\\n', '\n'),  # Fix formatting
# # #     "client_email" : st.secrets["gwf_service_account"]["client_email"],
# # #     "client_id" : st.secrets["gwf_service_account"]["client_id"],
# # #     "auth_uri" : st.secrets["gwf_service_account"]["auth_uri"],
# # #     "token_uri" : st.secrets["gwf_service_account"]["token_uri"],
# # #     "auth_provider_x509_cert_url" : st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
# # #     "client_x509_cert_url" : st.secrets["gwf_service_account"]["client_x509_cert_url"],
# # #     "universe_domain": st.secrets["gwf_service_account"]["universe_domain"],
# # # }

# # # # Google Sheets settings
# # # sheet_name = 'Team Scratchpad'
# # # users = ["Deb", "Kyle", "Lois", "Ryan"]

# # # # Function to get Google Sheets connection
# # # def get_google_sheet(sheet_name, worksheet_name):
# # #     scope = [
# # #         "https://www.googleapis.com/auth/spreadsheets",
# # #         "https://www.googleapis.com/auth/drive.metadata.readonly",
# # #     ]
# # #     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
# # #     client = gspread.authorize(creds)
# # #     sheet = client.open(sheet_name).worksheet(worksheet_name)
# # #     return sheet

# # # # Function to read the note from Google Sheets
# # # def read_note_from_gsheet(sheet_name, worksheet_name):
# # #     sheet = get_google_sheet(sheet_name, worksheet_name)
# # #     try:
# # #         note = sheet.cell(1, 1).value  # Read the content of cell A1
# # #     except:
# # #         note = ""
# # #     return note

# # # # Function to save the note to Google Sheets
# # # def save_note_to_gsheet(note, sheet_name, worksheet_name):
# # #     sheet = get_google_sheet(sheet_name, worksheet_name)
# # #     sheet.update_cell(1, 1, note)  # Save the content to cell A1

# # # # Callback function to update the note when user selection changes
# # # def update_note():
# # #     worksheet_name = worksheet_mapping[st.session_state["selected_user"]]
# # #     st.session_state["note"] = read_note_from_gsheet(sheet_name, worksheet_name)

# # # # Streamlit app layout
# # # st.title("Scratchpad 📝")

# # # # Map selected user to worksheet
# # # worksheet_mapping = {
# # #     "Deb": "Sheet1",
# # #     "Kyle": "Sheet2",
# # #     "Lois": "Sheet3",
# # #     "Ryan": "Sheet4"
# # # }

# # # # Dropdown for selecting a user with on_change callback to update note
# # # if "selected_user" not in st.session_state:
# # #     st.session_state["selected_user"] = users[0]  # Default to the first user

# # # st.selectbox(
# # #     "Select user", 
# # #     users, 
# # #     key="selected_user", 
# # #     on_change=update_note
# # # )

# # # # Initialize session state for note if not already set
# # # if "note" not in st.session_state:
# # #     update_note()

# # # # Display a text area for the user to write their note, leveraging session state
# # # user_note = st.text_area("Your Note", value=st.session_state["note"], height=300)

# # # # Save the note when the button is pressed
# # # if st.button("Save Note"):
# # #     worksheet_name = worksheet_mapping[st.session_state["selected_user"]]
# # #     st.session_state["note"] = user_note  # Update session state
# # #     save_note_to_gsheet(user_note, sheet_name, worksheet_name)
# # #     st.success(f"{st.session_state['selected_user']}'s note has been saved successfully!")

# # # # Check if the refresh button is pressed
# # # if st.button("Refresh Note"):
# # #     worksheet_name = worksheet_mapping[st.session_state["selected_user"]]
# # #     st.session_state["note"] = read_note_from_gsheet(sheet_name, worksheet_name)
# # #     st.success(f"{st.session_state['selected_user']}'s note has been refreshed!")


# # # import time
# # # import streamlit as st
# # # from datetime import date
# # # import logging
# # # logging.basicConfig(level=logging.INFO)

# # # import gspread
# # # from oauth2client.service_account import ServiceAccountCredentials

# # # # Define the Google Sheets credentials and scope
# # # creds_dict = {
# # #     "type" : st.secrets["gwf_service_account"]["type"],
# # #     "project_id" : st.secrets["gwf_service_account"]["project_id"],
# # #     "private_key_id" : st.secrets["gwf_service_account"]["private_key_id"],
# # #     "private_key" : st.secrets["gwf_service_account"]["private_key"].replace('\\n', '\n'),  # Fix formatting
# # #     "client_email" : st.secrets["gwf_service_account"]["client_email"],
# # #     "client_id" : st.secrets["gwf_service_account"]["client_id"],
# # #     "auth_uri" : st.secrets["gwf_service_account"]["auth_uri"],
# # #     "token_uri" : st.secrets["gwf_service_account"]["token_uri"],
# # #     "auth_provider_x509_cert_url" : st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
# # #     "client_x509_cert_url" : st.secrets["gwf_service_account"]["client_x509_cert_url"],
# # #     "universe_domain": st.secrets["gwf_service_account"]["universe_domain"],
# # # }

# # # # Google Sheets settings
# # # sheet_name = 'Team Scratchpad'
# # # users = ["Deb", "Kyle", "Lois", "Ryan"]


# # # # Function to get Google Sheets connection
# # # def get_google_sheet(sheet_name, worksheet_name):
# # #     scope = [
# # #         "https://www.googleapis.com/auth/spreadsheets",
# # #         "https://www.googleapis.com/auth/drive.metadata.readonly",
# # #     ]
# # #     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
# # #     client = gspread.authorize(creds)
# # #     sheet = client.open(sheet_name).worksheet(worksheet_name)
# # #     return sheet

# # # # Function to read the note from Google Sheets
# # # def read_note_from_gsheet(sheet_name, worksheet_name):
# # #     sheet = get_google_sheet(sheet_name, worksheet_name)
# # #     try:
# # #         note = sheet.cell(1, 1).value  # Read the content of cell A1
# # #     except:
# # #         note = ""
# # #     return note

# # # # Function to save the note to Google Sheets
# # # def save_note_to_gsheet(note, sheet_name, worksheet_name):
# # #     sheet = get_google_sheet(sheet_name, worksheet_name)
# # #     sheet.update_cell(1, 1, note)  # Save the content to cell A1





# # # # Streamlit app layout
# # # st.title("Scratchpad 📝")


# # # # Dropdown for selecting a user
# # # selected_user = st.selectbox("Select user", users)

# # # # Map selected user to worksheet
# # # worksheet_mapping = {
# # #     "Deb": "Sheet1",
# # #     "Kyle": "Sheet2",
# # #     "Lois": "Sheet3",
# # #     "Ryan": "Sheet4"
# # # }
# # # worksheet_name = worksheet_mapping[selected_user]

# # # # Initialize session state if it doesn't exist
# # # if "note" not in st.session_state:
# # #     st.session_state["note"] = read_note_from_gsheet(sheet_name, worksheet_name)


# # # # Check if the refresh button is pressed
# # # if st.button("Refresh Note"):
# # #     # Reload the note from Google Sheets
# # #     st.session_state["note"] = read_note_from_gsheet(sheet_name, worksheet_name)
# # #     # st.success("Refreshed!")

# # # # Display a text area for the user to write their note, leveraging session state
# # # user_note = st.text_area("Your Note", value=st.session_state["note"], height=300)

# # # # Save the note when the button is pressed
# # # if st.button("Save Note"):
# # #     st.session_state["note"] = user_note  # Update session state
# # #     save_note_to_gsheet(user_note, sheet_name, worksheet_name)
# # #     st.success(f"{selected_user}'s note has been saved successfully!")










# # # import time
# # # import streamlit as st
# # # from streamlit_extras.switch_page_button import switch_page
# # # from datetime import date
# # # import logging
# # # logging.basicConfig(level=logging.INFO)

# # # import gspread
# # # from oauth2client.service_account import ServiceAccountCredentials


# # # creds_dict = {
# # #     "type" : st.secrets["gwf_service_account"]["type"],
# # #     "project_id" : st.secrets["gwf_service_account"]["project_id"],
# # #     "private_key_id" : st.secrets["gwf_service_account"]["private_key_id"],
# # #     "private_key" : st.secrets["gwf_service_account"]["private_key"].replace('\\n', '\n'),  # Ensure newlines
# # #     "client_email" : st.secrets["gwf_service_account"]["client_email"],
# # #     "client_id" : st.secrets["gwf_service_account"]["client_id"],
# # #     "auth_uri" : st.secrets["gwf_service_account"]["auth_uri"],
# # #     "token_uri" : st.secrets["gwf_service_account"]["token_uri"],
# # #     "auth_provider_x509_cert_url" : st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
# # #     "client_x509_cert_url" : st.secrets["gwf_service_account"]["client_x509_cert_url"],
# # #     "universe_domain": st.secrets["gwf_service_account"]["universe_domain"],
# # # }

# # # # Team Scratchpad
# # # sheet_name = 'Team Scratchpad'
# # # worksheet_name = 'Sheet1'
# # # # List of users (you can replace or load these dynamically)
# # # users = ["Deb", "Kyle", "Lois", "Ryan"]

# # # # Function to get Google Sheets connection
# # # def get_google_sheet(sheet_name, worksheet_name):
# # #     scope = [
# # #         "https://www.googleapis.com/auth/spreadsheets",
# # #         "https://www.googleapis.com/auth/drive.metadata.readonly",
# # #     ]
# # #     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
# # #     client = gspread.authorize(creds)
# # #     sheet = client.open(sheet_name).worksheet(worksheet_name)
# # #     return sheet

# # # # Function to read the note from Google Sheets
# # # def read_note_from_gsheet(sheet_name, worksheet_name):
# # #     sheet = get_google_sheet(sheet_name, worksheet_name)
# # #     try:
# # #         note = sheet.cell(1, 1).value  # Read the content of cell A1
# # #     except:
# # #         note = ""
# # #     return note

# # # # Function to save the note to Google Sheets
# # # def save_note_to_gsheet(note, sheet_name, worksheet_name):
# # #     sheet = get_google_sheet(sheet_name, worksheet_name)
# # #     sheet.update_cell(1, 1, note)  # Save the content to cell A1

# # # # Streamlit app layout
# # # st.title("Scratchpad 📝")

# # # # Dropdown for selecting a user
# # # selected_user = st.selectbox("Select user", users)

# # # # Update the worksheet name based on the selected user
# # # if selected_user == "Deb":
# # #     worksheet_name = 'Sheet1'
# # # elif selected_user == "Kyle":
# # #     worksheet_name = 'Sheet2'  # Fixed typo here
# # # elif selected_user == "Lois":
# # #     worksheet_name = 'Sheet3'
# # # elif selected_user == "Ryan":
# # #     worksheet_name = 'Sheet4'

# # # # Load the note from Google Sheets
# # # note = read_note_from_gsheet(sheet_name, worksheet_name)

# # # # Check if the refresh button is pressed
# # # if st.button("Refresh Note"):
# # #     note = read_note_from_gsheet(sheet_name, worksheet_name)
# # #     st.success(f"{selected_user}'s note has been refreshed!")

# # # # Display a text area for the user to write their note
# # # user_note = st.text_area("Your Note", value=note, height=300)

# # # # Save the note when the button is pressed
# # # if st.button("Save Note"):
# # #     save_note_to_gsheet(user_note, sheet_name, worksheet_name)
# # #     st.success(f"{selected_user}'s note has been saved successfully!")









# # # import time
# # # import streamlit as st
# # # from streamlit_extras.switch_page_button import switch_page
# # # from datetime import date
# # # import logging
# # # logging.basicConfig(level=logging.INFO)

# # # import gspread
# # # from oauth2client.service_account import ServiceAccountCredentials


# # # from pydantic import BaseModel, Field
# # # from typing import Optional
# # # from datetime import date, datetime

# # # import json
# # # import os
# # # import csv

# # # creds_dict = {
# # #     "type" : st.secrets["gwf_service_account"]["type"],
# # #     "project_id" : st.secrets["gwf_service_account"]["project_id"],
# # #     "private_key_id" : st.secrets["gwf_service_account"]["private_key_id"],
# # #     "private_key" : st.secrets["gwf_service_account"]["private_key"],
# # #     "client_email" : st.secrets["gwf_service_account"]["client_email"],
# # #     "client_id" : st.secrets["gwf_service_account"]["client_id"],
# # #     "auth_uri" : st.secrets["gwf_service_account"]["auth_uri"],
# # #     "token_uri" : st.secrets["gwf_service_account"]["token_uri"],
# # #     "auth_provider_x509_cert_url" : st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
# # #     "client_x509_cert_url" : st.secrets["gwf_service_account"]["client_x509_cert_url"],
# # #     "universe_domain": st.secrets["gwf_service_account"]["universe_domain"],
# # # }


# # # # Team Scratchpad
# # # # open google sheets to the notepad file
# # # # import any notes from the cell
# # # #  if notes, populate the widget
# # # #  if no notes, leave blank
# # # #  user can edit
# # # #  if user clicks update, they save their notes

# # # sheet_name = 'Team Scratchpad'
# # # worksheet_name = 'Sheet1'
# # # # List of users (you can replace or load these dynamically)
# # # users = ["Deb", "Kyle", "Lois", "Ryan"]


# # # def get_google_sheet(sheet_name, worksheet_name):
# # #     scope = [
# # #         "https://www.googleapis.com/auth/spreadsheets",
# # #         "https://www.googleapis.com/auth/drive.metadata.readonly",
# # #     ]
# # #     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
# # #     client = gspread.authorize(creds)
# # #     sheet = client.open(sheet_name).worksheet(worksheet_name)
# # #     return sheet



# # # # Function to read the note from Google Sheets
# # # def read_note_from_gsheet(sheet_name, worksheet_name):
# # #     sheet = get_google_sheet(sheet_name, worksheet_name)
# # #     try:
# # #         note = sheet.cell(1, 1).value  # Read the content of cell A1
# # #     except:
# # #         note = ""
# # #     return note

# # # # Function to save the note to Google Sheets
# # # def save_note_to_gsheet(note, sheet_name, worksheet_name):
# # #     sheet = get_google_sheet(sheet_name, worksheet_name)
# # #     sheet.update_cell(1, 1, note)  # Save the content to cell A1



# # # # Streamlit app layout
# # # st.title("Scratchpad 📝")

# # # # Dropdown for selecting a user
# # # selected_user = st.selectbox("Select user", users)


# # # if selected_user:

# # #     if selected_user == "Deb":
# # #         worksheet_name = 'Sheet1'
# # #     elif selected_user == "Kyle":
# # #         worksheet_name = 'Sheet2'
# # #     elif selected_user == "Lois":
# # #         worksheet_name = 'Sheet3'
# # #     elif selected_user == "Ryan":
# # #         worksheet_name = 'Sheet4'

# # #     # Load the note from Google Sheets
# # #     note = read_note_from_gsheet(sheet_name, worksheet_name)


# # # # Check if the refresh button is pressed
# # # if st.button("Refresh Note"):
# # #     # Reload the note from Google Sheets if "Refresh" is clicked
# # #     note = read_note_from_gsheet(sheet_name, worksheet_name)
# # #     # st.success(f"{selected_user}'s note has been refreshed!")
# # # else:
# # #     # Load the note from the selected user's worksheet (initial load)
# # #     note = read_note_from_gsheet(sheet_name, worksheet_name)


# # # # Display a text area for the user to write their note
# # # user_note = st.text_area("Your Note", value=note, height=300)

# # # # Save the note when the button is pressed
# # # if st.button("Save Note"):
# # #     save_note_to_gsheet(user_note, sheet_name, worksheet_name)
# # #     st.success("Your note has been saved successfully!")

# # # # Provide feedback that the note is auto-loaded from Google Sheets on app load
# # # # st.caption("This notepad autosaves your note to Google Sheets and reloads it when you reopen the app.")


