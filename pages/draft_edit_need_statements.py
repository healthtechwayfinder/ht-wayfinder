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
if 'obs_id_with_title' not in st.session_state:
    st.session_state.obs_id_with_title = ''

if 'need_statement' not in st.session_state:
    st.session_state.need_statement = ''

if 'problem' not in st.session_state:
    st.session_state['problem'] = ""

if 'population' not in st.session_state:
    st.session_state['population'] = ""

if 'outcome' not in st.session_state:
    st.session_state['outcome'] = ""

if 'notes' not in st.session_state:
    st.session_state['notes'] = ""

if 'observation_ID' not in st.session_state:
    st.session_state['observation_ID'] = ""

if 'result' not in st.session_state:
    st.session_state['result'] = ""

if 'rerun' not in st.session_state:
    st.session_state['rerun'] = False


# ////////////////////// FUNCTIONS ////////////////////// FUNCTIONS ////////////////////// FUNCTIONS ////////////////////// 


# get need IDs with preview
def getExistingNeedIDS():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    need_log = client.open("2024 Healthtech Identify Log").worksheet("Need Statement Log")
    need_ids = need_log.col_values(1)[1:]
    need_previews = need_log.col_values(3)[1:]

    # find all observation ids with the same date
    existing_need_ids_with_title = dict(zip(need_ids, need_previews))

    # make strings with case id - title
    existing_need_ids_with_title = [f"{case_id} - {case_title}" for case_id, case_title in existing_need_ids_with_title.items()]

    print("Existing Observation IDS: ")
    print(existing_need_ids_with_title)
    return existing_need_ids_with_title




# ////////////////////// CODE ON PAGE ////////////////////// CODE ON PAGE ////////////////////// CODE ON PAGE //////////////////////

# Dropdown menu for selecting action
action = st.selectbox("Choose an action", ["Add New Case", "Edit Existing Case"])


# select from a list of needs
existing_need_ids_with_title = getExistingNeedIDS()
st.session_state['obs_id_with_title'] = st.selectbox("Related Observation ID", existing_need_ids_with_title)






# ////////////////////// NOTES ////////////////////// NOTES ////////////////////// NOTES ////////////////////// 













