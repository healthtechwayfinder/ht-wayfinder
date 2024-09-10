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

st.set_page_config(page_title="Add or Edit a Case", page_icon="🏥")
# Dropdown menu for selecting action
action = st.selectbox("Choose an action", ["Add New Case", "Edit Existing Case"])

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


if 'case_description' not in st.session_state:
    st.session_state['case_description'] = ""

# if 'location' not in st.session_state:
#     st.session_state['location'] = ""

if 'result' not in st.session_state:
    st.session_state['result'] = ""

if 'case_title' not in st.session_state:
    st.session_state['case_title'] = ""

if 'case_date' not in st.session_state:
    st.session_state['case_date'] = date.today()

if 'rerun' not in st.session_state:
    st.session_state['rerun'] = False

if 'parsed_case' not in st.session_state:
    st.session_state['parsed_case'] = ""

class caseRecord(BaseModel):
    stakeholders: Optional[str] = Field(default=None, description="Stakeholders involved in the observation. e.g. patient, surgeon, scrub tech, circulating nurse, ...")
    insider_language: Optional[str] = Field(default=None, description="Terminology used that is specific to this medical practice or procedure. e.g. specific words or phrases ...")
    tags: Optional[str] = Field(default=None, description="Tags or keywords that describe the observation. e.g. surgery, procedure, ...")

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

    if len(missing_fields)>0:
        output += "\n\n **Missing fields**:"

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
        # # print all the sheets in the workbook
        # print("All sheets in the workbook:")
        # sheet_list = client.open("BioDesign Observation Record").worksheets()
        # for sheet in sheet_list:
        #     print(sheet.title)

        case_sheet = client.open("2024 Healthtech Identify Log").worksheet("Case Log")

        headers = case_sheet.row_values(1)
        headers = [header.strip() for header in headers]

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

def embedCase(attendees, case_description, case_title, case_date, case_ID):
    db = PineconeVectorStore(
            index_name=st.secrets["pinecone-keys"]["index_to_connect"],
            namespace="cases",
            embedding=OpenAIEmbeddings(api_key=OPENAI_API_KEY),
            pinecone_api_key=st.secrets["pinecone-keys"]["api_key"],
        )
    
    db.add_texts([case_description], metadatas=[{'attendees': attendees, 'case_date': case_date, 'case_ID': case_ID}])
    print("Case added to Pinecone")

    if 'parsed_case' in st.session_state and len(st.session_state['parsed_case'])>0:
        parsed_case = st.session_state['parsed_case']
    else:
        parsed_case = parseCase(case_description)
        st.session_state['parsed_case'] = parsed_case
    

    # write attendees, observatoin and parsed case to csv
    case_keys = list(caseRecord.__fields__.keys())
    case_keys_formatted = [i.replace("_", " ").title() for i in case_keys]

    all_case_keys = ['Title', 'People Present', 'Case Description', 'Date', 'Case ID'] + case_keys_formatted
    case_values = [case_title, attendees, case_description, case_date, case_ID] + [parsed_case[key] for key in case_keys]

    case_dict = dict(zip(all_case_keys, case_values))
    # csv_file = open(case_csv, "a")
    # csv_writer = csv.writer(csv_file, delimiter=";")
    # csv_writer.writerow(case_values)

    status = addToGoogleSheets(case_dict)
    print("Case added to Google Sheets")

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
You help me by creating a brief 4-10 word title of the following medical case description. Do not use quotes or special characters in the title.

case_description: {case_description}
Output title:"""
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
    if 'case_title' in st.session_state:
        st.session_state['case_title'] = ""
    if 'result' in st.session_state:
        st.session_state['result'] = ""
    update_case_ID()

# Fetch case IDs from Google Sheets
def fetch_case_ids():
    sheet = get_google_sheet("2024 Healthtech Identify Log", "Observation Log")  # Adjust as per your sheet name
    case_ids = sheet.col_values(1)  # Assuming "Case ID" is in the first column
    return case_ids[1:]  # Exclude header

# Function to connect to Google Sheets
def get_google_sheet(sheet_name, worksheet_name):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).worksheet(worksheet_name)
    return sheet
# Fetch case IDs from Google Sheets
def fetch_case_ids():
    try:
        sheet = get_google_sheet("2024 Healthtech Identify Log", "Case Log")  # Ensure this is correct
        case_ids = sheet.col_values(1)  # Assuming "Case ID" is in the first column
        return case_ids[1:]  # Exclude header row
    except Exception as e:
        print(f"Error fetching case IDs: {e}")
        return []
# Fetch case details based on selected case ID
def fetch_case_details(case_id):
    sheet = get_google_sheet("2024 Healthtech Identify Log", "Observation Log")
    data = sheet.get_all_records()
    for row in data:
        if row["Case ID"] == case_id:
            return row
    return None
# Update case details in Google Sheets
def update_case(case_id, updated_data):
    try:
        sheet = get_google_sheet("2024 Healthtech Identify Log", "Case Log")
        data = sheet.get_all_records()

        # Find the row corresponding to the case_id and update it
        for i, row in enumerate(data, start=2):  # Skip header row
            if row["Case ID"] == case_id:
                # Update the necessary fields (Assuming the updated_data has the same keys as Google Sheets columns)
                for key, value in updated_data.items():
                    sheet.update_cell(i, list(row.keys()).index(key) + 1, value)
                return True
        return False
    except Exception as e:
        print(f"Error updating case: {e}")
        return False



import streamlit as st
from datetime import date


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
    
        # get all case ids from the sheets and update the counter
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.metadata.readonly"
            ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        case_sheet = client.open("2024 Healthtech Identify Log").worksheet("Case Log")
        column_values = case_sheet.col_values(1) 
    
        # find all case ids with the same date
        case_date_ids = [case_id for case_id in column_values if case_id.startswith(f"CA{case_date_str}")]
        case_date_ids.sort()
    
        # get the counter from the last case id
        if len(case_date_ids) > 0:
            counter = int(case_date_ids[-1][-4:])+1
        else:
            counter = 1
        
       
        st.session_state['case_ID'] = generate_case_ID(st.session_state['case_date'], counter)
    
    # Use columns to place case_date, case_ID, and attendees side by side
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # st calendar for date input with a callback to update the case_ID
        st.date_input("Case Date", date.today(), on_change=update_case_ID, key="case_date")

    
    with col2:
        # Ensure the case ID is set the first time the script runs
        if 'case_ID' not in st.session_state:
            update_case_ID()
    
        # Display the case ID
        st.text_input("Case ID:", value=st.session_state['case_ID'], disabled=True)
    
    with col3:
        #Display attendees options 
        st.session_state['attendees'] = st.multiselect("Attendees", ["Ana", "Bridget"])
    
    ############
    
    # # Function to generate case ID with the format CAYYYYMMDDxxxx
    # def generate_case_ID(case_date, counter):
    #     return f"CA{case_date.strftime('%y%m%d')}{counter:04d}"
    
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
    #         st.session_state['case_title']  = generateCaseSummary(st.session_state['observation'])
    
    #     if st.session_state['case_title'] != "":
    #         st.session_state['case_title'] = st.text_area("Generated Summary (editable):", value=st.session_state['case_title'], height=50)
        
    
    with col1:
        if st.button("Submit Case"):
            st.session_state['result'] = extractCaseFeatures(st.session_state['case_description'])
            st.session_state['case_title']  = generateCaseSummary(st.session_state['case_description'])
        
    if st.session_state['case_title'] != "":
        st.session_state['case_title'] = st.text_area("Case Title (editable):", value=st.session_state['case_title'], height=50)
    
    # st.write(f":green[{st.session_state['result']}]")
    st.markdown(st.session_state['result'], unsafe_allow_html=True)
    
    if st.session_state['rerun']:
        time.sleep(3)
        clear_case()
        st.session_state['rerun'] = False
        st.rerun()
        
        ##########
    
    if st.button("Log Case", disabled=st.session_state['case_title'] == ""):
        # st.session_state['case_title']  = generateCaseSummary(st.session_state['observation'])
        st.session_state["error"] = ""
    
        if st.session_state['case_description'] == "":
            st.session_state["error"] = "Error: Please enter case."
            st.markdown(
                f"<span style='color:red;'>{st.session_state['error']}</span>", 
                unsafe_allow_html=True
            )
        elif st.session_state['case_title'] == "":
            st.session_state["error"] = "Error: Please evaluate case."
            st.markdown(
                f"<span style='color:red;'>{st.session_state['error']}</span>", 
                unsafe_allow_html=True
            )
        else:
            status = embedCase(st.session_state['attendees'], st.session_state['case_description'],  st.session_state['case_title'], 
                                st.session_state['case_date'],
                                st.session_state['case_ID'])
            # st.session_state['case_title'] = st.text_input("Generated Summary (editable):", value=st.session_state['case_title'])
            # "Generated Summary: "+st.session_state['case_title']+"\n\n"
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

# If the user chooses "Edit Existing Case"
elif action == "Edit Existing Case":
    st.markdown("### Edit an Existing Case")

    # Step 1: Fetch and display case IDs in a dropdown
    case_ids = fetch_case_ids()

    # Ensure case_ids are not empty
    if not case_ids:
        st.error("No cases found.")
    else:
        case_to_edit = st.selectbox("Select a case to edit", case_ids)

        # Step 2: Fetch and display case details for the selected case
        if case_to_edit:
            case_details = fetch_case_details(case_to_edit)
            
            # Ensure case details are fetched correctly
            if case_details:
                # Debug: Print the case details (optional)
                print(f"Editing case: {case_details}")

                # Display editable fields for the selected case
                case_title_edit = st.text_input("Edit Case Title", case_details.get("Case Title", ""))
                case_description_edit = st.text_area("Edit Case Description", case_details.get("Case Description", ""))
                
                # Handle the case date properly (convert to a `datetime.date` object if needed)
                case_date_str = case_details.get("Case Date", "")
                try:
                    case_date_edit = st.date_input("Edit Case Date", date.fromisoformat(case_date_str))
                except ValueError:
                    st.error(f"Invalid date format for case: {case_date_str}")
                    case_date_edit = st.date_input("Edit Case Date", date.today())

                # Step 3: Save changes
                if st.button("Save Changes"):
                    updated_data = {
                        "Case Title": case_title_edit,
                        "Case Description": case_description_edit,
                        "Case Date": case_date_edit.isoformat(),
                    }
                    if update_case(case_to_edit, updated_data):
                        st.success(f"Changes to '{case_to_edit}' saved successfully!")
                    else:
                        st.error(f"Failed to save changes to '{case_to_edit}'.")


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



# Create a button using Streamlit's native functionality
if st.button("Back to Main Menu"):
    switch_page("main_menu")
