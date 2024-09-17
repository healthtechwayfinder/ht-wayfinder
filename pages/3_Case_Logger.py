
import time
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
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

st.set_page_config(page_title="Add or Edit a Case", page_icon="🏥")

# Dropdown menu for selecting action
action = st.selectbox("Choose an action", ["Add New Case", "Edit Existing Case"])

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

if 'case_description' not in st.session_state:
    st.session_state['case_description'] = ""

if 'result' not in st.session_state:
    st.session_state['result'] = ""

if 'case_title' not in st.session_state:
    st.session_state['case_title'] = ""

if 'rerun' not in st.session_state:
    st.session_state['rerun'] = False

if 'parsed_case' not in st.session_state:
    st.session_state['parsed_case'] = ""

class caseRecord(BaseModel):
    location: Optional[str] = Field(default=None, description="(only nouns) physical environment where the case took place. e.g: operating room, at the hospital MGH, in the emergency room...")
    stakeholders: Optional[str] = Field(default=None, description="Stakeholders involved in the healthcare event (no names).")
    people_present: Optional[str] = Field(default=None, description="Names cited in the description")
    insider_language: Optional[str] = Field(default=None, description="Terminology used that is specific to this medical practice or procedure.")
    tags: Optional[str] = Field(default=None, description="Generate a list of 3-5 tags that are very relevant to the medical observation.")

# Function to parse the case description
def parseCase(case_description: str):
    llm = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0.7,
        openai_api_key=OPENAI_API_KEY,
        max_tokens=500,
    )

    case_prompt = PromptTemplate.from_template(
"""
You help me parse descriptions of medical procedures or cases to extract details such as surgeon, procedure and date, whichever is available.
Format Instructions for output: {format_instructions}

case_description: {case_description}
Output:"""
)
    caseParser = PydanticOutputParser(pydantic_object=caseRecord)
    case_format_instructions = caseParser.get_format_instructions()

    case_chain = (
        case_prompt | llm | caseParser
    )

    output = case_chain.invoke({"case_description": case_description, "format_instructions": case_format_instructions})

    return json.loads(output.json())

def extractCaseFeatures(case_description):
    # Parse the case
    parsed_case = parseCase(case_description)
    st.session_state['parsed_case'] = parsed_case

    input_fields = list(caseRecord.__fields__.keys())
    missing_fields = [field for field in input_fields if parsed_case[field] is None]

    output = ""
    for field in input_fields:
        if field not in missing_fields:
            key_output = field.replace("_", " ").capitalize()
            output += f"**{key_output}**: {parsed_case[field]}\n"
            output += "\n"

    missing_fields = [field.replace("_", " ").capitalize() for field in missing_fields]

    if len(missing_fields) > 0:
        output += "\n\n **Missing fields**:"

        for field in missing_fields:
            output += f" <span style='color:red;'>{field}</span>,"

    return f"{output}"

def generateCaseSummary(case_description):
    llm = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0.7,
        openai_api_key=OPENAI_API_KEY,
        max_tokens=500,
    )

    case_prompt = PromptTemplate.from_template(
"""
You help me by creating a brief 4-10 word title of the following medical case description. Do not use quotes or special characters in the title.

case_description: {case_description}
Output title:"""
)

    case_chain = (
        case_prompt | llm | StrOutputParser()
    )

    output = case_chain.invoke({"case_description": case_description})

    return output

# If the user chooses "Add New Case"
if action == "Add New Case":
    st.markdown("### Add a New Case")
    
    # Initialize or retrieve the clear_case counters dictionary from session state
    if 'case_counters' not in st.session_state:
        st.session_state['case_counters'] = {}
    
    # Function to generate case ID with the format CAYYMMDDxxxx
    def generate_case_ID(case_date, counter):
        return f"CA{case_date.strftime('%y%m%d')}{counter:04d}"
    
    # Function to update case ID when the date changes
    def update_case_ID():
        case_date_str = st.session_state['case_date'].strftime('%y%m%d')

        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        case_sheet = client.open("2024 Healthtech Identify Log").worksheet("Case Log")
        column_values = case_sheet.col_values(1) 

        case_date_ids = [case_id for case_id in column_values if case_id.startswith(f"CA{case_date_str}")]
        case_date_ids.sort()

        if len(case_date_ids) > 0:
            counter = int(case_date_ids[-1][-4:]) + 1
        else:
            counter = 1

        st.session_state['case_ID'] = generate_case_ID(st.session_state['case_date'], counter)
    
    col1, col2, col3 = st.columns(3)

    with col1:
        st.date_input("Case Date", date.today(), on_change=update_case_ID, key="case_date")

    with col2:
        if 'case_ID' not in st.session_state:
            update_case_ID()
        st.text_input("Case ID:", value=st.session_state['case_ID'], disabled=True)

    with col3:
        st.session_state['attendees'] = st.multiselect("Attendees", ["Deborah", "Kyle", "Ryan", "Lois", "Fellowisa"])

    if "case_description" not in st.session_state:
        st.session_state["case_description"] = ""

    st.markdown("<h4 style='font-size:20px;'>Add Your Case:</h4>", unsafe_allow_html=True)
    st.session_state['case_description'] = st.text_area("Case:", value=st.session_state["case_description"], height=200)

    with col1:
        if st.button("Submit Case"):
            st.session_state['result'] = extractCaseFeatures(st.session_state['case_description'])
            st.session_state['case_title'] = generateCaseSummary(st.session_state['case_description'])

    if st.session_state['case_title'] != "":
        st.session_state['case_title'] = st.text_area("Case Title (editable):", value=st.session_state['case_title'], height=50)

    expected_fields = ['Location', 'Stakeholders', 'People Present', 'Insider Language', 'Tags', 'Observations']

    if 'result' in st.session_state and st.session_state['result'] != "":
        parsed_result = st.session_state['result']
        lines = parsed_result.splitlines()
        editable_fields = {}

        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                editable_fields[key] = value

        for field in expected_fields:
            if field in editable_fields:
                st.session_state['editable_result'] = st.text_input(f"{field}", value=editable_fields[field])
            else:
                st.session_state['editable_result'] = st.text_input(f"{field} (missing)", value="")

    if st.session_state.get('rerun)
