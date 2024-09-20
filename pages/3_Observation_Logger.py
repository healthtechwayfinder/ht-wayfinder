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
from streamlit_tags import st_tags

import gspread
from oauth2client.service_account import ServiceAccountCredentials


from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

import json
import os
import csv

st.set_page_config(page_title="Add a New Observation", page_icon="🔍")

st.markdown("# Observation Logger")
# Add a title for choosing an action
# Add a slightly smaller title with reduced space after
st.markdown("""
    <style>
    h4 {
        margin-bottom: 0rem;  /* No margin below the title */
        padding-bottom: 0rem; /* No padding below the title */
    }
    div[data-baseweb="select"] {
        margin-top: 0rem; /* No margin above the dropdown */
        padding-top: 0rem; /* No padding above the dropdown */
    }
    </style>
    <h3>Choose an action</h3>
    """, unsafe_allow_html=True)


# Dropdown menu for selecting action
action = st.selectbox("", ["Add New Observation", "Edit Existing Observation"], label_visibility="collapsed")



observations_csv = "observations.csv"
OPENAI_API_KEY = st.secrets["openai_key"]

# Access the credentials from Streamlit secrets
#test
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
if 'parsed_observation' not in st.session_state:
    st.session_state['parsed_observation'] = ""

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

# Initialize session state for selected_observation if it doesn't exist
if "selected_observation" not in st.session_state:
    st.session_state["selected_observation"] = ""  # Set initial value to an empty string

def get_google_sheet(spreadsheet_name, worksheet_name):
    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(spreadsheet_name).worksheet(worksheet_name)
    return sheet


# Fetch case IDs and titles from Google Sheets
def fetch_observation_ids_and_titles():
    try:
        sheet = get_google_sheet("2024 Healthtech Identify Log", "Observation Log")  # Ensure this is correct
        data = sheet.get_all_records()
        # Create a list of tuples with (case_id, title)
        observation_info = [(row["Observation ID"], row["Observation Title"]) for row in data if "Observation ID" in row and "Observation Title" in row]
        return observation_info
    except Exception as e:
        print(f"Error fetching Observation IDs and titles: {e}")
        return []

# Sample function to simulate fetching observation details from Google Sheets
def fetch_observation_details(observation_id):
    sheet = get_google_sheet("2024 Healthtech Identify Log", "Observation Log")
    data = sheet.get_all_records()
    # # Print the data being fetched
    # st.write(data)
    for row in data:
        if "Observation ID" in row and row["Observation ID"].strip() == observation_id.strip():
            return row
    st.error(f"Observation ID {observation_id} not found.")
    
    return None




def generateObservationTags(observation):
    # Create the LLM model
    llm = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0.7,
        openai_api_key=OPENAI_API_KEY,
        max_tokens=100,
    )

    # Define the prompt for generating tags from the observation text
    observation_tags_prompt = PromptTemplate.from_template(
        """
        Generate a list of 3-5 tags (only nouns) that are very relevant to the medical observation. The tags can be used to identify the type of procedure: (invasive procedure, minimally invasive, open procedure, non invasive, in the clinic, in the OR, in the emergency room..) the medical specialty (e.g.: rhynology, oncology, ophtalmology,..)  area of medicine, or type of technology being used for example Do not use numbers and separate them by commas.
        Give only the list of tags without any quotes or special characters.

        Observation: {observation}
        Tags:
        """
    )

    # Chain together the prompt and the LLM for generating tags
    observation_chain = (
        observation_tags_prompt | llm | StrOutputParser()
    )

    # Generate the tags using the LLM
    output = observation_chain.invoke({"observation": observation})

    # Return the generated tags
    return output



class ObservationRecord(BaseModel):
    stakeholders: Optional[str] = Field(default=None, description="Stakeholders involved in the healthcare event like a Patient, Care Partner, Advocacy & Support, Patient Advocacy Group, Patient Family, Patient Caretaker, Direct Patient Care Provider, Geriatrician, Chronic Disease Management Specialist, Cognitive Health Specialist, Psychologist, Psychiatrist, Nutritionist, Trainer, Physical Therapist, Occupational Therapist, End-of-Life / Palliative Care Specialist, Home Health Aide, Primary Care Physician, Social Support Assistant, Physical Therapist, Pharmacist, Nurse, Administrative & Support, Primary Care Physician, Facility Administrators, Nursing Home Associate, Assisted Living Facility Associate, Home Care Coordinator, Non-Healthcare Professional, Payer and Regulators, Government Official, Advocacy & Support, Professional Society Member, ...")
    sensory_observations: Optional[str] = Field(default=None, description="What is the observer sensing with sight, smell, sound, touch. e.g. sights, noises, textures, scents, ...")
    product_interactions: Optional[str] = Field(default=None, description="How is equipment and technology being used, engaged with, adjusted, or moved at this moment? what is missing?")
    process_actions: Optional[str] = Field(default=None, description="specific step or task that is taken within a larger workflow or process to achieve a particular goal or outcome. In the context of biodesign or healthcare, a process action could involve any number of operations that contribute to the diagnosis, treatment, or management of a patient, or the development and deployment of medical technologies..")
    insider_language: Optional[str] = Field(default=None, description="Terminology used that is specific to this medical practice or procedure. e.g. specific words or phrases ...")
   

def parseObservation(observation: str):
    llm = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0.7,
        openai_api_key=OPENAI_API_KEY,
        max_tokens=500,
    )

    observation_prompt = PromptTemplate.from_template(
"""
You help me parse observations of medical procedures to extract details such as  surgeon, procedure and date, whichever is available.
Format Instructions for output: {format_instructions}

Observation: {observation}
Output:"""
)
    observationParser = PydanticOutputParser(pydantic_object=ObservationRecord)
    observation_format_instructions = observationParser.get_format_instructions()

    observation_chain = (
        observation_prompt | llm | observationParser
    )

    # with get_openai_callback() as cb:
    output = observation_chain.invoke({"observation": observation, "format_instructions": observation_format_instructions})

    return json.loads(output.json())

def extractObservationFeatures(observation):

    # Parse the observation
    parsed_observation = parseObservation(observation)
    st.session_state['parsed_observation'] = parsed_observation

    input_fields = list(ObservationRecord.__fields__.keys())

    missing_fields = [field for field in input_fields if parsed_observation[field] is None]

    output = ""

    for field in input_fields:
        if field not in missing_fields:
            key_output = field.replace("_", " ").capitalize()
            output += f"**{key_output}**: {parsed_observation[field]}\n"
            output += "\n"

    missing_fields = [field.replace("_", " ").capitalize() for field in missing_fields]

    if len(missing_fields) > 0:
        output += "\n\n **Missing fields**:"
        for field in missing_fields:
            output += f" <span style='color:red;'>{field}</span>,"
    
    return f"{output}"



# Function to add the observation (including tags) to Google Sheets
def addToGoogleSheets(observation_dict):
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        observation_sheet = client.open("2024 Healthtech Identify Log").worksheet("Observation Log")

        headers = observation_sheet.row_values(1)
        headers = [i.strip() for i in headers]

        # Prepare the row data matching the headers
        row_to_append = []
        for header in headers:
            if header in observation_dict:
                value = observation_dict[header]
                if value is None:
                    row_to_append.append("")
                else:
                    row_to_append.append(str(observation_dict[header]))
            else:
                row_to_append.append("")  # Leave cell blank if header not in dictionary

        # Append the row to the sheet
        observation_sheet.append_row(row_to_append)
        return True
    except Exception as e:
        print("Error adding to Google Sheets: ", e)
        return False

# Function to update the "observations" column for a specific case ID in Google Sheets
import logging

# Function to update the "observations" column for a specific case ID in Google Sheets
import logging

# Function to update the "Observations" column for a specific case ID in Google Sheets
def update_case_observations(case_id, observation_id):
    try:
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        case_log = client.open("2024 Healthtech Identify Log").worksheet("Case Log")

        # Get all data from the sheet
        data = case_log.get_all_records()

        # Get the header row to find the "Observations" column
        headers = case_log.row_values(1)
        
        # Check if 'Observations' column exists in the sheet headers (case-sensitive)
        if "Observations" not in headers:
            logging.error("'Observations' column not found in the sheet headers")
            return False
        
        # Find the index of the "Observations" column (1-based index for gspread)
        obs_col_index = headers.index("Observations") + 1  # 'Observations' column

        # Log headers and column index
        logging.info(f"Headers: {headers}")
        logging.info(f"'Observations' column index: {obs_col_index}")

        # Find the row that corresponds to the given case_id
        for i, row in enumerate(data, start=2):  # Start from row 2 to skip the header row
            logging.info(f"Checking row {i}: {row}")
            if row["Case ID"] == case_id:
                logging.info(f"Found matching case ID: {case_id} at row {i}")
                
                # Get the current observations in the "Observations" column (if any)
                current_observations = row.get("Observations", "")
                
                # Append the new observation ID to the existing observations
                if current_observations:
                    updated_observations = f"{current_observations}, {observation_id}"
                else:
                    updated_observations = observation_id

                # Log the update before writing
                logging.info(f"Updating row {i}, column {obs_col_index} with: {updated_observations}")

                # Update the "Observations" column with the new value
                case_log.update_cell(i, obs_col_index, updated_observations)
                return True

        logging.warning(f"Case ID {case_id} not found in the case log")
        return False
    except Exception as e:
        logging.error(f"Error updating case Observations: {e}")
        return False

# Function to append an Observation ID to the "Observations" column in the Case Log worksheet
def append_observation_to_case(case_log_sheet, case_id, new_observation_id):
    # Get all data from the Case Log sheet
    all_data = case_log_sheet.get_all_values()
    
    # Find the index of the columns
    headers = all_data[0]
    case_id_col_index = headers.index('Case ID') + 1  # Convert to 1-based index for gspread
    observations_col_index = headers.index('Observations') + 1  # Convert to 1-based index
    
    # Find the row with the matching Case ID
    for i, row in enumerate(all_data[1:], start=2):  # Start at 2 because row 1 is headers
        if row[headers.index('Case ID')] == case_id:
            # Get the existing observations (if any)
            existing_observations = row[headers.index('Observations')]
            if existing_observations:
                existing_observations_list = [obs.strip() for obs in existing_observations.split(",") if obs.strip()]
            else:
                existing_observations_list = []
            
            # Check if the new Observation ID already exists
            if new_observation_id not in existing_observations_list:
                # Append the new Observation ID to the list
                updated_observations = existing_observations_list + [new_observation_id]
                
                # Update the cell in Google Sheets with the new value
                case_log_sheet.update_cell(i, observations_col_index, ", ".join(updated_observations))
                st.success(f"Observation ID '{new_observation_id}' has been added to Case ID '{case_id}'.")
            else:
                st.info(f"Observation ID '{new_observation_id}' already exists for Case ID '{case_id}'.")
            return
    st.error(f"Case ID '{case_id}' not found in the Case Log.")



# Modified function to embed the observation and tags
def embedObservation(observer, observation, observation_summary, observation_tags, observation_date, observation_id, related_case_id_with_title):
    # Extract only the case ID (before the hyphen)
    related_case_id = related_case_id_with_title.split(" - ")[0]
    
    db = PineconeVectorStore(
        index_name=st.secrets["pinecone-keys"]["index_to_connect"],
        namespace="observations",
        embedding=OpenAIEmbeddings(api_key=OPENAI_API_KEY),
        pinecone_api_key=st.secrets["pinecone-keys"]["api_key"],
    )

    # Add observation with metadata, including tags
    db.add_texts([observation], metadatas=[{
        'observer': observer,
        'observation_date': observation_date,
        'observation_id': observation_id,
        'tags': observation_tags,  # Add tags to the metadata
        'case_id': related_case_id
    }])

    print("Added to Pinecone: ", observation_id)

    # if 'parsed_observation' not in st.session_state:
    #     st.session_state['parsed_observation'] = parseObservation(observation)
    # else:
    #     parsed_observation = st.session_state['parsed_observation']


    if 'parsed_observation' in st.session_state and len(st.session_state['parsed_observation'])>0:
        parsed_observation = st.session_state['parsed_observation']
    else:
        parsed_observation = parseCase(observation)
        st.session_state['parsed_observation'] = parsed_observation
    

    # Prepare the observation record with the tags
    observation_keys = list(ObservationRecord.__fields__.keys())
    observation_keys_formatted = [i.replace("_", " ").title() for i in observation_keys]
    all_observation_keys = ['Observation Title', 'Observer', 'Observation Description', 'Tags', 'Date', 'Observation ID', 'Related Case ID'] + observation_keys_formatted
    observation_values = [observation_summary, observer, observation, observation_tags, observation_date, observation_id, related_case_id] + [parsed_observation[key] for key in observation_keys]

    observation_dict = dict(zip(all_observation_keys, observation_values))

    # Add the observation record (including tags) to Google Sheets
    status = addToGoogleSheets(observation_dict)
    print("Added to Google Sheets: ", status)

    # If the observation was successfully added to Google Sheets, update the "Case Log"
    if status:
        # Call the function to append the observation ID to the corresponding case in the "Case Log"
        update_case_observations(related_case_id, observation_id)

    return status



def generateObservationSummary(observation):

    llm = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0.7,
        openai_api_key=OPENAI_API_KEY,
        max_tokens=500,
    )


    observation_prompt = PromptTemplate.from_template(
"""
You help me by giving me the a 3-8 word title of the following medical observation. Do not use quotes or special characters.

Observation: {observation}
Output Title:"""
)

    observation_chain = (
        observation_prompt | llm | StrOutputParser()
    )

    # with get_openai_callback() as cb:
    output = observation_chain.invoke({"observation": observation})

    return output


def clear_observation():
    # if 'observation' in st.session_state:
    #     st.session_state['observation'] = ""
    # if 'observation_summary' in st.session_state:
    #     st.session_state['observation_summary'] = ""
    # if 'result' in st.session_state:
    #     st.session_state['result'] = ""
    # if 'observation_tags' in st.session_state:
    #     st.session_state['observation_tags'] = ""
    # if 'observer' in st.session_state:
    #     st.session_state['observer'] = ""
    # if 'sensory_observations' in st.session_state:
    #     st.session_state['sensory_observations'] = ""
    # if 'stakeholders' in st.session_state:
    #     st.session_state['stakeholders'] = ""
    # if 'product_interactions' in st.session_state:
    #     st.session_state['product_interactions'] = ""
    # if 'insider_language' in st.session_state:
    #     st.session_state['insider_language'] = ""
    # if 'process_actions' in st.session_state:
    #     st.session_state['process_actions'] = ""    
    parsed_observation = ""
    update_observation_id()

import streamlit as st
from datetime import date

# Initialize or retrieve the observation counters dictionary from session state
if 'observation_counters' not in st.session_state:
    st.session_state['observation_counters'] = {}

    

# Function to generate observation ID with the format OBYYMMDDxxxx
def generate_observation_id(observation_date, counter):
    return f"OB{observation_date.strftime('%y%m%d')}{counter:04d}"

# Function to update observation ID when the date changes
def update_observation_id():
    obs_date_str = st.session_state['observation_date'].strftime('%y%m%d')

    # get all observation ids from the sheets and update the counter
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    observation_sheet = client.open("2024 Healthtech Identify Log").worksheet("Observation Log")
    column_values = observation_sheet.col_values(1) 

    # find all observation ids with the same date
    obs_date_ids = [obs_id for obs_id in column_values if obs_id.startswith(f"OB{obs_date_str}")]
    obs_date_ids.sort()

    # get the counter from the last observation id
    if len(obs_date_ids) > 0:
        counter = int(obs_date_ids[-1][-4:])+1
    else:
        counter = 1
   
    st.session_state['observation_id'] = generate_observation_id(st.session_state['observation_date'], counter)


def getExistingCaseIDS():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    case_log = client.open("2024 Healthtech Identify Log").worksheet("Case Log")
    case_ids = case_log.col_values(1)[1:]
    case_dates_list = case_log.col_values(3)[1:]
    case_titles = case_log.col_values(2)[1:]

    # find all observation ids with the same date
    existing_case_ids_with_title = dict(zip(case_ids, case_titles))

    # make strings with case id - title
    existing_case_ids_with_title = [f"{case_id} - {case_title}" for case_id, case_title in existing_case_ids_with_title.items()]

    print("Existing Case IDS: ")
    print(existing_case_ids_with_title)
    return existing_case_ids_with_title


 #Function to get the date of the selected case from Google Sheets
def get_case_date(case_id_with_title):
    # Extract the case ID from the selected case (before the hyphen)
    case_id = case_id_with_title.split(" - ")[0]

    try:
        # Define Google API scope and credentials
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        
        # Open the case log sheet
        case_log = client.open("2024 Healthtech Identify Log").worksheet("Case Log")

        # Fetch all case data
        case_data = case_log.get_all_records()

        # Loop through the rows and find the case with the matching Case ID
        for row in case_data:
            if row.get('Case ID') == case_id:
                case_date_str = row.get('Date')  # Check if 'Date' exists
                if case_date_str:
                    try:
                        case_date = datetime.strptime(case_date_str, '%Y-%m-%d').date()  # Adjust date format if needed
                        return case_date
                    except ValueError:
                        logging.error(f"Invalid date format for case ID {case_id}: {case_date_str}")
                        return None
                else:
                    logging.warning(f"No date found for case ID {case_id}")
                    return None

    except gspread.exceptions.APIError as api_err:
        logging.error(f"API error while fetching case date: {api_err}")
        return None
    except Exception as e:
        logging.error(f"Error fetching case date: {e}")
        return None



# Function to update the observation date when a case ID is selected
def update_observation_date():
    # Retrieve the selected case ID and title from the session state
    case_id_with_title = st.session_state.get('selected_observation_id_with_title', '')

    # Ensure a case is selected (i.e., not an empty value)
    if case_id_with_title:
        case_date = get_case_date(case_id_with_title)  # Get the case date using your function
        if case_date:
            st.session_state['observation_date'] = case_date  # Update the observation date in session state
            update_observation_id()  # Ensure observation ID is updated when the date is updated


# If the user chooses "Add New Case"
if action == "Add New Observation":
    
    # Ensure observation_date is in session state
    if 'observation_date' not in st.session_state:
        st.session_state['observation_date'] = date.today()  # Default to today's date
    # Ensure observation_id is in session state
    if 'observation_id' not in st.session_state:
        update_observation_id()  # Initialize the observation ID
    
    
    existing_case_ids_with_title = getExistingCaseIDS()
    # case_id_with_title = st.selectbox("Related Case ID", [""] + existing_case_ids_with_title)
    
    # Selectbox for Related Case ID
    case_id_with_title = st.selectbox(
        "Select a Related Case ID",
        [""] + existing_case_ids_with_title,
        key='selected_observation_id_with_title',
        on_change=update_observation_date  # Call the update function only when a case ID is selected
    )
    
    
    # Use columns to place observation_date, observation_id, and observer side by side
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # st calendar for date input with a callback to update the observation_id
        #edit this to be the same as the case date
        # st.date_input("Observation Date", date.today(), on_change=update_observation_id, key="observation_date")
    
        # Display the observation date input and make it reflect session state
        st.date_input("Observation Date", value=st.session_state['observation_date'], key='observation_date', on_change=update_observation_id)
    
    
    with col2:
        # Ensure the observation ID is set the first time the script runs
        if 'observation_id' not in st.session_state:
            update_observation_id()
    
        # Display the observation ID
        st.text_input("Observation ID:", value=st.session_state['observation_id'], disabled=True)
    
    with col3:
        #Display Observer options 
        observer = st.selectbox("Observer", [""] + ["Deborah", "Kyle", "Ryan", "Lois"])
    
    
    # Initialize the observation text in session state if it doesn't exist
    if "observation" not in st.session_state:
        st.session_state["observation"] = ""
    
    # Function to clear the text area
    def clear_text():
        st.session_state["observation"] = ""
    
    # Add Your Observation Text with larger font size
    st.markdown("<h4 style='font-size:20px;'>Add Your Observation:</h4>", unsafe_allow_html=True)
    
    # Button for voice input (currently as a placeholder)
    if st.button("🎤 Record Observation (Coming Soon)"):
        st.info("Voice recording feature coming soon!")
    
    # Observation Text Area
    st.session_state['observation'] = st.text_area("Observation:", value=st.session_state["observation"], height=200)
    
    
    # Create columns to align the buttons
    col1, col2, col3 = st.columns([2, 2, 2])  # Adjust column widths as needed
    
    with col3:
        st.button("Clear Observation", on_click=clear_text)
        
        # Container for result display
        result_container = st.empty()
    
    
    
    with col1:
        if st.button("Evaluate Observation"):
            st.session_state['result'] = extractObservationFeatures(st.session_state['observation'])
            st.session_state['observation_summary']  = generateObservationSummary(st.session_state['observation'])
            # Generate tags for the observation
            st.session_state['observation_tags'] = generateObservationTags(st.session_state['observation'])
            
        
    if st.session_state['observation_summary'] != "":
        st.session_state['observation_summary'] = st.text_area("Generated Summary (editable):", value=st.session_state['observation_summary'], height=50)
    
    # here, add the function call to turn parsed results into editable text fields  
    
    parsed_observation = st.session_state['parsed_observation']
    
     # Ensure 'result' exists
    if isinstance(parsed_observation, dict):
        
        input_fields = list(ObservationRecord.__fields__.keys())
        # Find missing fields by checking if any field in parsed_observation is None or empty
        missing_fields = [field for field in input_fields if parsed_observation.get(field) in [None, ""]]
    
    
    
        for field in input_fields:
            if field not in missing_fields and field != "tags":
                field_clean = field.replace("_", " ").capitalize()
                st.session_state['parsed_observation'][field] = st.text_input(f'**{field_clean}**', key=field, value=st.session_state['parsed_observation'].get(field, ""))
    
            if field == "observation_tags":
                tags_values = parsed_observation.get('observation_tags', '')
                tags_values = [tag.strip() for tag in tags_values.split(",")]
                updated_tags = st_tags(
                    label="**Tags**",
                    text="Press enter to add more",
                    value=tags_values,  # Show the tags found in the result
                    maxtags=10,
                    key="tags_input"  # Unique key to ensure it's updated correctly
                )
                
                # Update tags_values with the modified tags from st_tags
                tags_values = updated_tags
                updated_tags_string = ", ".join(updated_tags)
                st.session_state['parsed_observation']['observation_tags'] = updated_tags_string
        
        if st.session_state.get('parsed_observation', '') != '':
            st.markdown("### Missing Fields")
            
            for field in missing_fields:
                field_clean = field.replace("_", " ").capitalize()
                st.session_state['parsed_observation'][field] = st.text_input(f'**{field_clean}**', key=field, value=st.session_state['parsed_observation'].get(field, ""))
    
    
    
    
    # # st.write(f":green[{st.session_state['result']}]")
    # # Display the generated tags in a text area (editable by the user if needed)
    # if st.session_state['observation_tags'] != "":
    #     st.session_state['observation_tags'] = st.text_area("Generated Tags (editable):", value=st.session_state['observation_tags'], height=50)
    
    st.markdown(st.session_state['result'], unsafe_allow_html=True)
    
    
    
    
    
    
    if st.button("Log Observation", disabled=st.session_state['observation_summary'] == ""):
        # st.session_state['observation_summary']  = generateObservationSummary(st.session_state['observation'])
        st.session_state["error"] = ""
    
        if st.session_state['observation'] == "":
            st.session_state["error"] = "Error! Please enter observation first"
            st.markdown(
                f"<span style='color:red;'>{st.session_state['error']}</span>", 
                unsafe_allow_html=True
            )
        elif st.session_state['observation_summary'] == "":
            st.session_state["error"] = "Error! Please evaluate observation first"
            st.markdown(
                f"<span style='color:red;'>{st.session_state['error']}</span>", 
                unsafe_allow_html=True
            )
        else:
            # update observation ID one last time to avoid accidental duplication with multiple users
            update_observation_id() 
            status = embedObservation(observer, st.session_state['observation'],  st.session_state['observation_summary'], 
                                st.session_state['observation_tags'],
                                st.session_state['observation_date'],
                                st.session_state['observation_id'],
                                case_id_with_title)
            clear_observation()
    
            # st.session_state['observation_summary'] = st.text_input("Generated Summary (editable):", value=st.session_state['observation_summary'])
            # "Generated Summary: "+st.session_state['observation_summary']+"\n\n"
            if status:
                st.session_state['result'] = "Observation added to your team's database."
                st.session_state['rerun'] = True
                st.rerun()
    
            else:
                st.session_state['result'] = "Error adding observation to your team's database, try again!"
            # clear_observation()
    
    # if st.session_state['rerun']:
    #     time.sleep(3)
    #     clear_observation()
    #     st.session_state['rerun'] = False
    #     st.rerun()
    
    
    st.markdown("---")
    
    
    # st.markdown("---")
    # Apply custom CSS to make the button blue
    # add a break line
    st.markdown("<br>", unsafe_allow_html=True)
    
    st.markdown("""
        <style>
        div.stButton > button {
            background-color: #A51C30;
            color: white;
            font-size: 16px;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
        }
        div.stButton > button:hover {
            background-color: #E7485F;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)
    
    
    
    # Create a button using Streamlit's native functionality
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.button("Back to Dashboard"):
        switch_page("Dashboard")

# If the user chooses "Add New Case"
elif action == "Edit Existing Observation":

    st.markdown("### Edit an Existing Observation")

    # Load existing observations from Google Sheets (or another source)
    observation_info = fetch_observation_ids_and_titles()  # Implement this function to load existing observation data
    
    # Ensure case_info is not empty
    if not observation_info:
        st.error("No observations found.")
    else:
        # Create a list of display names in the format "case_id: title"
        observation_options = [f"{observation_id}: {title}" for observation_id, title in observation_info]
        st.markdown("""
        <style>
        h4 {
            margin-bottom: 0.5rem;  /* No margin below the title */
            padding-bottom: 0.3rem; /* No padding below the title */
        }
        </style>
        <h4>Select an Observation to edit</h4>
        """, unsafe_allow_html=True)
        # Display the dropdown with combined case_id and title
        selected_observation = st.selectbox("", [""] + observation_options, key="selected_observation", label_visibility="collapsed")
        if selected_observation != "":
            # Extract the selected case_id from the dropdown (case_id is before the ":")
            observation_to_edit = selected_observation.split(":")[0].strip()
            observation_details = fetch_observation_details(observation_to_edit)
            if observation_details:
                st.write(f"Editing Observation ID: {observation_to_edit}")
                
                # # Loop through observation fields and display editable fields (except for Observation ID)
                # for field_name, field_value in observation_details.items():
                #     if field_name != "Observation ID":  # Ensure ID is not editable
                #         st.text_input(field_name, value=field_value, key=field_name)  # Editable text field
                # st.write(f"Editing Observation ID: {observation_to_edit}")
                
                observation_date_str = observation_details.get("Date", "")
                try:
                    observation_date = date.fromisoformat(observation_date_str) if observation_date_str else date.today()
                except ValueError:
                    observation_date = date.today()
                observation_date_input = st.date_input("Date", observation_date)
                
                observer_list = ["", "Deb", "Kyle", "Ryan", "Lois"]
                observer_value = str(observation_details.get("Observer", ""))  # Ensure observer_value is a string
                # Ensure the observer_value exists in the list, and get its index
                if observer_value in observer_list:
                    observer_index = observer_list.index(observer_value)
                else:
                    observer_index = 0  # Default to the first item if the value isn't in the list
                    
                observer = st.selectbox("Observer", observer_list , index=observer_index)
                observation_title = st.text_input("Title", observation_details.get("Observation Title", ""))
                observation_description = st.text_input("Description", observation_details.get("Observation Description", ""))
                # observation_stakeholders = st.text_input("Title", observation_details.get("Observation Title", ""))
                observation_stakeholders = st_tags(
                        label="Stakeholders:",
                        text="Press enter to add more",
                        value=observation_details.get("Stakeholders", "").split(",") if observation_details.get("Stakeholders") else [],  # Split tags into a list
                        suggestions=['Urology', 'Minimally Invasive', 'Neurogenic Bladder', 'Surgery', 'Postoperative'],
                        maxtags=30,  # Max number of tags the user can add
                    )

                observation_sensory_observations = st.text_input("Sensory Observations", observation_details.get("Sensory Observations", ""))
                observation_product_interactions = st.text_input("Product Interactions", observation_details.get("Product Interactions", ""))
                observation_people_interactions = st.text_input("People Interactions", observation_details.get("People Interactions", ""))
                observation_process_actions = st.text_input("Process Actions", observation_details.get("Process Actions", ""))
                insider_language = st_tags(
                        label="Insider Language:",
                        text="Press enter to add more",
                        value=observation_details.get("Insider Language", "").split(",") if observation_details.get("Insider Language") else [],  # Split tags into a list
                        suggestions=['Urology', 'Minimally Invasive', 'Neurogenic Bladder', 'Surgery', 'Postoperative'],
                        maxtags=30,  # Max number of tags the user can add
                    )
                tags = st_tags(
                        label="Insider Language:",
                        text="Press enter to add more",
                        value=observation_details.get("Tags", "").split(",") if observation_details.get("Tags") else [],  # Split tags into a list
                        suggestions=['Urology', 'Minimally Invasive', 'Neurogenic Bladder', 'Surgery', 'Postoperative'],
                        maxtags=30,  # Max number of tags the user can add
                    )
                
            else:
                st.write("Observation not found.")

            
        else:
            st.write("Please select an observation to edit.")

    
