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

# I propose copying the code over form the Add Observation page, but removing the AI components -- only entering info from the user right to the log



import time
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from datetime import date


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

st.set_page_config(page_title="Create a New Need Statement", page_icon=":pencil:")

st.markdown("# Create a New Need Statement")


need_csv = "need.csv"
OPENAI_API_KEY = st.secrets["openai_key"]

# Access the credentials from Streamlit secrets
#test
creds_dict = {
    "type" : st.secrets["gcp_service_account"]["type"],
    "project_id" : st.secrets["gcp_service_account"]["project_id"],
    "private_key_id" : st.secrets["gcp_service_account"]["private_key_id"],
    "private_key" : st.secrets["gcp_service_account"]["private_key"],
    "client_email" : st.secrets["gcp_service_account"]["client_email"],
    "client_id" : st.secrets["gcp_service_account"]["client_id"],
    "auth_uri" : st.secrets["gcp_service_account"]["auth_uri"],
    "token_uri" : st.secrets["gcp_service_account"]["token_uri"],
    "auth_provider_x509_cert_url" : st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url" : st.secrets["gcp_service_account"]["client_x509_cert_url"],
    "universe_domain": st.secrets["gcp_service_account"]["universe_domain"],
}

# Recorded variables:
# need_date
# need_ID
# observation_ID
# need_statement
# problem
# population
# outcome

# variables recorded: need_ID, need_date, need_statement, problem, population, outcome, observation_ID,

if 'need_statement' not in st.session_state:
    st.session_state['need_statement'] = ""

# if 'observation_ID_list' not in st.session_state:
#     st.session_state['observation_ID_list'] = ""


# if 'need_ID' not in st.session_state:
#     st.session_state['need_ID'] = ""

if 'problem' not in st.session_state:
    st.session_state['problem'] = ""

if 'population' not in st.session_state:
    st.session_state['population'] = ""

if 'outcome' not in st.session_state:
    st.session_state['outcome'] = ""

# if 'observation_ID' not in st.session_state:
#     st.session_state['observation_ID'] = ""

if 'notes' not in st.session_state:
    st.session_state['notes'] = ""

if 'result' not in st.session_state:
    st.session_state['result'] = ""
    
# if 'need_date' not in st.session_state:
#     st.session_state['need_date'] = date.today()

if 'rerun' not in st.session_state:
    st.session_state['rerun'] = False

if 'notes_input' not in st.session_state:
    st.session_state['notes_input'] = ""

#

# if not os.path.exists(need_csv):
#     need_keys = list(needRecord.__fields__.keys())
#     need_keys = ['need_ID', 'need_date', 'need_summary', 'observation_ID', 'location', 'need_statement'] + need_keys        
#     csv_file = open(need_csv, "w")
#     csv_writer = csv.writer(csv_file, delimiter=";")
#     csv_writer.writerow(need_keys)


def addToGoogleSheets(need_dict):
    try:
        scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        need_sheet = client.open("BioDesign Observation Record").worksheet('Need_Log')

        headers = need_sheet.row_values(1)

        # Prepare the row data matching the headers
        row_to_append = []
        for header in headers:
            if header in need_dict:
                value = need_dict[header]
                if value is None:
                    row_to_append.append("")
                else:
                    row_to_append.append(str(need_dict[header]))
            else:
                row_to_append.append("")  # Leave cell blank if header not in dictionary

        # Append the row to the sheet
        need_sheet.append_row(row_to_append)
        return True
    except Exception as e:
        print("Error adding to Google Sheets: ", e)
        return False
    # variables recorded: 'need_ID', 'need_date', 'need_statement', 'problem', 'population', 'outcome', 'observation_ID'


# put in correct format & call function to upload to google sheets
def recordNeed(need_ID, need_date, need_statement, problem, population, outcome, observation_ID, notes):
    
     all_need_keys = ['need_ID', 'need_date', 'need_statement', 'problem', 'population', 'outcome', 'observation_ID', 'notes'] # + need_keys
     need_values = [need_ID, need_date, need_statement, problem, population, outcome, observation_ID, notes] # + [parsed_need[key] for key in need_keys]
     need_dict = dict(zip(all_need_keys, need_values))
#     csv_file = open(need_csv, "a")
#     csv_writer = csv.writer(csv_file, delimiter=";")
#     csv_writer.writerow(need_values)

     status = addToGoogleSheets(need_dict)

     return status


# reset textboxes, except for the date
def clear_need():
    st.session_state.need_input = ''
    #st.session_state.input1 = ''
    st.session_state.notes_input = ''
    st.session_state.problem_input = ''
    st.session_state.population_input = ''
    st.session_state.outcome_input = ''
    
    # # if 'need_summary' in st.session_state:
    # #     st.session_state['need_summary'] = ""
    # if 'result' in st.session_state:
    #     st.session_state['result'] = ""
   
    # if 'problem' in st.session_state:
    #     st.session_state['problem'] = ""

    # if 'population' in st.session_state:
    #     st.session_state['population'] = ""

    # if 'outcome' in st.session_state:
    #     st.session_state['outcome'] = ""

    # if 'Notes' in st.session_state:
    #     st.session_state['Notes'] = ""
    update_need_ID()
    

# Initialize or retrieve the clear_need counters dictionary from session state
if 'need_counters' not in st.session_state:
    st.session_state['need_counters'] = {}

# get observation ID options
# def getObservationIDs():
#     # google sheets conection here
#     scope = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.metadata.readonly"
#         ]
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#     client = gspread.authorize(creds)
#     observation_sheet = client.open("BioDesign Observation Record").worksheet('Sheet1')
#     # Read the data from the Google Sheet into a DataFrame
#     # df = observation_sheet.col_values(7)     
#     # # Convert the desired column to a list
#     # observation_ID_list = df['observation_ID'].tolist()
#     observation_ID_list = observation_sheet.col_values(1)


def getObservationIDs():
    # Define the scope for the Google Sheets API
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
    ]
    
    # Authenticate with Google Sheets using the credentials dictionary
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # Open the Google Sheet and select the worksheet
    observation_sheet = client.open("BioDesign Observation Record").worksheet('Sheet1')
    
    # Fetch all the values in the first column (col_values returns a list)
    observation_ID_list = observation_sheet.col_values(1)  # Fetch column 1
    
    # Remove the header by slicing the list (if it exists)
    if observation_ID_list:
        observation_ID_list = observation_ID_list[1:]
    
    return observation_ID_list


# Function to generate need ID with the format NSYYMMDDxxxx
def generate_need_ID(need_date, counter):
    return f"NS{need_date.strftime('%y%m%d')}{counter:04d}"

# Function to update need ID when the date changes
def update_need_ID():
    obs_date_str = st.session_state['need_date'].strftime('%y%m%d')

    # get all need ids from the sheets and update the counter
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    need_sheet = client.open("BioDesign Observation Record").worksheet('Need_Log')
    column_values = need_sheet.col_values(1) 

    # find all need ids with the same date
    obs_date_ids = [obs_id for obs_id in column_values if obs_id.startswith(f"NS{obs_date_str}")] #how to make this work
    obs_date_ids.sort()

    # get the counter from the last need id
    if len(obs_date_ids) > 0:
        counter = int(obs_date_ids[-1][-4:])+1
    else:
        counter = 1

    st.session_state['need_ID'] = generate_need_ID(st.session_state['need_date'], counter)

# getObservationIDs()
# Fetch the observation IDs from the Google Sheet
observation_ID_list = getObservationIDs()



# Use columns to place need_date, need_ID, and observation_ID side by side
col1, col2, col3 = st.columns(3)

with col1:
    # st calendar for date input with a callback to update the need_ID
    st.date_input("Need Date", date.today(), on_change=update_need_ID, key="need_date")

with col2:
    # Ensure the need ID is set the first time the script runs
    if 'need_ID' not in st.session_state:
        update_need_ID()

    # Display the need ID
    st.text_input("Need ID:", value=st.session_state['need_ID'], disabled=True)

with col3:
    # Display observation_ID options 
    observation_ID = st.multiselect("Relevant Observations (multi-select):", observation_ID_list)



############

# # Function to generate need ID with the format OBYYYYMMDDxxxx
# def generate_need_ID(need_date, counter):
#     return f"OB{need_date.strftime('%y%m%d')}{counter:04d}"

# # Initialize or retrieve need ID counter from session state
# if 'need_ID_counter' not in st.session_state:
#     st.session_state['need_ID_counter'] = 1

# # Function to update need ID when the date changes
# def update_need_ID():
#     st.session_state['need_ID'] = generate_need_ID(st.session_state['need_date'], st.session_state['need_ID_counter'])

# # st calendar for date input with a callback to update the need_ID
# st.session_state['need_date'] = st.date_input("Observation Date", date.today(), on_change=update_need_ID)

# # Initialize need_ID based on the observation date and counter
# st.session_state['need_ID'] = st.text_input("Observation ID:", value=st.session_state['need_ID'], disabled=True)

##########

#new_need_ID = st.need_date().strftime("%Y%m%d")+"%03d"%need_ID_counter
#st.session_state['need_ID'] = st.text_input("Observation ID:", value=new_need_ID)

#########

# Textbox for name input
#observation_ID = st.selectbox("observation_ID", ["Ana", "Bridget"])

# ######

# # Text area for observation input
# st.session_state['observation'] = st.text_area("Add Your Observation", value=st.session_state['observation'], placeholder="Enter your observation...", height=200)

# ######


# Initialize the observation text in session state if it doesn't exist

if "need_statement" not in st.session_state:
    st.session_state["need_statement"] = ""

# Function to clear the text area
def clear_text():
  #  st.session_state["need_statement"] = ""
    st.session_state.need_statement = ''


#st.markdown("---")

# Observation Text Area
##

#observation_text = st.text_area("Observation", value=st.session_state["observation"], height=200, key="observation")

# Add Your need Text with larger font size
col1, col2, col3 = st.columns(3)

with col1:
    problem_input = st.text_input(label="Problem:")

with col2:
    population_input = st.text_input(label="Population:")

with col3:
    outcome_input = st.text_input(label="Outcome:")

st.markdown("<h4 style='font-size:20px;'>Need Statement:</h4>", unsafe_allow_html=True)

# Button for voice input (currently as a placeholder)
#if st.button("🎤 Record need (Coming Soon)"):
 #   st.info("Voice recording feature coming soon!")

# need Text Area
#st.session_state['need_statement'] = st.text_area("need:", value=st.session_state["need_statement"], height=100)

# Function to clear form inputs
# def clear_form():
#     st.session_state.input1 = ''

# Function to handle form submission
def submit_form():
    # Form submission logic
    if need_input:
            st.session_state["need_statement"] = st.session_state["need_input"]

           # need_statement = need_input
            problem = problem_input
            population = population_input
            outcome = outcome_input
            notes = notes_input
            # update_need_ID()
            st.write("Need statement recorded!")
            # st.write(f'Relevant Observations: {observation_ID}')
            # st.write(f'Need ID: {st.session_state['need_ID']}')
            # st.write(f'Problem: {problem}')
            # st.write(f'Population: {population}')
            # st.write(f'Outcome: {outcome}')
            # st.write(f'Notes: {notes}')
            recordNeed(st.session_state['need_ID'], st.session_state['need_date'], need_statement, problem, population, outcome, observation_ID, notes)
    clear_need()



with st.form(key="my_form"):
    need_input = st.text_input(label="There is a need for...")
    notes_input = st.text_input(label="Relevant Notes:")
    #notes_input = st.text_area("Relevant Notes:", value=st.session_state["notes_input"], height=100)
    submit_button = st.form_submit_button(label="Submit")
    submitted = st.form_submit_button("Submit", on_click=submit_form)

    # st.button("Clear need", on_click=clear_text)

    # Button to Clear the need Text Area
    # col21, col22, col23 = st.columns(3)  # Adjust column widths as needed
    
    # with col23:
    

    if submit_button:
        if need_input:
            st.session_state["need_statement"] = st.session_state["need_input"]

            # need_statement = need_input
            problem = problem_input
            population = population_input
            outcome = outcome_input
            notes = notes_input
            # update_need_ID()
            st.write("Need statement recorded!")
            # st.write(f'Relevant Observations: {observation_ID}')
            # st.write(f'Need ID: {st.session_state['need_ID']}')
            # st.write(f'Problem: {problem}')
            # st.write(f'Population: {population}')
            # st.write(f'Outcome: {outcome}')
            # st.write(f'Notes: {notes}')
            recordNeed(st.session_state['need_ID'], st.session_state['need_date'], need_statement, problem, population, outcome, observation_ID, notes)
            clear_need()

            #TO DO: clear text boxes after


# Create columns to align the buttons
# col1, col2, col3 = st.columns([2, 2, 2])  # Adjust column widths as needed

with col3:
      # Button to Clear the Observation Text Area
  #  st.button("Clear Observation", on_click=clear_text) 
    # Container for result display
    result_container = st.empty()
    # Use custom CSS for the red button
    # st.markdown("""
    #     <style>
    #     .stButton > button {
    #         background-color: #942124;
    #         color: white;
    #         font-size: 16px;
    #         padding: 10px 20px;
    #         border-radius: 8px;
    #         border: none;
    #     }
    #     .stButton > button:hover {
    #         background-color: darkred;
    #     }
    #     </style>
    #     """, unsafe_allow_html=True)

   
    
    

# #Use columns to place buttons side by side
# col11, col21 = st.columns(2)


#     if st.button("Generate Observation Summary"):
#         st.session_state['need_summary']  = generateneedSummary(st.session_state['observation'])

#     if st.session_state['need_summary'] != "":
#         st.session_state['need_summary'] = st.text_area("Generated Summary (editable):", value=st.session_state['need_summary'], height=50)
    

# with col1:
    # if st.button("Generate need Summary"):
    #     st.session_state['result'] = extractneedFeatures(st.session_state['need_statement'])
    #     st.session_state['need_summary']  = generateneedSummary(st.session_state['need_statement'])
    
# if st.session_state['need_summary'] != "":
#     st.session_state['need_summary'] = st.text_area("need Summary (editable):", value=st.session_state['need_summary'], height=50)

# st.write(f":green[{st.session_state['result']}]")
st.markdown(st.session_state['result'], unsafe_allow_html=True)

if st.session_state['rerun']:
    time.sleep(3)
    #clear_need()
    st.session_state['rerun'] = False
    st.rerun()
    
    ##########

# if st.button("Log need", disabled=st.session_state['need_statement'] == ""):
#     # st.session_state['need_summary']  = generateneedSummary(st.session_state['observation'])
#     st.session_state["error"] = ""

#     if st.session_state['need_statement'] == "":
#         st.session_state["error"] = "Error: Please enter need."
#         st.markdown(
#             f"<span style='color:red;'>{st.session_state['error']}</span>", 
#             unsafe_allow_html=True
#         )
    # elif st.session_state['need_summary'] == "":
    #     st.session_state["error"] = "Error: Please evaluate need."
    #     st.markdown(
    #         f"<span style='color:red;'>{st.session_state['error']}</span>", 
    #         unsafe_allow_html=True
    #     )
    # else:
    #     status = embedneed(observation_ID, st.session_state['need_statement'],  st.session_state['need_summary'], 
    #                         st.session_state['need_date'],
    #                         st.session_state['need_ID'])
        # st.session_state['need_summary'] = st.text_input("Generated Summary (editable):", value=st.session_state['need_summary'])
        # "Generated Summary: "+st.session_state['need_summary']+"\n\n"
        # if status:
        #     st.session_state['result'] = "Need statement added to your team's database."
        #     st.session_state['rerun'] = True
        #     st.rerun()
        # else:
        #     st.session_state['result'] = "Error adding need statement to your team's database. Please try again!"
        # clear_need()

st.markdown("---")

# if st.button("Back to Main Menu"):
#     clear_need()
#     switch_page("main_menu")


# st.markdown("---")
# Apply custom CSS to make the button blue
st.markdown("""
    <style>
    div.stButton > button {
        background-color: #365980;
        color: white;
        font-size: 16px;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
    }
    div.stButton > button:hover {
        background-color: #2c4a70;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)



# Create a button using Streamlit's native functionality
if st.button("Back to Main Menu"):
    switch_page("main_menu")


# REVIEW BELOW FOR MAKING LIST OF OBSERVATIONS


def update_observation_id():
    obs_date_str = st.session_state['observation_date'].strftime('%y%m%d')

    # get all observation ids from the sheets and update the counter
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    observation_sheet = client.open("BioDesign Observation Record").worksheet('Need_Log')
    column_values = observation_sheet.col_values(1) 

    # find all observation ids with the same date
    obs_date_ids = [obs_id for obs_id in column_values if obs_id.startswith(f"OB{obs_date_str}")]
    obs_date_ids.sort()

    # get the counter from the last observation id
    if len(obs_date_ids) > 0:
        counter = int(obs_date_ids[-1][-4:])+1
    else:
        counter = 1
    
    # # Check if the date is already in the dictionary
    # if obs_date_str in st.session_state['observation_counters']:
    #     # Increment the counter for this date
    #     st.session_state['observation_counters'][obs_date_str] += 1
    # else:
    #     # Initialize the counter to 1 for a new date
    #     st.session_state['observation_counters'][obs_date_str] = 1
    
    # Generate the observation ID using the updated counter
    # counter = st.session_state['observation_counters'][obs_date_str]

    # st.session_state['observation_id'] = generate_observation_id(st.session_state['observation_date'], counter)

def getObservationIDs():
    #put google sheets conection here

    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    observation_sheet = client.open("BioDesign Observation Record").worksheet('Need_Log')
    observation_ID_list = observation_sheet.col_values(1) 
    
    # Read the data from the Google Sheet into a DataFrame
    df = observation_sheet.col_values(1)     
    # df = conn.read()

    # Convert the desired column to a list
    column_list = df['column_name'].tolist()


