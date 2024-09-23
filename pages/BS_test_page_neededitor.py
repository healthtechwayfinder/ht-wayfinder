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
    # sheet = get_google_sheet("2024 Healthtech Identify Log", "Need Statement Log")
    # need_data = need_df
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



def display_selected_observation(selected_obs_id):
    obs_log = get_google_sheet("2024 Healthtech Identify Log", "Observation Log")
    df = pd.DataFrame(obs_log.get_all_records())

    # Get the observation description based on the selected Observation ID
    if selected_obs_id:
        selected_observation = df[df['Observation ID'] == selected_obs_id]
        if not selected_observation.empty:
            observation_description = selected_observation.iloc[0]['Observation Description']
            st.markdown(f"### {selected_obs_id} Description:\n{observation_description}")
            # st.markdown(f"### Selected Observation Description:\n{observation_description}")
        else:
            st.info("No description available for this observation.")
    else:
        st.info("Please select an observation.")


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
    # obs_log = get_google_sheet("2024 Healthtech Identify Log", "Observation Log")
    # df = pd.DataFrame(obs_log.get_all_records())

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
        st.write(need_details)




        # need_details = fetch_need_details(need_to_edit)
        if need_details:
           
            
            # amend code here for observation ID handling ///////////////////////////
            
            
            # Fetch observation_IDs associated with the selected need_ID
            matching_row = need_statement_df[need_statement_df['need_ID'] == st.session_state['selected_need_ID']]
            
            if not matching_row.empty:
                # Get the observation_IDs as a string and convert it into a list
                observation_ids_str = matching_row.iloc[0]['observation_ID']
                try:
                    # Safely convert the string to a list using ast.literal_eval
                    observation_ids = ast.literal_eval(observation_ids_str)
                    observation_ids = [obs_id.strip() for obs_id in observation_ids]  # Strip whitespace from each ID
                except (ValueError, SyntaxError):
                    st.error("Error parsing observation IDs. Please check the format in the Google Sheet.")
                    st.stop()
        
                # Find the Observation Titles corresponding to each observation_ID
                observation_ids_with_title = []
                for obs_id in observation_ids:
                    obs_row = observation_log_df[observation_log_df['Observation ID'] == obs_id]
                    if not obs_row.empty:
                        observation_title = obs_row.iloc[0]['Observation Title']
                        observation_ids_with_title.append(f"{obs_id} - {observation_title}")
                
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
                # need_details = {"observation_ID": selected_observation_ids}
                need_details["observation_ID"] = selected_observation_ids

                # st.write("Selected Observation IDs:", need_details.get("observation_ID"))
        
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

# # # OLD OLD OLD OLD OLD OLD OLD OLD ////////// make a list of potential observation IDs
# # def getObservationIDs():
# #     # Define the scope for the Google Sheets API
# #     scope = [
# #         "https://www.googleapis.com/auth/spreadsheets",
# #         "https://www.googleapis.com/auth/drive.metadata.readonly"
# #     ]
    
# #     # Authenticate with Google Sheets using the credentials dictionary
# #     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
# #     client = gspread.authorize(creds)
    
# #     # Open the Google Sheet and select the worksheet
# #     observation_sheet = client.open("2024 Healthtech Identify Log").worksheet('Observation Log')
    
# #     # Fetch all the values in the first column (col_values returns a list)
# #     observation_ID_list = observation_sheet.col_values(1)  # Fetch column 1
    
# #     # Remove the header by slicing the list (if it exists)
# #     if observation_ID_list:
# #         observation_ID_list = observation_ID_list[1:]
    
# #     return observation_ID_list




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



















#/////////////////////////////////////////////////////////////////////////////////////////////////////

# //// PROCESS ////
# 0. brief instructions appear at the top of the page with a link to the uder guide for more info
# 1. select one or more observations (type them in? drop down?)
#     -> summaries of observations are then displayed
# 2. select the date (default to today's date)
# 3. select the author (or NOT???? --  let's think this over)
# 4. enter statement:
#      -> 1st box: enter problem
#      -> 2nd box: enter population
#      -> 3rd box: enter outcome
#      -> 4th box: enter full need statement
#      -> 5th box for notes?
#    -> statement goes to sheet and information is recorded in corresonding columns
# 5. option to enter more statements with a (+) button (with a unique ID for each statement, user doesn't need to see this, honestly)
# 6. statement goes to the google sheet, no AI necessary -- user sees message "Need statement(s) recorded!)
# Other Notes:
# -> code could lay foundation for detecting and sorting problem, population, and solution rather than manual entry
# -> could the observation bot page have a widget in the right-hand sidebar for entering need satements from that page? (in need something comes up from a conversation)





