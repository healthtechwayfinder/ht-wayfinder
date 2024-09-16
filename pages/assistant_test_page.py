import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from openai import OpenAI
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.agents.openai_assistant import OpenAIAssistantRunnable #added
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain.callbacks import get_openai_callback
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnableLambda
from langchain.prompts import PromptTemplate
from langchain_pinecone import PineconeVectorStore

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

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


# Google Sheets setup
SCOPE = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
CREDS = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPE)
CLIENT = gspread.authorize(CREDS)
SPREADSHEET = CLIENT.open("Observation Investigator - Chat Log")  # Open the main spreadsheet



def create_new_chat_sheet():
    """Create a new sheet for the current chat thread."""
    chat_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Unique name based on timestamp
    sheet = SPREADSHEET.add_worksheet(title=f"Chat_{chat_timestamp}", rows="1", cols="2")  # Create new sheet
    sheet.append_row(["User Input", "Assistant Response"])  # Optional: Add headers
    return sheet

# # Create a new sheet for the chat thread if not already created
if "chat_sheet" not in st.session_state:
    st.session_state.chat_sheet = create_new_chat_sheet()

OPENAI_API_KEY = st.secrets["openai_key"]
assistant_ID = 'asst_Qatnn7dh8SW5FeFCzbtuXmxt'

st.set_page_config(page_title="Observation Investigator", page_icon="❓")

st.markdown("""
    <style>
    div.stButton > button {
        background-color: #a51c30;
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

# st.markdown("# Observation Investigator")
# st.write("Use this tool to find relationships between cases, summarize elements in observations, and plan for future observations.")
# # Subtitle for the chat section

# agent = OpenAIAssistantRunnable(assistant_id="<asst_Qatnn7dh8SW5FeFCzbtuXmxt>", as_agent=True)

# llm = ChatOpenAI(
#     # model_name="gpt-4o",
#     temperature=0.7,
#     openai_api_key=OPENAI_API_KEY,
#     max_tokens=500,
#     assistant_id='asst_Qatnn7dh8SW5FeFCzbtuXmxt',
# )

# interpreter_assistant = OpenAIAssistantRunnable.create_assistant(
#     name="langchain assistant",
#     instructions="You are a personal math tutor. Write and run code to answer math questions.",
#     tools=[{"type": "code_interpreter"}],
#     model="gpt-4-1106-preview",
# # )
# output = llm.invoke({"content": "What's 10 - 4 raised to the 2.7"})
# output

agent = OpenAIAssistantRunnable(client=OpenAI(api_key=OPENAI_API_KEY), assistant_id=assistant_id, as_agent=True)







