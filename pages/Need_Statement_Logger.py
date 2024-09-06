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


if 'need_statement' not in st.session_state:
    st.session_state['need_statement'] = ""

# if 'location' not in st.session_state:
#     st.session_state['location'] = ""

if 'result' not in st.session_state:
    st.session_state['result'] = ""

# if 'need_summary' not in st.session_state:
#     st.session_state['need_summary'] = ""

if 'need_date' not in st.session_state:
    st.session_state['need_date'] = date.today()

if 'rerun' not in st.session_state:
    st.session_state['rerun'] = False

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
        need_sheet = client.open("BioDesign Observation Record").Need_Log

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

    # write observation_ID, to csv
    need_keys = list(needRecord.__fields__.keys())
    all_need_keys = ['observation_ID', 'need_statement', 'need_date', 'need_ID'] + need_keys
    need_values = [observation_ID, need_statement, need_date, need_ID] + [parsed_need[key] for key in need_keys]

    need_dict = dict(zip(all_need_keys, need_values))
    csv_file = open(need_csv, "a")
    csv_writer = csv.writer(csv_file, delimiter=";")
    csv_writer.writerow(need_values)

    status = addToGoogleSheets(need_dict)

    return status


def clear_need():
    if 'need_statement' in st.session_state:
        st.session_state['need_statement'] = ""
    # if 'need_summary' in st.session_state:
    #     st.session_state['need_summary'] = ""
    if 'result' in st.session_state:
        st.session_state['result'] = ""
    update_need_ID()



# Initialize or retrieve the clear_need counters dictionary from session state
if 'need_counters' not in st.session_state:
    st.session_state['need_counters'] = {}

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
    need_sheet = client.open("BioDesign Observation Record").sheet1
    column_values = need_sheet.col_values(1) 

    # find all need ids with the same date
    obs_date_ids = [obs_id for obs_id in column_values if obs_id.startswith(f"OB{obs_date_str}")] #how to make this work
    obs_date_ids.sort()

    # get the counter from the last need id
    if len(obs_date_ids) > 0:
        counter = int(obs_date_ids[-1][-4:])+1
    else:
        counter = 1
    
    # # Check if the date is already in the dictionary
    # if obs_date_str in st.session_state['need_counters']:
    #     # Increment the counter for this date
    #     st.session_state['need_counters'][obs_date_str] += 1
    # else:
    #     # Initialize the counter to 1 for a new date
    #     st.session_state['need_counters'][obs_date_str] = 1
    
    # Generate the need ID using the updated counter
    # counter = st.session_state['need_counters'][obs_date_str]

    st.session_state['need_ID'] = generate_need_ID(st.session_state['need_date'], counter)

# Use columns to place need_date, need_ID, and observation_ID side by side
col1, col2, col3 = st.columns(3)

with col1:
    # st calendar for date input with a callback to update the need_ID
    st.date_input("Need Date", date.today(), on_change=update_need_ID, key="need_date")
    # st.location['location'] = st.text_input("Location:", "")
    # st.session_state['location'] = st.text_input("Location:", value=st.session_state["location"])

with col2:
    # Ensure the need ID is set the first time the script runs
    if 'need_ID' not in st.session_state:
        update_need_ID()

    # Display the need ID
    st.text_input("Need ID:", value=st.session_state['need_ID'], disabled=True)

with col3:
    # Display observation_ID options 
    # need to create a variable that's just an array of all the obervation IDs
    observation_ID = st.multiselect("Relevant Observations (multi-select)", ["Test 1", "Test 2"]) 

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
    st.session_state["need_statement"] = ""

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

with st.form(key="my_form"):
    need_input = st.text_input(label="")
    
    submit_button = st.form_submit_button(label="Submit")
    # Button to Clear the need Text Area
    col21, col22, col23 = st.columns(3)  # Adjust column widths as needed
    
    with col23:
        st.button("Clear need", on_click=clear_text)
    

    if submit_button:
        if text_input:
            need_statement = need_input
            problem = problem_input
            population = populaiton_input
            outcome = outcome_input
            st.write("Need statement recorded!")
            #update so that all variables are saved from text input and then logged



# Create columns to align the buttons
# col1, col2, col3 = st.columns([2, 2, 2])  # Adjust column widths as needed

with col3:
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
    clear_need()
    st.session_state['rerun'] = False
    st.rerun()
    
    ##########

if st.button("Log need", disabled=st.session_state['need_statement'] == ""):
    # st.session_state['need_summary']  = generateneedSummary(st.session_state['observation'])
    st.session_state["error"] = ""

    if st.session_state['need_statement'] == "":
        st.session_state["error"] = "Error: Please enter need."
        st.markdown(
            f"<span style='color:red;'>{st.session_state['error']}</span>", 
            unsafe_allow_html=True
        )
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
        if status:
            st.session_state['result'] = "Need statement added to your team's database."
            st.session_state['rerun'] = True
            st.rerun()
        else:
            st.session_state['result'] = "Error adding need statement to your team's database. Please try again!"
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

















# import os
# import csv
# from datetime import date
# from typing import Optional

# import streamlit as st
# from streamlit_extras.switch_page_button import switch_page

# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
# from pydantic import BaseModel, Field
# from streamlit_extras.switch_page_button import switch_page

# # Lil bit of testing here $$$$$$$$$$$$$$$$$$$$$$

# st.set_page_config(page_title="Log a New Need Statement", page_icon="🔍")

# st.markdown("# Log a New Need Statement")




# # Constants
# observations_csv = "observations.csv"

# # Access GCP credentials from Streamlit secrets
# creds_dict = {
#     key: st.secrets["gcp_service_account"][key]
#     for key in st.secrets["gcp_service_account"]
# }

# # Initialize session state variables
# for key, default in {
#     'need_statement': "",
#     'problem': "",
#     'population': "",
#     'outcome': "",
#     'notes': "",
#     'need_statement_date': date.today(),
#     'rerun': False,
# }.items():
#     if key not in st.session_state:
#         st.session_state[key] = default

# # Define the NeedStatement model
# class NeedStatement(BaseModel):
#     problem: Optional[str] = Field(None, description="Describe the problem.")
#     population: Optional[str] = Field(None, description="Who is affected?")
#     outcome: Optional[str] = Field(None, description="Desired outcome?")
#     full_statement: Optional[str] = Field(None, description="Full need statement.")
#     notes: Optional[str] = Field(None, description="Additional notes.")

# # Create CSV file if it doesn't exist
# if not os.path.exists(observations_csv):
#     statement_keys = ['problem', 'population', 'outcome', 'full_statement', 'notes', 'author', 'statement_date', 'statement_id']
#     with open(observations_csv, "w") as csv_file:
#         csv_writer = csv.writer(csv_file, delimiter=";")
#         csv_writer.writerow(statement_keys)

# # Function to add to Google Sheets
# def addToGoogleSheets(statement_dict):
#     try:
#         scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.metadata.readonly"]
#         creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#         client = gspread.authorize(creds)
#         statement_sheet = client.open("Need Statements Record").sheet1
#         headers = statement_sheet.row_values(1)
#         row_to_append = [str(statement_dict.get(header, "")) for header in headers]
#         statement_sheet.append_row(row_to_append)
#         return True
#     except Exception as e:
#         st.error(f"Error adding to Google Sheets: {str(e)}")
#         return False

# # Function for need statement ID generation and updating
# def generate_statement_id(statement_date, counter):
#     return f"NS{statement_date.strftime('%y%m%d')}{counter:04d}"

# def update_statement_id():
#     stmt_date_str = st.session_state['need_statement_date'].strftime('%y%m%d')
#     scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.metadata.readonly"]
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#     client = gspread.authorize(creds)
#     statement_sheet = client.open("Need Statements Record").sheet1
#     stmt_date_ids = [stmt_id for stmt_id in statement_sheet.col_values(1) if stmt_id.startswith(f"NS{stmt_date_str}")]
#     counter = int(stmt_date_ids[-1][-4:]) + 1 if stmt_date_ids else 1
#     st.session_state['statement_id'] = generate_statement_id(st.session_state['need_statement_date'], counter)

# # Streamlit UI components
# col1, col2 = st.columns(2)

# with col1:
#     st.date_input("Statement Date", date.today(), on_change=update_statement_id, key="need_statement_date")

# with col2:
#     if 'statement_id' not in st.session_state:
#         update_statement_id()
#     st.text_input("Statement ID:", value=st.session_state['statement_id'], disabled=True)

# st.text_input("Problem:", key="problem")
# st.text_input("Population:", key="population")
# st.text_input("Outcome:", key="outcome")
# st.text_area("Full Need Statement:", height=100, key="need_statement")
# st.text_area("Notes (Optional):", height=100, key="notes")

# # Submit Button
# if st.button("Submit Need Statement"):
#     need_statement_data = {
#         "problem": st.session_state['problem'],
#         "population": st.session_state['population'],
#         "outcome": st.session_state['outcome'],
#         "full_statement": st.session_state['need_statement'],
#         "notes": st.session_state['notes'],
#         "author": "Auto-generated",  # Placeholder for author, modify as needed
#         "statement_date": st.session_state['need_statement_date'],
#         "statement_id": st.session_state['statement_id'],
#     }

#     if addToGoogleSheets(need_statement_data):
#         st.success("Need statement(s) recorded!")
#         st.session_state['rerun'] = True
#         st.rerun()
#     else:
#         st.error("Error recording the need statement, please try again.")

# # Clear Button
# if st.button("Clear Form"):
#     for key in ['need_statement', 'problem', 'population', 'outcome', 'notes']:
#         st.session_state[key] = ""

# st.markdown("---")

# if st.button("Back to Main Menu"):
#     switch_page("main_menu")



# # Streamlit configuration
# st.set_page_config(page_title="Log a Need Statement", page_icon="✏️")
# st.markdown("# Add a New Need Statement")





# # ///////////////////////////////////

# # import time
# # import streamlit as st
# # from streamlit_extras.switch_page_button import switch_page


# # from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# # from langchain.chains import LLMChain
# # from langchain.output_parsers import PydanticOutputParser
# # # from langchain.callbacks import get_openai_callback
# # from langchain.schema import StrOutputParser
# # from langchain.schema.runnable import RunnableLambda
# # from langchain.prompts import PromptTemplate
# # from langchain_pinecone import PineconeVectorStore

# # import gspread
# # from oauth2client.service_account import ServiceAccountCredentials


# # from pydantic import BaseModel, Field
# # from typing import Optional
# # from datetime import date, datetime

# # import json
# # import os
# # import csv

# # st.set_page_config(page_title="Add a New Observation", page_icon="🔍")

# # st.markdown("# Add a New Observation")


# # observations_csv = "observations.csv"
# # OPENAI_API_KEY = st.secrets["openai_key"]

# # # Access the credentials from Streamlit secrets
# # #test
# # creds_dict = {
# #     "type" : st.secrets["gcp_service_account"]["type"],
# #     "project_id" : st.secrets["gcp_service_account"]["project_id"],
# #     "private_key_id" : st.secrets["gcp_service_account"]["private_key_id"],
# #     "private_key" : st.secrets["gcp_service_account"]["private_key"],
# #     "client_email" : st.secrets["gcp_service_account"]["client_email"],
# #     "client_id" : st.secrets["gcp_service_account"]["client_id"],
# #     "auth_uri" : st.secrets["gcp_service_account"]["auth_uri"],
# #     "token_uri" : st.secrets["gcp_service_account"]["token_uri"],
# #     "auth_provider_x509_cert_url" : st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
# #     "client_x509_cert_url" : st.secrets["gcp_service_account"]["client_x509_cert_url"],
# #     "universe_domain": st.secrets["gcp_service_account"]["universe_domain"],
# # }


# # if 'observation' not in st.session_state:
# #     st.session_state['observation'] = ""

# # if 'result' not in st.session_state:
# #     st.session_state['result'] = ""

# # if 'observation_summary' not in st.session_state:
# #     st.session_state['observation_summary'] = ""

# # if 'observation_date' not in st.session_state:
# #     st.session_state['observation_date'] = date.today()

# # if 'rerun' not in st.session_state:
# #     st.session_state['rerun'] = False

# # class ObservationRecord(BaseModel):
# #     location: Optional[str] = Field(default=None, description="Location or setting where this observation made. e.g. operating room (OR), hospital, exam room,....")
# #     people_present: Optional[str] = Field(default=None, description="People present during the observation. e.g. patient, clinician, scrub tech, family member, ...")
# #     sensory_observations: Optional[str] = Field(default=None, description="What is the observer sensing with sight, smell, sound, touch. e.g. sights, noises, textures, scents, ...")
# #     specific_facts: Optional[str] = Field(default=None, description="The facts noted in the observation. e.g. the wound was 8cm, the sclera had a perforation, the patient was geriatric, ...")
# #     insider_language: Optional[str] = Field(default=None, description="Terminology used that is specific to this medical practice or procedure. e.g. specific words or phrases ...")
# #     process_actions: Optional[str] = Field(default=None, description="Which actions occurred during the observation, and when they occurred. e.g. timing of various steps of a process, including actions performed by doctors, staff, or patients, could include the steps needed to open or close a wound, ...")
# #     # summary_of_observation: Optional[str] = Field(default=None, description="A summary of 1 sentence of the encounter or observation, e.g. A rhinoplasty included portions that were functional (covered by insurance), and cosmetic portions which were not covered by insurance. During the surgery, the surgeon had to provide instructions to a nurse to switch between functional and cosmetic parts, back and forth. It was mentioned that coding was very complicated for this procedure, and for other procedures, because there are 3 entities in MEE coding the same procedure without speaking to each other, ...")
# #     questions: Optional[str] = Field(default=None, description="Recorded open questions about people or their behaviors to be investigated later. e.g. Why is this procedure performed this way?, Why is the doctor standing in this position?, Why is this specific tool used for this step of the procedure? ...")

# # if not os.path.exists(observations_csv):
# #     observation_keys = list(ObservationRecord.__fields__.keys())
# #     observation_keys = ['observation_summary', 'observer', 'observation', 'observation_date', 'observation_id'] + observation_keys        
# #     csv_file = open(observations_csv, "w")
# #     csv_writer = csv.writer(csv_file, delimiter=";")
# #     csv_writer.writerow(observation_keys)

# # def parseObservation(observation: str):
# #     llm = ChatOpenAI(
# #         model_name="gpt-4o",
# #         temperature=0.7,
# #         openai_api_key=OPENAI_API_KEY,
# #         max_tokens=500,
# #     )

# #     observation_prompt = PromptTemplate.from_template(
# # """
# # You help me parse observations of medical procedures to extract details such as  surgeon, procedure and date, whichever is available.
# # Format Instructions for output: {format_instructions}

# # Observation: {observation}
# # Output:"""
# # )
# #     observationParser = PydanticOutputParser(pydantic_object=ObservationRecord)
# #     observation_format_instructions = observationParser.get_format_instructions()

# #     observation_chain = (
# #         observation_prompt | llm | observationParser
# #     )

# #     # with get_openai_callback() as cb:
# #     output = observation_chain.invoke({"observation": observation, "format_instructions": observation_format_instructions})

# #     return json.loads(output.json())

# # def extractObservationFeatures(observation):

# #     # Parse the observation
# #     parsed_observation = parseObservation(observation)

# #     input_fields = list(ObservationRecord.__fields__.keys())

# #     missing_fields = [field for field in input_fields if parsed_observation[field] is None]

# #     output = ""

# #     for field in input_fields:
# #         if field not in missing_fields:
# #             key_output = field.replace("_", " ").capitalize()
# #             output += f"**{key_output}**: {parsed_observation[field]}\n"
# #             output += "\n"

# #     missing_fields = [field.replace("_", " ").capitalize() for field in missing_fields]

# #     output += "\n\n **Missing fields**:"
# #     # for field in missing_fields:
# #     #     output += f" {field},"

# #     # # output += "\n\n"
# #     # # output += "="*75
# #     # output += "\nPlease add the missing fields to the observation if needed, then proceed with adding observation to your team record."

# #     # return f"{output}"

# #      # Add each missing field in red
# #     for field in missing_fields:
# #         output += f" <span style='color:red;'>{field}</span>,"

# #     # Display the output
# #     # st.markdown(output, unsafe_allow_html=True)
# #     return f"{output}"

# # def addToGoogleSheets(observation_dict):
# #     try:
# #         scope = [
# #         "https://www.googleapis.com/auth/spreadsheets",
# #         "https://www.googleapis.com/auth/drive.metadata.readonly"
# #         ]
# #         creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
# #         client = gspread.authorize(creds)
# #         observation_sheet = client.open("BioDesign Observation Record").sheet1

# #         headers = observation_sheet.row_values(1)

# #         # Prepare the row data matching the headers
# #         row_to_append = []
# #         for header in headers:
# #             if header in observation_dict:
# #                 value = observation_dict[header]
# #                 if value is None:
# #                     row_to_append.append("")
# #                 else:
# #                     row_to_append.append(str(observation_dict[header]))
# #             else:
# #                 row_to_append.append("")  # Leave cell blank if header not in dictionary

# #         # Append the row to the sheet
# #         observation_sheet.append_row(row_to_append)
# #         return True
# #     except Exception as e:
# #         print("Error adding to Google Sheets: ", e)
# #         return False

# # def embedObservation(observer, observation, observation_summary, observation_date, observation_id):
# #     db = PineconeVectorStore(
# #             index_name=st.secrets["pinecone-keys"]["index_to_connect"],
# #             namespace="observations",
# #             embedding=OpenAIEmbeddings(api_key=OPENAI_API_KEY),
# #             pinecone_api_key=st.secrets["pinecone-keys"]["api_key"],
# #         )
    
# #     db.add_texts([observation], metadatas=[{'observer': observer, 'observation_date': observation_date, 'observation_id': observation_id}])

# #     parsed_observation = parseObservation(observation)

# #     # write observer, observatoin and parsed observation to csv
# #     observation_keys = list(ObservationRecord.__fields__.keys())
# #     all_observation_keys = ['observation_summary', 'observer', 'observation', 'observation_date', 'observation_id'] + observation_keys
# #     observation_values = [observation_summary, observer, observation, observation_date, observation_id] + [parsed_observation[key] for key in observation_keys]

# #     observation_dict = dict(zip(all_observation_keys, observation_values))
# #     csv_file = open(observations_csv, "a")
# #     csv_writer = csv.writer(csv_file, delimiter=";")
# #     csv_writer.writerow(observation_values)

# #     status = addToGoogleSheets(observation_dict)

# #     return status


# # def generateObservationSummary(observation):

# #     llm = ChatOpenAI(
# #         model_name="gpt-4o",
# #         temperature=0.7,
# #         openai_api_key=OPENAI_API_KEY,
# #         max_tokens=500,
# #     )


# #     observation_prompt = PromptTemplate.from_template(
# # """
# # You help me by giving me the a one line summary of the following medical observation.

# # Observation: {observation}
# # Output Summary:"""
# # )

# #     observation_chain = (
# #         observation_prompt | llm | StrOutputParser()
# #     )

# #     # with get_openai_callback() as cb:
# #     output = observation_chain.invoke({"observation": observation})

# #     return output


# # def clear_observation():
# #     if 'observation' in st.session_state:
# #         st.session_state['observation'] = ""
# #     if 'observation_summary' in st.session_state:
# #         st.session_state['observation_summary'] = ""
# #     if 'result' in st.session_state:
# #         st.session_state['result'] = ""
# #     update_observation_id()

# # import streamlit as st
# # from datetime import date

# # # Initialize or retrieve the observation counters dictionary from session state
# # if 'observation_counters' not in st.session_state:
# #     st.session_state['observation_counters'] = {}

# # # Function to generate observation ID with the format OBYYMMDDxxxx
# # def generate_observation_id(observation_date, counter):
# #     return f"OB{observation_date.strftime('%y%m%d')}{counter:04d}"

# # # Function to update observation ID when the date changes
# # def update_observation_id():
# #     obs_date_str = st.session_state['observation_date'].strftime('%y%m%d')

# #     # get all observation ids from the sheets and update the counter
# #     scope = [
# #         "https://www.googleapis.com/auth/spreadsheets",
# #         "https://www.googleapis.com/auth/drive.metadata.readonly"
# #         ]
# #     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
# #     client = gspread.authorize(creds)
# #     observation_sheet = client.open("BioDesign Observation Record").sheet1
# #     column_values = observation_sheet.col_values(1) 

# #     # find all observation ids with the same date
# #     obs_date_ids = [obs_id for obs_id in column_values if obs_id.startswith(f"OB{obs_date_str}")]
# #     obs_date_ids.sort()

# #     # get the counter from the last observation id
# #     if len(obs_date_ids) > 0:
# #         counter = int(obs_date_ids[-1][-4:])+1
# #     else:
# #         counter = 1
    
# #     # # Check if the date is already in the dictionary
# #     # if obs_date_str in st.session_state['observation_counters']:
# #     #     # Increment the counter for this date
# #     #     st.session_state['observation_counters'][obs_date_str] += 1
# #     # else:
# #     #     # Initialize the counter to 1 for a new date
# #     #     st.session_state['observation_counters'][obs_date_str] = 1
    
# #     # Generate the observation ID using the updated counter
# #     # counter = st.session_state['observation_counters'][obs_date_str]

# #     st.session_state['observation_id'] = generate_observation_id(st.session_state['observation_date'], counter)

# # # Use columns to place observation_date, observation_id, and observer side by side
# # col1, col2, col3 = st.columns(3)

# # with col1:
# #     # st calendar for date input with a callback to update the observation_id
# #     st.date_input("Observation Date", date.today(), on_change=update_observation_id, key="observation_date")

# # with col2:
# #     # Ensure the observation ID is set the first time the script runs
# #     if 'observation_id' not in st.session_state:
# #         update_observation_id()

# #     # Display the observation ID
# #     st.text_input("Observation ID:", value=st.session_state['observation_id'], disabled=True)

# # with col3:
# #     #Display Observer options 
# #     observer = st.selectbox("Observer", ["Ana", "Bridget"])

# # ############

# # # # Function to generate observation ID with the format OBYYYYMMDDxxxx
# # # def generate_observation_id(observation_date, counter):
# # #     return f"OB{observation_date.strftime('%y%m%d')}{counter:04d}"

# # # # Initialize or retrieve observation ID counter from session state
# # # if 'observation_id_counter' not in st.session_state:
# # #     st.session_state['observation_id_counter'] = 1

# # # # Function to update observation ID when the date changes
# # # def update_observation_id():
# # #     st.session_state['observation_id'] = generate_observation_id(st.session_state['observation_date'], st.session_state['observation_id_counter'])

# # # # st calendar for date input with a callback to update the observation_id
# # # st.session_state['observation_date'] = st.date_input("Observation Date", date.today(), on_change=update_observation_id)

# # # # Initialize observation_id based on the observation date and counter
# # # st.session_state['observation_id'] = st.text_input("Observation ID:", value=st.session_state['observation_id'], disabled=True)

# # ##########

# # #new_observation_id = st.observation_date().strftime("%Y%m%d")+"%03d"%observation_id_counter
# # #st.session_state['observation_id'] = st.text_input("Observation ID:", value=new_observation_id)

# # #########

# # # Textbox for name input
# # #observer = st.selectbox("Observer", ["Ana", "Bridget"])

# # # ######

# # # # Text area for observation input
# # # st.session_state['observation'] = st.text_area("Add Your Observation", value=st.session_state['observation'], placeholder="Enter your observation...", height=200)

# # # ######


# # # Initialize the observation text in session state if it doesn't exist
# # if "observation" not in st.session_state:
# #     st.session_state["observation"] = ""

# # # Function to clear the text area
# # def clear_text():
# #     st.session_state["observation"] = ""

# # #st.markdown("---")

# # # Observation Text Area
# # ##

# # #observation_text = st.text_area("Observation", value=st.session_state["observation"], height=200, key="observation")

# # # Add Your Observation Text with larger font size
# # st.markdown("<h4 style='font-size:20px;'>Add Your Observation:</h4>", unsafe_allow_html=True)

# # # Button for voice input (currently as a placeholder)
# # if st.button("🎤 Record Observation (Coming Soon)"):
# #     st.info("Voice recording feature coming soon!")

# # # Observation Text Area
# # st.session_state['observation'] = st.text_area("Observation:", value=st.session_state["observation"], height=200)


# # # Create columns to align the buttons
# # col1, col2, col3 = st.columns([2, 2, 2])  # Adjust column widths as needed

# # with col3:
# #     # Use custom CSS for the red button
# #     # st.markdown("""
# #     #     <style>
# #     #     .stButton > button {
# #     #         background-color: #942124;
# #     #         color: white;
# #     #         font-size: 16px;
# #     #         padding: 10px 20px;
# #     #         border-radius: 8px;
# #     #         border: none;
# #     #     }
# #     #     .stButton > button:hover {
# #     #         background-color: darkred;
# #     #     }
# #     #     </style>
# #     #     """, unsafe_allow_html=True)

# #     # Button to Clear the Observation Text Area
# #     st.button("Clear Observation", on_click=clear_text)
    
# #     # Container for result display
# #     result_container = st.empty()

# # # #Use columns to place buttons side by side
# # # col11, col21 = st.columns(2)


# # # with col11:
# # #     if st.button("Generate Observation Summary"):
# # #         st.session_state['observation_summary']  = generateObservationSummary(st.session_state['observation'])

# # #     if st.session_state['observation_summary'] != "":
# # #         st.session_state['observation_summary'] = st.text_area("Generated Summary (editable):", value=st.session_state['observation_summary'], height=50)
    

# # with col1:
# #     if st.button("Evaluate Observation"):
# #         st.session_state['result'] = extractObservationFeatures(st.session_state['observation'])
# #         st.session_state['observation_summary']  = generateObservationSummary(st.session_state['observation'])
    
# # if st.session_state['observation_summary'] != "":
# #     st.session_state['observation_summary'] = st.text_area("Generated Summary (editable):", value=st.session_state['observation_summary'], height=50)

# # # st.write(f":green[{st.session_state['result']}]")
# # st.markdown(st.session_state['result'], unsafe_allow_html=True)

# # if st.session_state['rerun']:
# #     time.sleep(3)
# #     clear_observation()
# #     st.session_state['rerun'] = False
# #     st.rerun()
    
# #     ##########

# # if st.button("Add Observation to Team Record", disabled=st.session_state['observation_summary'] == ""):
# #     # st.session_state['observation_summary']  = generateObservationSummary(st.session_state['observation'])
# #     st.session_state["error"] = ""

# #     if st.session_state['observation'] == "":
# #         st.session_state["error"] = "Error! Please enter observation first"
# #         st.markdown(
# #             f"<span style='color:red;'>{st.session_state['error']}</span>", 
# #             unsafe_allow_html=True
# #         )
# #     elif st.session_state['observation_summary'] == "":
# #         st.session_state["error"] = "Error! Please evaluate observation first"
# #         st.markdown(
# #             f"<span style='color:red;'>{st.session_state['error']}</span>", 
# #             unsafe_allow_html=True
# #         )
# #     else:
# #         status = embedObservation(observer, st.session_state['observation'],  st.session_state['observation_summary'], 
# #                             st.session_state['observation_date'],
# #                             st.session_state['observation_id'])
# #         # st.session_state['observation_summary'] = st.text_input("Generated Summary (editable):", value=st.session_state['observation_summary'])
# #         # "Generated Summary: "+st.session_state['observation_summary']+"\n\n"
# #         if status:
# #             st.session_state['result'] = "Observation added to your team's database."
# #             st.session_state['rerun'] = True
# #             st.rerun()
# #         else:
# #             st.session_state['result'] = "Error adding observation to your team's database, try again!"
# #         # clear_observation()

# # st.markdown("---")

# # # if st.button("Back to Main Menu"):
# # #     clear_observation()
# # #     switch_page("main_menu")


# # # st.markdown("---")
# # # Apply custom CSS to make the button blue
# # st.markdown("""
# #     <style>
# #     div.stButton > button {
# #         background-color: #365980;
# #         color: white;
# #         font-size: 16px;
# #         padding: 10px 20px;
# #         border: none;
# #         border-radius: 5px;
# #     }
# #     div.stButton > button:hover {
# #         background-color: #2c4a70;
# #         color: white;
# #     }
# #     </style>
# #     """, unsafe_allow_html=True)



# # # Create a button using Streamlit's native functionality
# # if st.button("Back to Main Menu"):
# #     switch_page("main_menu")
