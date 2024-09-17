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

# Initialize session state variables
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

# Define caseRecord schema for parsing
class caseRecord(BaseModel):
    location: Optional[str] = Field(default=None, description="Physical environment where the case took place.")
    stakeholders: Optional[str] = Field(default=None, description="Stakeholders involved in the healthcare event.")
    people_present: Optional[str] = Field(default=None, description="People present during the case.")
    insider_language: Optional[str] = Field(default=None, description="Medical terminologies used in the case.")
    tags: Optional[str] = Field(default=None, description="Relevant tags for the medical observation.")

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
You help me parse descriptions of medical procedures or cases to extract details such as surgeon, procedure, and date, whichever is available.
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

# Function to extract case features and display missing fields
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

# Function to generate the case summary
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

# Display the form for adding a new case
if action == "Add New Case":
    st.markdown("### Add a New Case")
    
    # Case input fields
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.date_input("Case Date", date.today(), key="case_date")

    with col2:
        st.text_input("Case ID:", value=st.session_state['case_ID'], disabled=True)

    with col3:
        st.session_state['attendees'] = st.multiselect("Attendees", ["Deborah", "Kyle", "Ryan", "Lois", "Fellowisa"])

    st.markdown("<h4 style='font-size:20px;'>Add Your Case:</h4>", unsafe_allow_html=True)
    st.session_state['case_description'] = st.text_area("Case:", value=st.session_state["case_description"], height=200)

    # Submit button
    with col1:
        if st.button("Submit Case"):
            st.session_state['result'] = extractCaseFeatures(st.session_state['case_description'])
            st.session_state['case_title'] = generateCaseSummary(st.session_state['case_description'])

    # Editable case title if available
    if st.session_state['case_title'] != "":
        st.session_state['case_title'] = st.text_area("Case Title (editable):", value=st.session_state['case_title'], height=50)

    # Define all expected fields, including missing ones
    expected_fields = {
        'Location': '',
        'Stakeholders': '',
        'People Present': '',
        'Insider Language': '',
        'Tags': '',
        'Observations': ''
    }

    # Display each field as editable, including missing fields
    if 'result' in st.session_state and st.session_state['result'] != "":
        parsed_result = st.session_state['result']
        
        # Split the result into lines
        lines = parsed_result.splitlines()
        editable_fields = {}

        # Parse existing fields from the result
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                editable_fields[key] = value  # Store existing field-value pairs

        # Display all expected fields, even the empty ones
        for field in expected_fields:
            if field in editable_fields:
                st.text_input(f"{field}", value=editable_fields[field])
            else:
                st.text_input(f"{field} (missing)", value="")

    # Handle rerun logic if needed
    if st.session_state.get('rerun', False):
        time.sleep(3)
        clear_case()
        st.session_state['rerun'] = False
        st.rerun()

    # Logging the case
    if st.button("Log Case", disabled=st.session_state['case_title'] == ""):
        if st.session_state['case_description'] == "":
            st.markdown("<span style='color:red;'>Error: Please enter case.</span>", unsafe_allow_html=True)
        elif st.session_state['case_title'] == "":
            st.markdown("<span style='color:red;'>Error: Please evaluate case.</span>", unsafe_allow_html=True)
        else:
            status = embedCase(
                st.session_state['attendees'], 
                st.session_state['case_description'],  
                st.session_state['case_title'], 
                st.session_state['case_date'],
                st.session_state['case_ID']
            )
            if status:
                st.session_state['result'] = "Case added to your team's database."
                st.session_state['rerun'] = True
                st.rerun()
            else:
                st.session_state['result'] = "Error adding case to your team's database. Please try again!"
