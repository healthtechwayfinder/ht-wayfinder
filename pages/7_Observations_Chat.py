import streamlit as st
from streamlit_extras.switch_page_button import switch_page


from langchain_openai import ChatOpenAI, OpenAIEmbeddings
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
SPREADSHEET = CLIENT.open("2024 Healthtech Identify Log")  # Open the main spreadsheet

def create_new_chat_sheet():
    """Create a new sheet for the current chat thread."""
    chat_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")  # Unique name based on timestamp
    sheet = SPREADSHEET.add_worksheet(title=f"Chat_{chat_timestamp}", rows="1", cols="2")  # Create new sheet
    sheet.append_row(["User Input", "Assistant Response"])  # Optional: Add headers
    return sheet

# # Create a new sheet for the chat thread if not already created
# if "chat_sheet" not in st.session_state:
#     st.session_state.chat_sheet = create_new_chat_sheet()

OPENAI_API_KEY = st.secrets["openai_key"]

st.set_page_config(page_title="Ask Observations", page_icon="❓")

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

st.markdown("# Ask the Team's Observations")

# st.write("This is the Ask the Team's Observations page.")
# Subtitle for the chat section

if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

llm = ChatOpenAI(
    model_name="gpt-4o",
    temperature=0.7,
    openai_api_key=OPENAI_API_KEY,
    max_tokens=500,
)


def refresh_observations_db():
    db = PineconeVectorStore(
        index_name=st.secrets["pinecone-keys"]["index_to_connect"],
        namespace="observations",
        embedding=OpenAIEmbeddings(api_key=OPENAI_API_KEY),
        pinecone_api_key=st.secrets["pinecone-keys"]["api_key"],
    )
    return db

def refresh_cases_db():
    db = PineconeVectorStore(
        index_name=st.secrets["pinecone-keys"]["index_to_connect"],
        namespace="cases",
        embedding=OpenAIEmbeddings(api_key=OPENAI_API_KEY),
        pinecone_api_key=st.secrets["pinecone-keys"]["api_key"],
    )
    return db

def get_observation_sheet_as_dict():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    observation_sheet = client.open("2024 Healthtech Identify Log").worksheet("Observation Log")
    data = observation_sheet.get_all_records()
    return data

def get_case_sheet_as_dict():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    case_sheet = client.open("2024 Healthtech Identify Log").worksheet("Case Log")
    data = case_sheet.get_all_records()
    return data

def get_case_descriptions_from_case_ids(case_ids):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    case_sheet = client.open("2024 Healthtech Identify Log").worksheet("Case Log")
    data = case_sheet.get_all_records()

    cases = {}
    for case in data:
        if case['Case ID'] in case_ids:
            cases[case['Case ID']] = case['Case Description']

    return cases

# if 'observation_google_sheet' not in st.session_state:
#     st.session_state['observation_google_sheet'] = get_observation_sheet_as_dict()

# if 'case_google_sheet' not in st.session_state:
#     st.session_state['case_google_sheet'] = get_case_sheet_as_dict()

# Handle new input
if prompt := st.chat_input("What would you like to ask?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Perform similarity search using Pinecone
    updated_observations_db = refresh_observations_db()
    related_observations = updated_observations_db.similarity_search(prompt, k=10)
    # related_observations = st.session_state['observation_google_sheet'] # Placeholder for now
    print(related_observations)

    # get case ids from metadata of related observations
    case_ids = []
    for observation in related_observations:
        if 'case_id' in observation.metadata:
            case_ids.append(observation.metadata['case_id'])

    print("Fetching case descriptions for case ids: ", case_ids)
    related_cases = get_case_descriptions_from_case_ids(case_ids)
    print(related_cases)

    updated_cases_db = refresh_cases_db()
    related_cases_similarity = updated_cases_db.similarity_search(prompt, k=4)


    question_prompt = PromptTemplate.from_template(
          """
        You are a helpful assistant trained in the Stanford Biodesign process that can answer questions about given observations of health care procedures. 
        You have to use the set of observations and the relevant cases to help answer the question. Cite the relevant observations with relevant quotes and observation IDs to back your answer.
        There might be repeated observations or repeated cases in the set, consider them as the same observation or case.

        Question: {question}
        Set of Observations: {related_observations}
        Relevant Cases linked to Observations:{related_cases}
        Semantailcally Relevant cases: {related_cases_similarity}
        Final Answer:
         """
    )
    
    observation_chat_chain = (
        question_prompt | llm | StrOutputParser()
    )

    with get_openai_callback() as cb:
        output = observation_chat_chain.invoke({"question": prompt, 
                                                "related_observations": related_observations,
                                                "related_cases": related_cases,
                                                "related_cases_similarity": related_cases_similarity},)

    # Update the conversation history
    st.session_state.messages.append({"role": "assistant", "content": output})

    # Display the response
    with st.chat_message("assistant"):
        st.markdown(output)
        # st.markdown("---")
        # st.markdown("### Related Observations")
        # for i, observation in enumerate(related_observations):
        #     st.write(f"{i+1}. {observation}")

    # Store chat in the current sheet
    # st.session_state.chat_sheet.append_row([st.session_state.messages[-2]['content'], st.session_state.messages[-1]['content']])

# st.markdown("---")
# if st.button("Back to Main Menu"):
#     switch_page("main_menu")

st.markdown("---")

# Spacer to push the button to the bottom

# Add a spacer to push the button to the bottom of the page
st.write(" " * 50)
# Apply custom CSS to make the button blue
st.markdown("""
    <style>
    div.stButton > button {
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


button_place = st.empty()

# Your other code here...

# Populate the reserved place with the button
if button_place.button("Back to Dashboard"):
    switch_page("Dashboard")

# # Create a button using Streamlit's native functionality
# if st.button("Back to Main Menu"):
#     switch_page("main_menu")
