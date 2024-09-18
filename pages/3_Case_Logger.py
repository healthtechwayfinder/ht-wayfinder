import time
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import StrOutputParser
from langchain.prompts import PromptTemplate
from langchain_pinecone import PineconeVectorStore
from pydantic import BaseModel, Field
from typing import Optional
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import date
import json

# Streamlit page setup
st.set_page_config(page_title="Add or Edit a Case", page_icon="🏥")
action = st.selectbox("Choose an action", ["Add New Case", "Edit Existing Case"])

# OpenAI API key and Google credentials
OPENAI_API_KEY = st.secrets["openai_key"]
creds_dict = st.secrets["gwf_service_account"]

# Session state initialization
for key in ['case_description', 'result', 'case_title', 'rerun', 'parsed_case']:
    if key not in st.session_state:
        st.session_state[key] = ""

class CaseRecord(BaseModel):
    location: Optional[str] = Field(default=None, description="Location of the case.")
    stakeholders: Optional[str] = Field(default=None, description="Stakeholders involved.")
    people_present: Optional[str] = Field(default=None, description="People present.")
    insider_language: Optional[str] = Field(default=None, description="Insider language used.")
    tags: Optional[str] = Field(default=None, description="Relevant tags for the case.")

# Function to generate a definition using OpenAI API
def generate_definition(term):
    llm = ChatOpenAI(
        model_name="gpt-4o", temperature=0.7, openai_api_key=OPENAI_API_KEY, max_tokens=100
    )
    prompt = PromptTemplate.from_template("Provide a brief, simple definition for the following medical term: {term}.")
    definition_chain = LLMChain(llm=llm, prompt=prompt, output_parser=StrOutputParser())
    return definition_chain.run(term)

# Function to parse a case description
def parse_case(case_description):
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0.7, openai_api_key=OPENAI_API_KEY, max_tokens=500)
    case_prompt = PromptTemplate.from_template("Extract details from the case description: {case_description}")
    case_parser = PydanticOutputParser(pydantic_object=CaseRecord)
    case_chain = LLMChain(llm=llm, prompt=case_prompt, output_parser=case_parser)
    output = case_chain.run({"case_description": case_description})
    return json.loads(output.json())

# Function to add case details to Google Sheets
def add_to_google_sheets(case_dict):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.metadata.readonly"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        case_sheet = client.open("2024 Healthtech Identify Log").worksheet("Case Log")
        headers = case_sheet.row_values(1)
        row_to_append = [case_dict.get(header, "") for header in headers]
        case_sheet.append_row(row_to_append)
        return True
    except Exception as e:
        st.error(f"Error adding to Google Sheets: {e}")
        return False

# Embed case into Pinecone and update glossary
def embed_case(attendees, case_description, case_title, case_date, case_ID):
    db = PineconeVectorStore(index_name=st.secrets["pinecone-keys"]["index_to_connect"], namespace="cases", 
                             embedding=OpenAIEmbeddings(api_key=OPENAI_API_KEY),
                             pinecone_api_key=st.secrets["pinecone-keys"]["api_key"])
    
    db.add_texts([case_description], metadatas=[{'attendees': attendees, 'case_date': case_date, 'case_ID': case_ID}])
    parsed_case = parse_case(case_description) if 'parsed_case' not in st.session_state else st.session_state['parsed_case']
    case_dict = {
        "Title": case_title,
        "Case Description": case_description,
        "Date": case_date,
        "Case ID": case_ID,
        "Attendees": ', '.join(attendees),
        **parsed_case
    }
    return add_to_google_sheets(case_dict)

# Generate case summary
def generate_case_summary(case_description):
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0.7, openai_api_key=OPENAI_API_KEY, max_tokens=500)
    case_prompt = PromptTemplate.from_template("Create a brief title for the following case description: {case_description}")
    case_chain = LLMChain(llm=llm, prompt=case_prompt, output_parser=StrOutputParser())
    return case_chain.run(case_description)

# Streamlit UI logic for adding or editing cases (truncated for brevity)
# Refer to the original code for detailed UI implementation
