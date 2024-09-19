import time
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import Optional
from datetime import date

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import langchain and other required libraries
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnableLambda
from langchain.prompts import PromptTemplate
from langchain_pinecone import PineconeVectorStore

# Pydantic models and other dependencies
from pydantic import BaseModel, Field
import json
import os
import csv

# Load credentials from Streamlit secrets
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

# Initialize session state variables
for key in ["observation", "result", "observation_summary", "observation_tags", "rerun"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# Function to connect to Google Sheets
def get_google_sheet(sheet_name, worksheet_name):
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(credentials)
    sheet = client.open("2024 Healthtech Identify Log").worksheet("Observation Log")
    return sheet

# Function to get observation IDs from the Google Sheet
def get_observation_ids():
    sheet = get_google_sheet("2024 Healthtech Identify Log", "Observation Log")
    
    # Fetch relevant columns from the sheet
    observation_ids = sheet.col_values(1)[1:]  # Skip header
    observation_titles = sheet.col_values(2)[1:]  # Titles
    observation_ids_with_title = dict(zip(observation_ids, observation_titles))
    
    # Create formatted list with ID - title format
    formatted_observations = [f"{obs_id} - {title}" for obs_id, title in observation_ids_with_title.items()]
    
    logging.info(f"Existing Observation IDs: {formatted_observations}")
    return formatted_observations

# Correct the list of observations to use string literals
observations = [
    "OB2409100015", "OB2409180003", "OB2409190002", "OB2409190003", 
    "OB2409190004", "OB2409190005", "OB2409190006", "OB2409190007"
]

# Function to filter and return observation data for the given list of observation IDs
def get_filtered_observation_data(observations, observation_data):
    filtered_data = {obs_id: observation_data[obs_id] for obs_id in observations if obs_id in observation_data}
    return filtered_data

# Get the observation IDs from Google Sheets
observation_ids = get_observation_ids()

formatted_observations = get_filtered_observation_data(observations,observation_ids)

# Streamlit UI for Observation ID Selection
st.title("Observation ID Selection")

# Multi-select dropdown with observation IDs
selected_observation_ids = st.multiselect("Select Observation IDs:", formatted_observations)

# Display the selected Observation IDs
if selected_observation_ids:
    st.write("You selected the following Observation IDs:", selected_observation_ids)

