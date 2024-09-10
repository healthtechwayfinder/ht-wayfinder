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

st.set_page_config(page_title="Add a New Case", page_icon="🏥")

st.markdown("# Add a New Case")


case_csv = "case.csv"
OPENAI_API_KEY = st.secrets["openai_key"]

# Access the credentials from Streamlit secrets
#test
creds_dict = {
    "type" : st.secrets["gcp_service_account"]["type"],
    "project_id" : st.secrets["gcp_service_account"]["project_id"],
    "private_key_id" : st.secrets["gcp_service_account"]["private_key_id"],
    "private_key" : st.secrets["gcp_service_account"]["private_key"],
    "client_email" : st.secrets["gcp_service_account"]["client_email"],
    "client_id" : st.secrets["gcp_service_account"]["client_id"],
    "auth_uri" : st.secrets["gcp_service_account"]["auth_uri"],
    "token_uri" : st.secrets["gcp_service_account"]["token_uri"],
    "auth_provider_x509_cert_url" : st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url" : st.secrets["gcp_service_account"]["client_x509_cert_url"],
    "universe_domain": st.secrets["gcp_service_account"]["universe_domain"],
}


if 'case_description' not in st.session_state:
    st.session_state['case_description'] = ""

if 'location' not in st.session_state:
    st.session_state['location'] = ""

if 'result' not in st.session_state:
    st.session_state['result'] = ""

if 'case_summary' not in st.session_state:
    st.session_state['case_summary'] = ""

if 'case_date' not in st.session_state:
    st.session_state['case_date'] = date.today()

if 'rerun' not in st.session_state:
    st.session_state['rerun'] = False

class caseRecord(BaseModel):
   # location: Optional[str] = Field(default=None, description="Location or setting where this case made. e.g. operating room (OR), hospital, exam room,....")
    People_Present: Optional[str] = Field(default=None, description="People present during the case. e.g. patient, clinician, scrub tech, family member, ...")
    Sensory_Observations: Optional[str] = Field(default=None, description="What is the observer sensing with sight, smell, sound, touch. e.g. sights, noises, textures, scents, ...")
    Specific_Facts: Optional[str] = Field(default=None, description="The facts noted in the case. e.g. the wound was 8cm, the sclera had a perforation, the patient was geriatric, ...")
    Insider_Language: Optional[str] = Field(default=None, description="Terminology used that is specific to this medical practice or procedure. e.g. specific words or phrases ...")
    Process_Actions: Optional[str] = Field(default=None, description="Which actions occurred during the case, and when they occurred. e.g. timing of various steps of a process, including actions performed by doctors, staff, or patients, could include the steps needed to open or close a wound, ...")
    # summary_of_observation: Optional[str] = Field(default=None, description="A summary of 1 sentence of the encounter or observation, e.g. A rhinoplasty included portions that were functional (covered by insurance), and cosmetic portions which were not covered by insurance. During the surgery, the surgeon had to provide instructions to a nurse to switch between functional and cosmetic parts, back and forth. It was mentioned that coding was very complicated for this procedure, and for other procedures, because there are 3 entities in MEE coding the same procedure without speaking to each other, ...")
    Notes_and_Impressions: Optional[str] = Field(default=None, description="Recorded thoughts, perceptions, insights, or open questions about people or their behaviors to be investigated later. e.g. Why is this procedure performed this way?, Why is the doctor standing in this position?, Why is this specific tool used for this step of the procedure? ...")

if not os.path.exists(case_csv):
    case_keys = list(caseRecord.__fields__.keys())
    case_keys = ['case_ID', 'case_date', 'case_summary', 'attendees', 'location', 'case_description'] + case_keys        
    csv_file = open(case_csv, "w")
    csv_writer = csv.writer(csv_file, delimiter=";")
    csv_writer.writerow(case_keys)

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

    # with get_openai_callback() as cb:
    output = case_chain.invoke({"case_description": case_description, "format_instructions": case_format_instructions})

    return json.loads(output.json())

def extractCaseFeatures(case_description):

    # Parse the case
    parsed_case = parseCase(case_description)

    input_fields = list(caseRecord.__fields__.keys())

    missing_fields = [field for field in input_fields if parsed_case[field] is None]

    output = ""

    for field in input_fields:
        if field not in missing_fields:
            key_output = field.replace("_", " ").capitalize()
            output += f"**{key_output}**: {parsed_case[field]}\n"
            output += "\n"

    missing_fields = [field.replace("_", " ").capitalize() for field in missing_fields]

    output += "\n\n **Missing fields**:"
    # for field in missing_fields:
    #     output += f" {field},"

    # # output += "\n\n"
    # # output += "="*75
    # output += "\nPlease add the missing fields to the observation if needed, then proceed with adding observation to your team record."

    # return f"{output}"

     # Add each missing field in red
    for field in missing_fields:
        output += f" <span style='color:red;'>{field}</span>,"

    # Display the output
    # st.markdown(output, unsafe_allow_html=True)
    return f"{output}"

def addToGoogleSheets(case_dict):
    try:
        scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        case_sheet = client.open("BioDesign Observation Record").Case_Log

        headers = case_sheet.row_values(1)

        # Prepare the row data matching the headers
        row_to_append = []
        for header in headers:
            if header in case_dict:
                value = case_dict[header]
                if value is None:
                    row_to_append.append("")
                else:
                    row_to_append.append(str(case_dict[header]))
            else:
                row_to_append.append("")  # Leave cell blank if header not in dictionary

        # Append the row to the sheet
        case_sheet.append_row(row_to_append)
        return True
    except Exception as e:
        print("Error adding to Google Sheets: ", e)
        return False

def embedCase(attendees, case_description, case_summary, case_date, case_ID):
    db = PineconeVectorStore(
            index_name=st.secrets["pinecone-keys"]["index_to_connect"],
            namespace="cases",
            embedding=OpenAIEmbeddings(api_key=OPENAI_API_KEY),
            pinecone_api_key=st.secrets["pinecone-keys"]["api_key"],
        )
    
    db.add_texts([case_description], metadatas=[{'attendees': Attendees, 'case_date': Case_Date, 'case_ID': Case_ID}])

    parsed_case = parseCase(case_description)

    # write attendees, observatoin and parsed case to csv
    case_keys = list(caseRecord.__fields__.keys())
    all_case_keys = ['case_summary', 'attendees', 'case_description', 'case_date', 'case_ID'] + case_keys
    case_values = [case_summary, attendees, case_description, case_date, case_ID] + [parsed_case[key] for key in case_keys]

    case_dict = dict(zip(all_case_keys, case_values))
    csv_file = open(case_csv, "a")
    csv_writer = csv.writer(csv_file, delimiter=";")
    csv_writer.writerow(case_values)

    status = addToGoogleSheets(case_dict)

    return status


def generateCaseSummary(case_description):

    llm = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0.7,
        openai_api_key=OPENAI_API_KEY,
        max_tokens=500,
    )


    case_prompt = PromptTemplate.from_template(
"""
You help me by creating a brief, one-sentence summary of the following medical case description.

case_description: {case_description}
Output Summary:"""
)

    case_chain = (
        case_prompt | llm | StrOutputParser()
    )

    # with get_openai_callback() as cb:
    output = case_chain.invoke({"case_description": case_description})

    return output


def clear_case():
    if 'case_description' in st.session_state:
        st.session_state['case_description'] = ""
    if 'case_summary' in st.session_state:
        st.session_state['case_summary'] = ""
    if 'result' in st.session_state:
        st.session_state['result'] = ""
    update_case_ID()

import streamlit as st
from datetime import date

# Initialize or retrieve the clear_case counters dictionary from session state
if 'case_counters' not in st.session_state:
    st.session_state['case_counters'] = {}

# Function to generate case ID with the format OBYYMMDDxxxx
def generate_case_ID(case_date, counter):
    return f"OB{case_date.strftime('%y%m%d')}{counter:04d}"

# Function to update case ID when the date changes
def update_case_ID():
    obs_date_str = st.session_state['case_date'].strftime('%y%m%d')

    # get all case ids from the sheets and update the counter
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    case_sheet = client.open("BioDesign Observation Record").sheet1
    column_values = case_sheet.col_values(1) 

    # find all case ids with the same date
    obs_date_ids = [obs_id for obs_id in column_values if obs_id.startswith(f"OB{obs_date_str}")]
    obs_date_ids.sort()

    # get the counter from the last case id
    if len(obs_date_ids) > 0:
        counter = int(obs_date_ids[-1][-4:])+1
    else:
        counter = 1
    
    # # Check if the date is already in the dictionary
    # if obs_date_str in st.session_state['case_counters']:
    #     # Increment the counter for this date
    #     st.session_state['case_counters'][obs_date_str] += 1
    # else:
    #     # Initialize the counter to 1 for a new date
    #     st.session_state['case_counters'][obs_date_str] = 1
    
    # Generate the case ID using the updated counter
    # counter = st.session_state['case_counters'][obs_date_str]

    st.session_state['case_ID'] = generate_case_ID(st.session_state['case_date'], counter)

# Use columns to place case_date, case_ID, and attendees side by side
col1, col2, col3 = st.columns(3)

with col1:
    # st calendar for date input with a callback to update the case_ID
    st.date_input("Case Date", date.today(), on_change=update_case_ID, key="case_date")
    #st.location['location'] = st.text_input("Location:", "")
    st.session_state['location'] = st.text_input("Location:", value=st.session_state["location"])




with col2:
    # Ensure the case ID is set the first time the script runs
    if 'case_ID' not in st.session_state:
        update_case_ID()

    # Display the case ID
    st.text_input("Case ID:", value=st.session_state['case_ID'], disabled=True)

with col3:
    #Display attendees options 
    attendees = st.multiselect("Attendees", ["Ana", "Bridget"])

############

# # Function to generate case ID with the format OBYYYYMMDDxxxx
# def generate_case_ID(case_date, counter):
#     return f"OB{case_date.strftime('%y%m%d')}{counter:04d}"

# # Initialize or retrieve case ID counter from session state
# if 'case_ID_counter' not in st.session_state:
#     st.session_state['case_ID_counter'] = 1

# # Function to update case ID when the date changes
# def update_case_ID():
#     st.session_state['case_ID'] = generate_case_ID(st.session_state['case_date'], st.session_state['case_ID_counter'])

# # st calendar for date input with a callback to update the case_ID
# st.session_state['case_date'] = st.date_input("Observation Date", date.today(), on_change=update_case_ID)

# # Initialize case_ID based on the observation date and counter
# st.session_state['case_ID'] = st.text_input("Observation ID:", value=st.session_state['case_ID'], disabled=True)

##########

#new_case_ID = st.case_date().strftime("%Y%m%d")+"%03d"%case_ID_counter
#st.session_state['case_ID'] = st.text_input("Observation ID:", value=new_case_ID)

#########

# Textbox for name input
#attendees = st.selectbox("attendees", ["Ana", "Bridget"])

# ######

# # Text area for observation input
# st.session_state['observation'] = st.text_area("Add Your Observation", value=st.session_state['observation'], placeholder="Enter your observation...", height=200)

# ######


# Initialize the observation text in session state if it doesn't exist

if "case_description" not in st.session_state:
    st.session_state["case_description"] = ""

# Function to clear the text area
def clear_text():
    st.session_state["case_description"] = ""

#st.markdown("---")

# Observation Text Area
##

#observation_text = st.text_area("Observation", value=st.session_state["observation"], height=200, key="observation")

# Add Your case Text with larger font size
st.markdown("<h4 style='font-size:20px;'>Add Your Case:</h4>", unsafe_allow_html=True)

# Button for voice input (currently as a placeholder)
#if st.button("🎤 Record Case (Coming Soon)"):
 #   st.info("Voice recording feature coming soon!")

# case Text Area
st.session_state['case_description'] = st.text_area("Case:", value=st.session_state["case_description"], height=200)


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

    # Button to Clear the case Text Area
    st.button("Clear Case", on_click=clear_text)
    
    # Container for result display
    result_container = st.empty()

# #Use columns to place buttons side by side
# col11, col21 = st.columns(2)


#     if st.button("Generate Observation Summary"):
#         st.session_state['case_summary']  = generateCaseSummary(st.session_state['observation'])

#     if st.session_state['case_summary'] != "":
#         st.session_state['case_summary'] = st.text_area("Generated Summary (editable):", value=st.session_state['case_summary'], height=50)
    

with col1:
    if st.button("Generate Case Summary"):
        st.session_state['result'] = extractCaseFeatures(st.session_state['case_description'])
        st.session_state['case_summary']  = generateCaseSummary(st.session_state['case_description'])
    
if st.session_state['case_summary'] != "":
    st.session_state['case_summary'] = st.text_area("Case Summary (editable):", value=st.session_state['case_summary'], height=50)

# st.write(f":green[{st.session_state['result']}]")
st.markdown(st.session_state['result'], unsafe_allow_html=True)

if st.session_state['rerun']:
    time.sleep(3)
    clear_case()
    st.session_state['rerun'] = False
    st.rerun()
    
    ##########

if st.button("Log Case", disabled=st.session_state['case_summary'] == ""):
    # st.session_state['case_summary']  = generateCaseSummary(st.session_state['observation'])
    st.session_state["error"] = ""

    if st.session_state['case_description'] == "":
        st.session_state["error"] = "Error: Please enter case."
        st.markdown(
            f"<span style='color:red;'>{st.session_state['error']}</span>", 
            unsafe_allow_html=True
        )
    elif st.session_state['case_summary'] == "":
        st.session_state["error"] = "Error: Please evaluate case."
        st.markdown(
            f"<span style='color:red;'>{st.session_state['error']}</span>", 
            unsafe_allow_html=True
        )
    else:
        status = embedCase(attendees, st.session_state['case_description'],  st.session_state['case_summary'], 
                            st.session_state['case_date'],
                            st.session_state['case_ID'])
        # st.session_state['case_summary'] = st.text_input("Generated Summary (editable):", value=st.session_state['case_summary'])
        # "Generated Summary: "+st.session_state['case_summary']+"\n\n"
        if status:
            st.session_state['result'] = "Case added to your team's database."
            st.session_state['rerun'] = True
            st.rerun()
        else:
            st.session_state['result'] = "Error adding case to your team's database. Please try again!"
        # clear_case()

st.markdown("---")

# if st.button("Back to Main Menu"):
#     clear_case()
#     switch_page("main_menu")


# st.markdown("---")
# Apply custom CSS to make the button blue
st.markdown("""
    <style>
    div.stButton > button {
        # background-color: #365980;
        # color: white;
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



# Create a button using Streamlit's native functionality
if st.button("Back to Main Menu"):
    switch_page("main_menu")
