import time
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from datetime import date
import logging
logging.basicConfig(level=logging.INFO)

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
import pandas as pd

st.set_page_config(page_title="Create a New Need Statement", page_icon=":pencil2:")
st.markdown("# Create a New Need Statement")
st.write("Use this tool to record needs as you draft them. Select the date that the need was generated, and a unique identifier will auto-populate. In the next box, select all related observations.")
st.write("Start by outlining the problem, population, and outcome, and then enter the whole statement in the corresponding text box. In the last box, add any relevant notes -- things like how you might want to workshop the statement, specific insights, assumptions in the statement that need validation, or opportunities for improvement or more research.")

OPENAI_API_KEY = st.secrets["openai_key"]

# Access the credentials from Streamlit secrets
creds_dict = {
    "type": st.secrets["gwf_service_account"]["type"],
    "project_id": st.secrets["gwf_service_account"]["project_id"],
    "private_key_id": st.secrets["gwf_service_account"]["private_key_id"],
    "private_key": st.secrets["gwf_service_account"]["private_key"].replace('\\n', '\n'),  # Fix formatting
    "client_email": st.secrets["gwf_service_account"]["client_email"],
    "client_id": st.secrets["gwf_service_account"]["client_id"],
    "auth_uri": st.secrets["gwf_service_account"]["auth_uri"],
    "token_uri": st.secrets["gwf_service_account"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["gwf_service_account"]["client_x509_cert_url"],
    "universe_domain": st.secrets["gwf_service_account"]["universe_domain"],
}

# Function to get Google Sheets connection
def get_google_sheet(sheet_name, worksheet_name):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).worksheet(worksheet_name)
    return sheet

# New function for getting observation IDs
def getExistingObsIDS():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
    ])
    client = gspread.authorize(creds)
    obs_log = client.open("2024 Healthtech Identify Log").worksheet("Observation Log")
    obs_ids = obs_log.col_values(1)[1:]  # Observation IDs
    obs_titles = obs_log.col_values(2)[1:]  # Observation titles
    
    # Combine IDs and titles for display
    existing_obs_ids_with_title = [f"{obs_id} - {obs_title}" for obs_id, obs_title in zip(obs_ids, obs_titles)]
    return existing_obs_ids_with_title

# Function to display the selected observations
def display_selected_observations(selected_obs_ids):
    obs_log = get_google_sheet("2024 Healthtech Identify Log", "Observation Log")
    df = pd.DataFrame(obs_log.get_all_records())

    # Iterate over all selected Observation IDs and display the corresponding description
    for obs_id in selected_obs_ids:
        clean_obs_id = obs_id.split(" - ")[0]  # Extract only the Observation ID
        selected_observation = df[df['Observation ID'] == clean_obs_id]
        if not selected_observation.empty:
            observation_description = selected_observation.iloc[0]['Observation Description']
            st.markdown(f"### {clean_obs_id} Description:\n{observation_description}")
        else:
            st.info(f"No description available for {obs_id}.")

# prepare list of observations and allow user to pick multiple
existing_obs_ids_with_title = getExistingObsIDS()
st.session_state['obs_ids_with_title'] = st.multiselect("Related Observation IDs", existing_obs_ids_with_title)

# If any observation IDs are selected, display their descriptions
if st.session_state['obs_ids_with_title']:
    display_selected_observations(st.session_state['obs_ids_with_title'])

# Columns for date and need ID
col1, col2 = st.columns(2)

# Need Date
with col1:
    st.date_input("Need Date", date.today(), key="need_date")

# Need ID
with col2:
    if 'need_ID' not in st.session_state:
        # Generate a need ID once the page is loaded
        st.session_state['need_ID'] = f"NS{date.today().strftime('%y%m%d')}0001"
    st.text_input("Need ID (auto-generated):", value=st.session_state['need_ID'], disabled=True)

# Create the form
with st.form("my_form"):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.text_input("Problem:", key="problem")

    with col2:
        st.text_input("Population:", key="population")

    with col3:
        st.text_input("Outcome:", key="outcome")

    st.text_input("Need Statement:", key="need_statement")
    st.text_input("Notes:", key="notes")
    
    submitted = st.form_submit_button("Submit", on_click=submit_form)


    # Form submit button
    # submitted = st.form_submit_button("Submit")

    if submitted:
        st.write('<p style="color:green;">Need statement recorded!</p>', unsafe_allow_html=True)

# Back to Dashboard button
if st.button("Back to Dashboard"):
    switch_page("Dashboard")
























# import streamlit as st
# from streamlit_extras.switch_page_button import switch_page

# from openai import OpenAI
# from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# from langchain.agents.openai_assistant import OpenAIAssistantRunnable #added
# from langchain.chains import LLMChain
# from langchain_community.callbacks.manager import get_openai_callback
# from langchain.output_parsers import PydanticOutputParser
# from langchain.callbacks import get_openai_callback
# from langchain.schema import StrOutputParser
# from langchain.schema.runnable import RunnableLambda
# from langchain.prompts import PromptTemplate
# from langchain_pinecone import PineconeVectorStore

# import gspread
# from oauth2client.service_account import ServiceAccountCredentials
# from datetime import datetime

# # Access the credentials from Streamlit secrets
# creds_dict = {
#     "type" : st.secrets["gwf_service_account"]["type"],
#     "project_id" : st.secrets["gwf_service_account"]["project_id"],
#     "private_key_id" : st.secrets["gwf_service_account"]["private_key_id"],
#     "private_key" : st.secrets["gwf_service_account"]["private_key"],
#     "client_email" : st.secrets["gwf_service_account"]["client_email"],
#     "client_id" : st.secrets["gwf_service_account"]["client_id"],
#     "auth_uri" : st.secrets["gwf_service_account"]["auth_uri"],
#     "token_uri" : st.secrets["gwf_service_account"]["token_uri"],
#     "auth_provider_x509_cert_url" : st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
#     "client_x509_cert_url" : st.secrets["gwf_service_account"]["client_x509_cert_url"],
#     "universe_domain": st.secrets["gwf_service_account"]["universe_domain"],
# }


# # Google Sheets setup
# SCOPE = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.metadata.readonly"
#         ]
# CREDS = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
# CLIENT = gspread.authorize(CREDS)
# SPREADSHEET = CLIENT.open("Observation Investigator - Chat Log")  # Open the main spreadsheet



# def create_new_chat_sheet():
#     """Create a new sheet for the current chat thread."""
#     chat_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Unique name based on timestamp
#     sheet = SPREADSHEET.add_worksheet(title=f"Chat_{chat_timestamp}", rows="1", cols="2")  # Create new sheet
#     sheet.append_row(["User Input", "Assistant Response"])  # Optional: Add headers
#     return sheet

# # # Create a new sheet for the chat thread if not already created
# if "chat_sheet" not in st.session_state:
#     st.session_state.chat_sheet = create_new_chat_sheet()

# OPENAI_API_KEY = st.secrets["openai_key"]
# assistant_ID = 'asst_Qatnn7dh8SW5FeFCzbtuXmxt'

# st.set_page_config(page_title="Observation Investigator", page_icon="❓")

# st.markdown("""
#     <style>
#     div.stButton > button {
#         background-color: #a51c30;
#         color: white;
#         font-size: 16px;
#         padding: 10px 20px;
#         border: none;
#         border-radius: 5px;
#     }
#     div.stButton > button:hover {
#         background-color: #2c4a70;
#         color: white;
#     }
#     </style>
#     """, unsafe_allow_html=True)

# # st.markdown("# Observation Investigator")
# # st.write("Use this tool to find relationships between cases, summarize elements in observations, and plan for future observations.")
# # # Subtitle for the chat section

# # agent = OpenAIAssistantRunnable(assistant_id="<asst_Qatnn7dh8SW5FeFCzbtuXmxt>", as_agent=True)

# # llm = ChatOpenAI(
# #     # model_name="gpt-4o",
# #     temperature=0.7,
# #     openai_api_key=OPENAI_API_KEY,
# #     max_tokens=500,
# #     assistant_id='asst_Qatnn7dh8SW5FeFCzbtuXmxt',
# # )

# # interpreter_assistant = OpenAIAssistantRunnable.create_assistant(
# #     name="langchain assistant",
# #     instructions="You are a personal math tutor. Write and run code to answer math questions.",
# #     tools=[{"type": "code_interpreter"}],
# #     model="gpt-4-1106-preview",
# # # )
# # output = llm.invoke({"content": "What's 10 - 4 raised to the 2.7"})
# # output

# # agent = OpenAIAssistantRunnable(client=OpenAI(api_key=OPENAI_API_KEY), assistant_id=assistant_id, as_agent=True)



# # from openai import OpenAI
# client = OpenAI()

# assistant = client.beta.assistants.create(
#   name="Math Tutor",
#   instructions="You are a personal math tutor. Write and run code to answer math questions.",
#   tools=[{"type": "code_interpreter"}],
#   model="gpt-4o",
# )

# thread = client.beta.threads.create()

# message = client.beta.threads.messages.create(
#   thread_id=thread.id,
#   role="user",
#   content="I need to solve the equation `3x + 11 = 14`. Can you help me?"
# )


# run = client.beta.threads.runs.create_and_poll(
#   thread_id=thread.id,
#   assistant_id=assistant_ID,
#   instructions="Please address the user as Jane Doe. The user has a premium account."
# )

# if run.status == 'completed': 
#   messages = client.beta.threads.messages.list(
#     thread_id=thread.id
#   )
#   print(messages)
# else:
#   print(run.status)





