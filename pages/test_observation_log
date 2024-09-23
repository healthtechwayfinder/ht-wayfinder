import time
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import logging
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_pinecone import PineconeVectorStore
from streamlit_tags import st_tags
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime
import json

# from utils.login_utils import check_if_already_logged_in

# Function to initialize session state variables
def init_session_state():
    session_keys = ['observation', 'parsed_observation', 'result', 'observation_summary', 'observation_tags', 
                    'rerun', 'observer', 'selected_case_id_with_title', 'selected_observation']
    for key in session_keys:
        if key not in st.session_state:
            st.session_state[key] = "" if key != 'observation_tags' else []

# Initialize session state variables
init_session_state()

# Function to get Google Sheets client
def get_google_sheets_client():
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
        "universe_domain": st.secrets["gwf_service_account"]["universe_domain"]
    }

    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

# Function to fetch Google Sheet
def get_google_sheet(spreadsheet_name, worksheet_name):
    client = get_google_sheets_client()
    sheet = client.open(spreadsheet_name).worksheet(worksheet_name)
    return sheet

# Fetch case IDs and titles from Google Sheets
def fetch_observation_ids_and_titles():
    try:
        sheet = get_google_sheet("2024 Healthtech Identify Log", "Observation Log")
        data = sheet.get_all_records()
        observation_info = [(row["Observation ID"], row["Observation Title"]) for row in data if "Observation ID" in row and "Observation Title" in row]
        return observation_info
    except Exception as e:
        logging.error(f"Error fetching Observation IDs and titles: {e}")
        return []

# Function to fetch observation details from Google Sheets
def fetch_observation_details(observation_id):
    try:
        sheet = get_google_sheet("2024 Healthtech Identify Log", "Observation Log")
        data = sheet.get_all_records()
        for row in data:
            if "Observation ID" in row and row["Observation ID"].strip() == observation_id.strip():
                return row
        st.error(f"Observation ID {observation_id} not found.")
    except Exception as e:
        logging.error(f"Error fetching observation details: {e}")
        return None

# Create and initialize LLM model
def get_llm():
    OPENAI_API_KEY = st.secrets.get("openai_key")
    if not OPENAI_API_KEY:
        st.error("OpenAI API Key is missing from secrets!")
        st.stop()
    
    return ChatOpenAI(model_name="gpt-4", temperature=0.7, openai_api_key=OPENAI_API_KEY, max_tokens=100)

# Function to generate observation tags
def generate_observation_tags(observation):
    llm = get_llm()
    observation_tags_prompt = PromptTemplate.from_template(
        """
        Generate a list of 3-5 tags (only nouns) that are very relevant to the medical observation.
        Tags:
        """
    )
    observation_chain = observation_tags_prompt | llm | StrOutputParser()
    output = observation_chain.invoke({"observation": observation})
    return output

# Class for parsing observation records
class ObservationRecord(BaseModel):
    stakeholders: Optional[str] = Field(default=None, description="Stakeholders involved...")
    sensory_observations: Optional[str] = Field(default=None, description="What is the observer sensing...")
    product_interactions: Optional[str] = Field(default=None, description="How is equipment and technology...")
    people_interactions: Optional[str] = Field(default=None, description="How people interact...")
    process_actions: Optional[str] = Field(default=None, description="Specific step or task...")
    insider_language: Optional[str] = Field(default=None, description="Terminology used...")
    tags: Optional[str] = Field(default=None, description="Generate a list of 3-5 tags...")

# Function to parse observation using LLM
def parse_observation(observation: str):
    llm = get_llm()
    observation_prompt = PromptTemplate.from_template(
        """
        You help me parse observations of medical procedures...
        Observation: {observation}
        Output:
        """
    )
    observation_parser = PydanticOutputParser(pydantic_object=ObservationRecord)
    observation_chain = observation_prompt | llm | observation_parser
    output = observation_chain.invoke({"observation": observation})
    return json.loads(output.json())

# Function to embed observation in Pinecone
def embed_observation(observer, observation, observation_summary, observation_tags, observation_date, observation_id, related_case_id_with_title):
    related_case_id = related_case_id_with_title.split(" - ")[0]

    db = PineconeVectorStore(
        index_name=st.secrets["pinecone-keys"]["index_to_connect"],
        namespace="observations",
        embedding=OpenAIEmbeddings(api_key=st.secrets["openai_key"]),
        pinecone_api_key=st.secrets["pinecone-keys"]["api_key"],
    )
    db.add_texts([observation], metadatas=[{
        'observer': observer,
        'observation_date': observation_date,
        'observation_id': observation_id,
        'tags': observation_tags,
        'case_id': related_case_id
    }])

# Function to add the observation to Google Sheets
def add_to_google_sheets(observation_dict):
    try:
        observation_sheet = get_google_sheet("2024 Healthtech Identify Log", "Observation Log")
        headers = observation_sheet.row_values(1)
        row_to_append = [observation_dict.get(header, "") for header in headers]
        observation_sheet.append_row(row_to_append)
        return True
    except Exception as e:
        logging.error(f"Error adding to Google Sheets: {e}")
        return False

# UI for observation logger
def observation_logger_ui():
    st.set_page_config(page_title="Add a New Observation", page_icon="🔍")
    st.markdown("# Observation Logger")

    action = st.selectbox("", ["Add New Observation", "Edit Existing Observation"], label_visibility="collapsed")

    if action == "Add New Observation":
        st.date_input("Observation Date", value=st.session_state.get('observation_date', date.today()), key='observation_date')
        st.text_input("Observation ID:", value=st.session_state.get('observation_id', ''), disabled=True)
        observer = st.selectbox("Observer", ["", "Deborah", "Kyle", "Ryan", "Lois"], key='observer_key')

        st.text_area("Observation:", value=st.session_state.get("observation", ""), height=200)

        if st.button("Review Observation"):
            st.session_state['observation_summary'] = generate_observation_tags(st.session_state['observation'])
            st.session_state['result'] = parse_observation(st.session_state['observation'])

        if st.button("Log Observation"):
            embed_observation(
                observer,
                st.session_state['observation'],
                st.session_state['observation_summary'],
                st.session_state['observation_tags'],
                st.session_state['observation_date'],
                st.session_state['observation_id'],
                st.session_state['selected_case_id_with_title']
            )

    elif action == "Edit Existing Observation":
        st.markdown("### Edit an Existing Observation")
        observation_info = fetch_observation_ids_and_titles()
        if observation_info:
            selected_observation = st.selectbox("", [f"{ob_id}: {title}" for ob_id, title in observation_info])
            if selected_observation:
                observation_id = selected_observation.split(":")[0].strip()
                observation_details = fetch_observation_details(observation_id)
                if observation_details:
                    st.text_area("Edit Observation", value=observation_details.get("Observation Description", ""))

# Run the observation logger UI
if __name__ == "__main__":
    observation_logger_ui()
