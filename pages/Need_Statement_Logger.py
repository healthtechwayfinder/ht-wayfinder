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
# -> could the observation bot page have a widget in the right-hand sidebar for entering need satements from that page? (in case something comes up from a conversation)

# I propose copying the code over form the Add Observation page, but removing the AI components -- only entering info from the user right to the log

import os
import csv
import json
import time
from datetime import date, datetime
from typing import Optional

import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pydantic import BaseModel, Field
from streamlit_extras.switch_page_button import switch_page

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser, StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_pinecone import PineconeVectorStore

# Streamlit configuration
st.set_page_config(page_title="Log a Need Statement", page_icon="✏️")
st.markdown("# Add a New Observation")

# Constants
observations_csv = "observations.csv"
OPENAI_API_KEY = st.secrets["openai_key"]

# Access GCP credentials from Streamlit secrets
creds_dict = {
    key: st.secrets["gcp_service_account"][key]
    for key in st.secrets["gcp_service_account"]
}

# Initialize session state variables
for key, default in {
    'observation': "",
    'result': "",
    'observation_summary': "",
    'observation_date': date.today(),
    'rerun': False,
    'parsed_observation': None,
    'verification': None,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Define the ObservationRecord model
class ObservationRecord(BaseModel):
    location: Optional[str] = Field(None, description="Location or setting where this observation made.")
    people_present: Optional[str] = Field(None, description="People present during the observation.")
    sensory_observations: Optional[str] = Field(None, description="Sensory observations.")
    specific_facts: Optional[str] = Field(None, description="Facts noted in the observation.")
    insider_language: Optional[str] = Field(None, description="Terminology used specific to the practice.")
    process_actions: Optional[str] = Field(None, description="Actions occurred during the observation.")
    questions: Optional[str] = Field(None, description="Open questions to be investigated later.")

# Create CSV file if it doesn't exist
if not os.path.exists(observations_csv):
    observation_keys = ['observation_summary', 'observer', 'observation', 'observation_date', 'observation_id'] + list(ObservationRecord.__fields__.keys())
    with open(observations_csv, "w") as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=";")
        csv_writer.writerow(observation_keys)

# Functions for observation parsing, feature extraction, and storage
def parseObservation(observation: str):
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0.7, openai_api_key=OPENAI_API_KEY, max_tokens=500)

    observation_prompt = PromptTemplate.from_template(
        "You help me parse observations of medical procedures to extract details such as surgeon, procedure, and date."
        "Format Instructions for output: {format_instructions}\n\nObservation: {observation}\nOutput:"
    )

    observationParser = PydanticOutputParser(pydantic_object=ObservationRecord)
    observation_format_instructions = observationParser.get_format_instructions()

    observation_chain = LLMChain(prompt=observation_prompt, llm=llm, output_parser=observationParser)

    output = observation_chain.invoke({"observation": observation, "format_instructions": observation_format_instructions})

    return json.loads(output.json())

def addToGoogleSheets(observation_dict):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.metadata.readonly"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        observation_sheet = client.open("BioDesign Observation Record").sheet1
        headers = observation_sheet.row_values(1)
        row_to_append = [str(observation_dict.get(header, "")) for header in headers]
        observation_sheet.append_row(row_to_append)
        return True
    except Exception as e:
        print("Error adding to Google Sheets: ", e)
        return False

def embedObservation(observer, observation, observation_summary, observation_date, observation_id, observation_data):
    db = PineconeVectorStore(
        index_name=st.secrets["pinecone-keys"]["index_to_connect"],
        namespace="observations",
        embedding=OpenAIEmbeddings(api_key=OPENAI_API_KEY),
        pinecone_api_key=st.secrets["pinecone-keys"]["api_key"],
    )
    db.add_texts([observation], metadatas=[{'observer': observer, 'observation_date': observation_date, 'observation_id': observation_id}])

    observation_keys = ['observation_summary', 'observer', 'observation', 'observation_date', 'observation_id'] + list(ObservationRecord.__fields__.keys())
    observation_values = [observation_summary, observer, observation, observation_date, observation_id] + [observation_data[key] for key in ObservationRecord.__fields__.keys()]
    observation_dict = dict(zip(observation_keys, observation_values))

    with open(observations_csv, "a") as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=";")
        csv_writer.writerow(observation_values)

    return addToGoogleSheets(observation_dict)

def generateObservationSummary(observation):
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0.7, openai_api_key=OPENAI_API_KEY, max_tokens=500)
    observation_prompt = PromptTemplate.from_template(
        "You help me by giving me a one-line summary of the following medical observation.\n\nObservation: {observation}\nOutput Summary:"
    )
    observation_chain = LLMChain(prompt=observation_prompt, llm=llm, output_parser=StrOutputParser())
    return observation_chain.invoke({"observation": observation})

def clear_observation():
    for key in ['observation', 'observation_summary', 'result', 'parsed_observation', 'verification']:
        st.session_state[key] = ""
    update_observation_id()

# Functions for observation ID generation and updating
def generate_observation_id(observation_date, counter):
    return f"OB{observation_date.strftime('%y%m%d')}{counter:04d}"

def update_observation_id():
    obs_date_str = st.session_state['observation_date'].strftime('%y%m%d')
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.metadata.readonly"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    observation_sheet = client.open("BioDesign Observation Record").sheet1
    obs_date_ids = [obs_id for obs_id in observation_sheet.col_values(1) if obs_id.startswith(f"OB{obs_date_str}")]
    counter = int(obs_date_ids[-1][-4:]) + 1 if obs_date_ids else 1
    st.session_state['observation_id'] = generate_observation_id(st.session_state['observation_date'], counter)

# Streamlit UI components
col1, col2, col3 = st.columns(3)

with col1:
    st.date_input("Observation Date", date.today(), on_change=update_observation_id, key="observation_date")

with col2:
    if 'observation_id' not in st.session_state:
        update_observation_id()
    st.text_input("Observation ID:", value=st.session_state['observation_id'], disabled=True)

with col3:
    observer = st.selectbox("Observer", ["Ana", "Bridget"])

st.markdown("<h4 style='font-size:20px;'>Add Your Observation:</h4>", unsafe_allow_html=True)

if st.button("🎤 Record Observation (Coming Soon)"):
    st.info("Voice recording feature coming soon!")

st.text_area("Observation:", value=st.session_state["observation"], height=200, key='observation')

col1, col2, col3 = st.columns(3)

with col3:
    st.button("Clear Observation", on_click=clear_observation)

with col1:
    if st.button("Evaluate Observation"):
        st.session_state['parsed_observation'] = parseObservation(st.session_state['observation'])
        st.session_state['observation_summary'] = generateObservationSummary(st.session_state['observation'])

if st.session_state['parsed_observation']:
    st.markdown("### Verify or Edit Observation Data")

    # Editable fields for each parsed observation field
    st.session_state['verification'] = {}

    st.text_input("Observation Summary", value=st.session_state['observation_summary'], key="observation_summary")
    for field, value in st.session_state['parsed_observation'].items():
        st.session_state['verification'][field] = {
            "value": st.text_input(field.replace("_", " ").capitalize(), value=value),
            "verified": st.checkbox(f"Verify {field.replace('_', ' ').capitalize()}", value=True)
        }

if st.session_state['parsed_observation']:
    all_verified = all(st.session_state['verification'][field]['verified'] for field in st.session_state['verification'])

    if st.button("Add Observation to Team Record", disabled=not all_verified):
        if embedObservation(observer, st.session_state['observation'], st.session_state['observation_summary'],
                            st.session_state['observation_date'], st.session_state['observation_id'],
                            {field: st.session_state['verification'][field]['value'] for field in st.session_state['verification']}):
            st.success("Observation added to your team's database.")
            st.session_state['rerun'] = True
            st.rerun()
        else:
            st.error("Error adding observation to your team's database, try again!")

st.markdown("---")

if st.button("Back to Main Menu"):
    switch_page("main_menu")
