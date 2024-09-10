import time
import streamlit as st
from streamlit_extras.switch_page_button import switch_page


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

st.set_page_config(page_title="Add a New Observation", page_icon="🔍")

st.markdown("# Add a New Observation")


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

if 'result' not in st.session_state:
    st.session_state['result'] = ""

if 'observation_summary' not in st.session_state:
    st.session_state['observation_summary'] = ""

if 'observation_tags' not in st.session_state:
    st.session_state['observation_tags'] = ""

if 'observation_date' not in st.session_state:
    st.session_state['observation_date'] = date.today()

if 'rerun' not in st.session_state:
    st.session_state['rerun'] = False


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
        Generate a list of 3-5 tags that are very relevant to the medical observation. The tags can be used to identify the type of procedure: (invasive procedure, minimally invasive, open procedure, non invasive, in the clinic, in the OR, in the emergency room..) the medical specialty (e.g.: rhynology, oncology, ophtalmology,..)  area of medicine, or type of technology being used for example Do not use numbers and separate them by commas.
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
    # location: Optional[str] = Field(default=None, description="Location or setting where this observation made. e.g. operating room (OR), hospital, exam room,....")
    stakeholders: Optional[str] = Field(default=None, description="Stakeholders involved in the healthcare event like a Patient, Care Partner, Advocacy & Support, Patient Advocacy Group, Patient Family, Patient Caretaker, Direct Patient Care Provider, Geriatrician, Chronic Disease Management Specialist, Cognitive Health Specialist, Psychologist, Psychiatrist, Nutritionist, Trainer, Physical Therapist, Occupational Therapist, End-of-Life / Palliative Care Specialist, Home Health Aide, Primary Care Physician, Social Support Assistant, Physical Therapist, Pharmacist, Nurse, Administrative & Support, Primary Care Physician, Facility Administrators, Nursing Home Associate, Assisted Living Facility Associate, Home Care Coordinator, Non-Healthcare Professional, Payer and Regulators, Government Official, Advocacy & Support, Professional Society Member, ...")
    sensory_observations: Optional[str] = Field(default=None, description="What is the observer sensing with sight, smell, sound, touch. e.g. sights, noises, textures, scents, ...")
    product_interactions: Optional[str] = Field(default=None, description="How is equipment and technology being used, engaged with, adjusted, or moved at this moment? what is missing?")
    process_actions: Optional[str] = Field(default=None, description="specific step or task that is taken within a larger workflow or process to achieve a particular goal or outcome. In the context of biodesign or healthcare, a process action could involve any number of operations that contribute to the diagnosis, treatment, or management of a patient, or the development and deployment of medical technologies..")
    # people_present: Optional[str] = Field(default=None, description="People present during the observation. e.g. patient, clinician, scrub tech, family member, ...")
    # specific_facts: Optional[str] = Field(default=None, description="The facts noted in the observation. e.g. the wound was 8cm, the sclera had a perforation, the patient was geriatric, ...")
    insider_language: Optional[str] = Field(default=None, description="Terminology used that is specific to this medical practice or procedure. e.g. specific words or phrases ...")
    # summary_of_observation: Optional[str] = Field(default=None, description="A summary of 1 sentence of the encounter or observation, e.g. A rhinoplasty included portions that were functional (covered by insurance), and cosmetic portions which were not covered by insurance. During the surgery, the surgeon had to provide instructions to a nurse to switch between functional and cosmetic parts, back and forth. It was mentioned that coding was very complicated for this procedure, and for other procedures, because there are 3 entities in MEE coding the same procedure without speaking to each other, ...")
    # questions: Optional[str] = Field(default=None, description="Recorded open questions about people or their behaviors to be investigated later. e.g. Why is this procedure performed this way?, Why is the doctor standing in this position?, Why is this specific tool used for this step of the procedure? ...")

# if not os.path.exists(observations_csv):
    # observation_keys = list(ObservationRecord.__fields__.keys())
    # observation_keys = ['observation_summary', 'observer', 'observation', 'observation_date', 'observation_id'] + observation_keys        
    # csv_file = open(observations_csv, "w")
    # csv_writer = csv.writer(csv_file, delimiter=";")
    # csv_writer.writerow(observation_keys)


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
    # for field in missing_fields:
    #     output += f" {field},"

    # # output += "\n\n"
    # # output += "="*75
    # output += "\nPlease add the missing fields to the observation if needed, then proceed with adding observation to your team record."

    # return f"{output}"

     # Add each missing field in red
        

    # Display the output
    # st.markdown(output, unsafe_allow_html=True)
    return f"{output}"

# def addToGoogleSheets(observation_dict):
#     try:
#         scope = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.metadata.readonly"
#         ]
#         creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#         client = gspread.authorize(creds)
#         observation_sheet = client.open("2024 Healthtech Identify Log").worksheet("Observation Log")

#         headers = observation_sheet.row_values(1)
#         headers = [i.strip() for i in headers]

#         # Prepare the row data matching the headers
#         row_to_append = []
#         for header in headers:
#             if header in observation_dict:
#                 value = observation_dict[header]
#                 if value is None:
#                     row_to_append.append("")
#                 else:
#                     row_to_append.append(str(observation_dict[header]))
#             else:
#                 row_to_append.append("")  # Leave cell blank if header not in dictionary

#         # Append the row to the sheet
#         observation_sheet.append_row(row_to_append)
#         return True
#     except Exception as e:
#         print("Error adding to Google Sheets: ", e)
#         return False

# def embedObservation(observer, observation, observation_summary, observation_date, observation_id):
#     db = PineconeVectorStore(
#             index_name=st.secrets["pinecone-keys"]["index_to_connect"],
#             namespace="observations",
#             embedding=OpenAIEmbeddings(api_key=OPENAI_API_KEY),
#             pinecone_api_key=st.secrets["pinecone-keys"]["api_key"],
#         )
    
#     db.add_texts([observation], metadatas=[{'observer': observer, 'observation_date': observation_date, 'observation_id': observation_id}])

#     print("Added to Pinecone: ", observation_id)

#     parsed_observation = parseObservation(observation)

#     # write observer, observatoin and parsed observation to csv
#     observation_keys = list(ObservationRecord.__fields__.keys())
#     observation_keys_formatted = [i.replace("_", " ").title() for i in observation_keys]
#     all_observation_keys = ['Observation Title', 'Observer', 'Observation Description', 'Date', 'Observation ID'] + observation_keys_formatted
#     observation_values = [observation_summary, observer, observation, observation_date, observation_id] + [parsed_observation[key] for key in observation_keys]

#     observation_dict = dict(zip(all_observation_keys, observation_values))
#     # csv_file = open(observations_csv, "a")
#     # csv_writer = csv.writer(csv_file, delimiter=";")
#     # csv_writer.writerow(observation_values)

#     status = addToGoogleSheets(observation_dict)
#     print("Added to Google Sheets: ", status)

#     return status

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


# Modified function to embed the observation and tags
def embedObservation(observer, observation, observation_summary, observation_tags, observation_date, observation_id, related_case_id_with_title):
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

    if 'parsed_observation' not in st.session_state:
        st.session_state['parsed_observation'] = parseObservation(observation)
    else:
        parsed_observation = st.session_state['parsed_observation']


    # Prepare the observation record with the tags
    observation_keys = list(ObservationRecord.__fields__.keys())
    observation_keys_formatted = [i.replace("_", " ").title() for i in observation_keys]
    all_observation_keys = ['Observation Title', 'Observer', 'Observation Description', 'Tags', 'Date', 'Observation ID', 'Related Case ID'] + observation_keys_formatted
    observation_values = [observation_summary, observer, observation, observation_tags, observation_date, observation_id, related_case_id] + [parsed_observation[key] for key in observation_keys]

    observation_dict = dict(zip(all_observation_keys, observation_values))

    # Add the observation record (including tags) to Google Sheets
    status = addToGoogleSheets(observation_dict)
    print("Added to Google Sheets: ", status)

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
    if 'observation' in st.session_state:
        st.session_state['observation'] = ""
    if 'observation_summary' in st.session_state:
        st.session_state['observation_summary'] = ""
    if 'result' in st.session_state:
        st.session_state['result'] = ""
    if 'observation_tags' in st.session_state:
        st.session_state['observation_tags'] = ""
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
    
    # # Check if the date is already in the dictionary
    # if obs_date_str in st.session_state['observation_counters']:
    #     # Increment the counter for this date
    #     st.session_state['observation_counters'][obs_date_str] += 1
    # else:
    #     # Initialize the counter to 1 for a new date
    #     st.session_state['observation_counters'][obs_date_str] = 1
    
    # Generate the observation ID using the updated counter
    # counter = st.session_state['observation_counters'][obs_date_str]

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
    case_titles = case_log.col_values(2)[1:]

    # find all observation ids with the same date
    existing_case_ids_with_title = dict(zip(case_ids, case_titles))

    # make strings with case id - title
    existing_case_ids_with_title = [f"{case_id} - {case_title}" for case_id, case_title in existing_case_ids_with_title.items()]

    print("Existing Case IDS: ")
    print(existing_case_ids_with_title)
    return existing_case_ids_with_title


# Use columns to place observation_date, observation_id, and observer side by side
col1, col2, col3 = st.columns(3)

with col1:
    # st calendar for date input with a callback to update the observation_id
    st.date_input("Observation Date", date.today(), on_change=update_observation_id, key="observation_date")

    existing_case_ids_with_title = getExistingCaseIDS()
    case_id_with_title = st.selectbox("Related Case ID", existing_case_ids_with_title)

with col2:
    # Ensure the observation ID is set the first time the script runs
    if 'observation_id' not in st.session_state:
        update_observation_id()

    # Display the observation ID
    st.text_input("Observation ID:", value=st.session_state['observation_id'], disabled=True)

with col3:
    #Display Observer options 
    observer = st.selectbox("Observer", ["Ana", "Bridget"])

############

# # Function to generate observation ID with the format OBYYYYMMDDxxxx
# def generate_observation_id(observation_date, counter):
#     return f"OB{observation_date.strftime('%y%m%d')}{counter:04d}"

# # Initialize or retrieve observation ID counter from session state
# if 'observation_id_counter' not in st.session_state:
#     st.session_state['observation_id_counter'] = 1

# # Function to update observation ID when the date changes
# def update_observation_id():
#     st.session_state['observation_id'] = generate_observation_id(st.session_state['observation_date'], st.session_state['observation_id_counter'])

# # st calendar for date input with a callback to update the observation_id
# st.session_state['observation_date'] = st.date_input("Observation Date", date.today(), on_change=update_observation_id)

# # Initialize observation_id based on the observation date and counter
# st.session_state['observation_id'] = st.text_input("Observation ID:", value=st.session_state['observation_id'], disabled=True)

##########

#new_observation_id = st.observation_date().strftime("%Y%m%d")+"%03d"%observation_id_counter
#st.session_state['observation_id'] = st.text_input("Observation ID:", value=new_observation_id)

#########

# Textbox for name input
#observer = st.selectbox("Observer", ["Ana", "Bridget"])

# ######

# # Text area for observation input
# st.session_state['observation'] = st.text_area("Add Your Observation", value=st.session_state['observation'], placeholder="Enter your observation...", height=200)

# ######


# Initialize the observation text in session state if it doesn't exist
if "observation" not in st.session_state:
    st.session_state["observation"] = ""

# Function to clear the text area
def clear_text():
    st.session_state["observation"] = ""

#st.markdown("---")

# Observation Text Area
##

#observation_text = st.text_area("Observation", value=st.session_state["observation"], height=200, key="observation")

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
    # Use custom CSS for the red button
    # st.markdown("""
    #     <style>
    #     .stButton > button {
    #         background-color: #942124;
    #         color: white;
    #         font-size: 16px;
    #         padding: 10px 20px;
    #         border-radius: 8px;
    #         border: none;
    #     }
    #     .stButton > button:hover {
    #         background-color: darkred;
    #     }
    #     </style>
    #     """, unsafe_allow_html=True)

    # Button to Clear the Observation Text Area
    st.button("Clear Observation", on_click=clear_text)
    
    # Container for result display
    result_container = st.empty()

# #Use columns to place buttons side by side
# col11, col21 = st.columns(2)


# with col11:
#     if st.button("Generate Observation Summary"):
#         st.session_state['observation_summary']  = generateObservationSummary(st.session_state['observation'])

#     if st.session_state['observation_summary'] != "":
#         st.session_state['observation_summary'] = st.text_area("Generated Summary (editable):", value=st.session_state['observation_summary'], height=50)
    

with col1:
    if st.button("Evaluate Observation"):
        st.session_state['result'] = extractObservationFeatures(st.session_state['observation'])
        st.session_state['observation_summary']  = generateObservationSummary(st.session_state['observation'])
        # Generate tags for the observation
        st.session_state['observation_tags'] = generateObservationTags(st.session_state['observation'])
    
if st.session_state['observation_summary'] != "":
    st.session_state['observation_summary'] = st.text_area("Generated Summary (editable):", value=st.session_state['observation_summary'], height=50)

# st.write(f":green[{st.session_state['result']}]")
# Display the generated tags in a text area (editable by the user if needed)
if st.session_state['observation_tags'] != "":
    st.session_state['observation_tags'] = st.text_area("Generated Tags (editable):", value=st.session_state['observation_tags'], height=50)

st.markdown(st.session_state['result'], unsafe_allow_html=True)

if st.session_state['rerun']:
    time.sleep(3)
    clear_observation()
    st.session_state['rerun'] = False
    st.rerun()
    
    ##########

if st.button("Add Observation to Team Record", disabled=st.session_state['observation_summary'] == ""):
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
        status = embedObservation(observer, st.session_state['observation'],  st.session_state['observation_summary'], 
                            st.session_state['observation_tags'],
                            st.session_state['observation_date'],
                            st.session_state['observation_id'],
                            case_id_with_title)
        # st.session_state['observation_summary'] = st.text_input("Generated Summary (editable):", value=st.session_state['observation_summary'])
        # "Generated Summary: "+st.session_state['observation_summary']+"\n\n"
        if status:
            st.session_state['result'] = "Observation added to your team's database."
            st.session_state['rerun'] = True
            st.rerun()
        else:
            st.session_state['result'] = "Error adding observation to your team's database, try again!"
        # clear_observation()

st.markdown("---")

# if st.button("Back to Main Menu"):
#     clear_observation()
#     switch_page("main_menu")


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
