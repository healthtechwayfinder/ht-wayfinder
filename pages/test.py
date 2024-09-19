import time
import streamlit as st
from streamlit_extras.switch_page_button import switch_page

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


if 'observation' not in st.session_state:
    st.session_state['observation'] = ""

if 'result' not in st.session_state:
    st.session_state['result'] = ""

if 'observation_summary' not in st.session_state:
    st.session_state['observation_summary'] = ""

if 'observation_tags' not in st.session_state:
    st.session_state['observation_tags'] = ""

# if 'observation_date' not in st.session_state:
#     st.session_state['observation_date'] = date.today()

if 'rerun' not in st.session_state:
    st.session_state['rerun'] = False

# Function to connect to Google Sheets
def get_google_sheet(sheet_name, worksheet_name):
    # Define the scope for accessing Google Sheets API
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Use the credentials from your service account JSON file
    credentials = ServiceAccountCredentials.from_json_keyfile_name("path_to_your_credentials.json", scope)
    
    # Authorize the client
    client = gspread.authorize(credentials)
    
    # Open the Google Sheet
    sheet = client.open(sheet_name).worksheet(worksheet_name)
    
    return sheet

# Function to get observation IDs from the Google Sheet
def get_observation_ids():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    observation_log = client.open("2024 Healthtech Identify Log").worksheet("CObservation Log")
    observation_ids = observation_log.col_values(1)[1:]
    observation_dates_list = observation_log.col_values(3)[1:]
    observation_titles = observation_log.col_values(2)[1:]

    # find all observation ids with the same date
    existing_observation_ids_with_title = dict(zip(observation_ids, observation_titles))

    # make strings with case id - title
    existing_observation_ids_with_title = [f"{observation_id} - {observation_title}" for observation_id, observation_title in existing_observation_ids_with_title.items()]

    print("Existing Observation IDS: ")
    print(existing_observation_ids_with_title)
    return existing_observation_ids_with_title

# In your Streamlit app, create a multi-select dropdown
st.title("Observation ID Selection")

# Get the observation IDs from Google Sheets
observation_ids = get_observation_ids()

# Display the multi-select dropdown with the observation IDs
selected_observation_ids = st.multiselect("Select Observation IDs:", observation_ids)

# Display the selected Observation IDs
if selected_observation_ids:
    st.write("You selected the following Observation IDs:", selected_observation_ids)
