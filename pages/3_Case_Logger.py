import time
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from datetime import date
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
import random

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

# if 'case_date' not in st.session_state:
#     st.session_state['case_date'] = ""

if 'rerun' not in st.session_state:
    st.session_state['rerun'] = False

if 'parsed_case' not in st.session_state:
    st.session_state['parsed_case'] = ""

class caseRecord(BaseModel):
    location: Optional[str] = Field(default=None, description="(only nouns) physical environment where the case took place. e.g: operating room, at the hospital MGH, in the emergency room...")
    stakeholders: Optional[str] = Field(default=None, description="Stakeholders involved in the healthcare event (no names) like a Patient, Care Partner, Advocacy & Support, Patient Advocacy Group, Patient Family, Patient Caretaker, Direct Patient Care Provider, Geriatrician, Chronic Disease Management Specialist, Cognitive Health Specialist, Psychologist, Psychiatrist, Nutritionist, Trainer, Physical Therapist, Occupational Therapist, End-of-Life / Palliative Care Specialist, Home Health Aide, Primary Care Physician, Social Support Assistant, Physical Therapist, Pharmacist, Nurse, Administrative & Support, Primary Care Physician, Facility Administrators, Nursing Home Associate, Assisted Living Facility Associate, Home Care Coordinator, Non-Healthcare Professional, Payer and Regulators, Government Official, Advocacy & Support, Professional Society Member, ...")
    people_present: Optional[str] = Field(default=None, description="Names cited in the description")
    insider_language: Optional[str] = Field(default=None, description="Terminology used that is specific to this medical practice or procedure. e.g. specific words or phrases ...")
    tags: Optional[str] = Field(default=None, description="Generate a list of 3-5 tags (only noun) that are very relevant to the medical observation. The tags can be used to identify the type of procedure: (invasive procedure, minimally invasive, open procedure, non invasive, in the clinic, in the OR, in the emergency room..) the medical specialty (e.g.: rhynology, oncology, ophtalmology,..)  area of medicine, or type of technology being used for example Do not use numbers and separate them by commas. Give only the list of tags without any quotes or special characters.")

def generateDefinition(term):
    llm = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0.7,
        openai_api_key=OPENAI_API_KEY,
        max_tokens=100,
    )

    prompt = PromptTemplate.from_template(
        """
        Provide a brief, simple definition for the following medical term.

        Term: {term}
        Definition:
        """
    )
    definition_chain = (
        prompt | llm | StrOutputParser()
    )
    output = definition_chain.invoke({"term": term})
    return output

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

# Function to parse the result string into a dictionary
def parse_result_string(result_str):
    parsed_dict = {}
    # Split the string into lines
    lines = result_str.splitlines()
    # Iterate over each line and split on the first colon to get key-value pairs
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)  # Split only on the first colon
            parsed_dict[key.strip()] = value.strip()  # Trim extra spaces
            
    return parsed_dict

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

    # Display missing fields as editable inputs
    output += "\n\n **Missing fields**:"
    for field in missing_fields:
        field_clean = field.replace("_", " ").capitalize()
        # Render text input for missing fields, storing results back in parsed_case
        parsed_case[field] = st.text_input(f"Enter {field_clean}", key=field)
        
    return f"{output}"

def addToGlossary(insider_language_terms, case_id):
    try:
        # Set the scope and authenticate
        scope = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.metadata.readonly",
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)

        # Open the glossary worksheet
        glossary_sheet = client.open("Glossary").worksheet("Sheet1")

        # Get all the existing glossary terms
        glossary_data = glossary_sheet.get_all_records()

        # Find the column indices for "Term" and "Related cases"
        headers = glossary_sheet.row_values(1)
        print("Headers found:", headers)  # Debugging

        term_col_idx = headers.index("Term") + 1
        related_cases_col_idx = headers.index("Related cases") + 1
        definition_col_idx = headers.index("Definition") + 1

        # Split the insider language terms if they are in a single string
        terms_list = [term.strip() for term in insider_language_terms.split(",")]

        for term in terms_list:
            term_exists = False

            # Check if the term already exists in the glossary
            for i, row in enumerate(glossary_data, start=2):  # Start at 2 to skip the header row
                if row['Term'].strip().lower() == term.strip().lower():
                    term_exists = True
                    # Append the case_id to the "Related cases" column if it's not already there
                    related_cases = row['Related cases']
                    if case_id not in related_cases.split(', '):
                        updated_related_cases = f"{related_cases}, {case_id}".strip(', ')
                        glossary_sheet.update_cell(i, related_cases_col_idx, updated_related_cases)
                        print(f"Updated related cases for term {term} with {case_id}")
                    else:
                        print(f"Case ID {case_id} already exists for term {term}")
                    break

            # If the term doesn't exist, add a new entry with a generated definition
            if not term_exists:
                print(f"Term {term} does not exist, adding a new one.")
                definition = generateDefinition(term)
                glossary_sheet.append_row([term, definition, case_id])
                print(f"Added new term: {term} with definition and case ID: {case_id}")

    except Exception as e:
        print(f"Error adding to the Glossary: {e}")


def addToGoogleSheets(case_dict):
    try:
        scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        case_sheet = client.open("2024 Healthtech Identify Log").worksheet("Case Log")
        headers = case_sheet.row_values(1)
        headers = [header.strip() for header in headers]

        # Debug: Print case_dict to verify if attendees are being included
        print("Case Dictionary to Save: ", case_dict)

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
    
    # Add insider language to Glossary sheet
    if parsed_case['insider_language']:
        addToGlossary(parsed_case['insider_language'], case_ID)

    # write attendees, observatoin and parsed case to csv
    case_keys = list(caseRecord.__fields__.keys())
    case_keys_formatted = [i.replace("_", " ").title() for i in case_keys]
    # all_case_keys = ['Title', 'People Present', 'Case Description', 'Date', 'Case ID', 'Attendees'] + case_keys_formatted
    # case_values = [case_title, attendees, case_description, case_date, case_ID] + [parsed_case[key] for key in case_keys]
    all_case_keys = ['Title', 'People Present', 'Case Description', 'Date', 'Case ID', 'Attendees'] + case_keys_formatted
    case_values = [case_title, attendees, case_description, case_date, case_ID, ', '.join(attendees)] + [parsed_case[key] for key in case_keys]
    case_dict = dict(zip(all_case_keys, case_values))
    # csv_file = open(case_csv, "a")
    # csv_writer = csv.writer(csv_file, delimiter=";")
    # csv_writer.writerow(case_values)
    # Debug: Print the case_dict before saving
    print("Case Dictionary: ", case_dict)
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
    # Refresh the page back to the initial state

# Fetch case IDs and titles from Google Sheets
def fetch_case_ids_and_titles():
    try:
        sheet = get_google_sheet("2024 Healthtech Identify Log", "Case Log")  # Ensure this is correct
        data = sheet.get_all_records()
        # Create a list of tuples with (case_id, title)
        case_info = [(row["Case ID"], row["Title"]) for row in data if "Case ID" in row and "Title" in row]
        return case_info
    except Exception as e:
        print(f"Error fetching case IDs and titles: {e}")
        return []

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
    sheet = get_google_sheet("2024 Healthtech Identify Log", "Case Log")
    data = sheet.get_all_records()
    # # Print the data being fetched
    # st.write(data)
    for row in data:
        if "Case ID" in row and row["Case ID"].strip() == case_id.strip():
            return row
    st.error(f"Case ID {case_id} not found.")
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


# Function to generate a random color
def random_color():
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

# Function to render editable colorful tags
def render_editable_colorful_tags(tags_values):
    colorful_tags = []
    for tag in tags_values:
        color = random_color()
        tag_html = f"<span style='background-color:{color}; padding:5px 10px; border-radius:8px; margin-right:5px; color:white;'>{tag}</span>"
        colorful_tags.append(tag_html)
    return colorful_tags

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
        st.session_state['attendees'] = st.multiselect("Attendees", ["Deborah", "Kyle", "Ryan", "Lois", "Fellowisa"])
    
    # Initialize the observation text in session state if it doesn't exist
    if "case_description" not in st.session_state:
        st.session_state["case_description"] = ""
    
    # Function to clear the text area
    def clear_text():
        st.session_state["case_description"] = ""

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
        #Button to Clear the case Text Area
        st.button("Clear Case", on_click=clear_case)
        # Container for result display
        result_container = st.empty() 
    
    with col1:
        if st.button("Submit Case"):
            # Generate the case description
            st.session_state['case_title']  = generateCaseSummary(st.session_state['case_description'])
            if st.session_state['case_title'] != "":
                st.session_state['result'] = extractCaseFeatures(st.session_state['case_description'])
            
    # # Process the result after button click
    # parsed_result = st.session_state['result']

    # Process the result after button click
    parsed_result = st.session_state.get('result', '')
    
    # Ensure parsed_result is a valid string before calling .splitlines()
    if isinstance(parsed_result, str) and parsed_result:
        lines = parsed_result.splitlines()
    else:
        st.error("No valid result found to process. Please submit a valid case.")
    
        
    # Ensure 'result' exists
    if parsed_result and isinstance(st.session_state['parsed_case'], dict):
        # Print case title
        st.session_state['case_title'] = st.text_area("Case Title (editable):", value=st.session_state['case_title'])
        # # Debug: Show the parsed result
        # st.write("Parsed Result:", parsed_result)
        # Initialize tags as an empty list in case it's not found
        tags_values = []
        # Split the result by lines and extract each case detail by assuming specific labels
        lines = parsed_result.splitlines()
        #     # Debug: Write lines being processed
        # st.write("Lines from parsed result:", lines)
        editable_fields = {}
        # Find missing fields by checking if any field in parsed_case is None or empty
        input_fields = list(caseRecord.__fields__.keys())
        # Find missing fields by checking if any field in parsed_case is None or empty
        parsed_case = st.session_state['parsed_case']
        missing_fields = [field for field in input_fields if parsed_case.get(field) in [None, ""]]

        # Ensure 'result' exists in session state
        parsed_result = st.session_state.get('result', '')
        
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)  # Split by the first colon
                key = key.strip()
                value = value.strip()
                # Remove markdown bold characters (e.g., **Tags**) by replacing them with an empty string
                key_clean = key.replace('**', '').strip()
                # No missing fields handling here! Only make fields editable.
                # Skip printing or displaying missing fields or empty fields
                if key_clean in missing_fields or value == "":
                    continue  # Skip this field if it's missing or has an empty value

                # # The following line displays each field from the parsed result as an editable text input.
                # editable_fields[key_clean] = st.text_input(f"{key_clean}", value=value)

                # Process tags when the key is 'Tags'
                if key_clean.lower() == 'tags':
                    # st.write(f"Processing line: key='{key}', value='{value}'")
                    tags_values = [tag.strip() for tag in value.split(",")]
                    # st.write(f"Tags after splitting and stripping: {tags_values}")
                    # st.write(f"Length of tags_values: {len(tags_values)}")
                    continue
                
                # Print non-empty fields only (non-missing fields)
                editable_fields[key_clean] = st.text_input(f"{key_clean}", value=value)
        
        # Save the editable fields to session state
        st.session_state['editable_result'] = editable_fields

        # # Display tags if tags were found
        # if tags_values:
        #     st_tags(
        #         label="Tags",
        #         text="Press enter to add more",
        #         value=tags_values,  # Show the tags found in the result
        #         maxtags=10
        #     )
        # else:
        #     st.write("No tags found.")

        # st.write("Current Tags:", tags_values)  # This will display the list of tags

        # Display tags and allow for dynamic updates using st_tags
        updated_tags = st_tags(
            label="Tags",
            text="Press enter to add more",
            value=tags_values,  # Show the tags found in the result
            maxtags=10,
            key="tags_input"  # Unique key to ensure it's updated correctly
        )
        
        # Update tags_values with the modified tags from st_tags
        tags_values = updated_tags

        # Print the updated tags values after any modification (entry or deletion)
        st.write("Updated Tags:", tags_values)

        st.session_state['parsed_case']['tags'] = updated_tags

        # Update 'result' with parsed_case
        st.session_state['result'] = st.session_state['parsed_case']
        
        # Print the updated session state for debugging
        st.write("Updated session state result:", st.session_state['result'])

        # Convert updated_tags to a comma-separated string
        updated_tags_string = ", ".join(updated_tags)
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)  # Split by the first colon
                key = key.strip()
                value = value.strip()
                # Remove markdown bold characters (e.g., **Tags**) by replacing them with an empty string
                key_clean = key.replace('**', '').strip()
        
                # If the key is 'tags', update it with the modified tags
                if key_clean.lower() == 'tags':
                    st.write(f"Processing line: key='{key}', value='{value}'")  # Debugging output
                    # Substitute the old value (tags) with the updated tags
                    value = updated_tags_string  # Replace the old value with updated tags
                    st.write(f"Updated Tags: {updated_tags_string}")  # Debugging output
                    # Update the session state with the updated tags
                    # if 'result' not in st.session_state or not isinstance(st.session_state['result'], dict):
                    #     st.session_state['result'] = {}  # Initialize result if it doesn't exist
                    
                    # # Update the 'tags' field in the result
                    # st.session_state['result']['tags'] = updated_tags_string
        
                # Continue with other processing logic for the rest of the lines
                # You can add further updates to the session state as needed for other fields
        
        # Debug: Print session state to verify changes
        st.write("Updated session state result:", st.session_state['result'])
        
        st.markdown("### Missing Fields")
        
        for field in missing_fields:
            field_clean = field.replace("_", " ").capitalize()
            # Render text input for missing fields, storing results back in parsed_case
            st.session_state['parsed_case'][field] = st.text_input(f"Enter {field_clean}", key=field, value=st.session_state['parsed_case'].get(field, ""))
            
        # # Ensure that parsed_case is updated in the 'result' for Google Sheets
        # st.session_state['result'] = parsed_case  # Update the result with the modified parsed_case
    
        # # Save the editable fields to session state
        # st.session_state['editable_result'] = editable_fields


    
    # #Rerun logic
    # if st.session_state['rerun']:
    #     time.sleep(3)
    #     clear_case()
    #     st.session_state['rerun'] = False
    #     st.rerun()
    # Rerun logic
    if st.session_state['rerun']:
        # Ensure any unsaved changes are stored in session state before rerun
        # Example: Save updated case fields, tags, etc
        # Any other custom saving logic
        time.sleep(3)  # Pause to let the user see changes, if necessary
        #clear_case()  # Optional: Clear case if needed before rerun
        st.session_state['rerun'] = False
        st.rerun()  # Trigger the rerun

   # Logging cases  
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

    # Fetch and display case IDs and titles in a dropdown
    case_info = fetch_case_ids_and_titles()

    # Ensure case_info is not empty
    if not case_info:
        st.error("No cases found.")
    else:
        # Create a list of display names in the format "case_id: title"
        case_options = [f"{case_id}: {title}" for case_id, title in case_info]
        
        # Display the dropdown with combined case_id and title
        selected_case = st.selectbox("Select a case to edit", case_options)

        # Extract the selected case_id from the dropdown (case_id is before the ":")
        case_to_edit = selected_case.split(":")[0].strip()
    
        # Step 2: Fetch and display case details for the selected case
        if case_to_edit:
            case_details = fetch_case_details(case_to_edit)
            
            if case_details:
                # # Debug: Print the case details (optional)
                # st.write(f"Editing case: {case_details}")
    
                # Editable fields for the selected case
                case_title = st.text_input("Title", case_details.get("Title", ""))
                #case_date = st.date_input("Date", date.fromisoformat(case_details.get("Date", str(date.today()))))
                case_description = st.text_area("Case Description", case_details.get("Case Description", ""))
                location = st.text_input("Location", case_details.get("Location", ""))
                stakeholders = st.text_input("Stakeholders", case_details.get("Stakeholders", ""))
                people_present = st.text_input("People Present", case_details.get("People Present", ""))
                insider_language = st.text_input("Insider Language", case_details.get("Insider Language", ""))
                tags = st.text_input("Tags", case_details.get("Tags", ""))


                # # Editable field for tags using st_tags
                # tags = st_tags(
                #     label="Enter tags:",
                #     text="Press enter to add more",
                #     value=case_details.get("Tags", "").split(",") if case_details.get("Tags") else [],  # Split tags into a list
                #     suggestions=['Urology', 'Minimally Invasive', 'Neurogenic Bladder', 'Surgery', 'Postoperative'],
                #     maxtags=10,  # Max number of tags the user can add
                # )

            
                        # Get and validate the date field
                case_date_str = case_details.get("Date", "")
                try:
                    # Try to parse the date from ISO format, or default to today's date
                    case_date = date.fromisoformat(case_date_str) if case_date_str else date.today()
                except ValueError:
                    case_date = date.today()

                case_date_input = st.date_input("Date", case_date)
            
                # Step 3: Save changes
                if st.button("Save Changes"):
                    updated_data = {
                        "Title": case_title,
                        "Date": case_date_input.isoformat(),
                        "Case Description": case_description,
                        "Location": location,
                        "Stakeholders": stakeholders,
                        "People Present": people_present,
                        "Insider Language": insider_language,
                        "Tags": tags,
                        "Observations": observations,
                    }
                    if update_case(case_to_edit, updated_data):
                        st.success(f"Changes to '{case_to_edit}' saved successfully!")
                    else:
                        st.error(f"Failed to save changes to '{case_to_edit}'.")


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
    
