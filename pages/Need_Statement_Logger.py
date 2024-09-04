# //// PROCESS ////
# 0. brief instructions appear at the top of the page with a link to the uder guide for more info
# 1. select one or more observations (type them in? drop down?)
#     -> summaries of observations are then displayed
# 2. select the date (default to today's date)
# 3. select the author (or NOT???? --  let's think this over)
# 4. enter statement:
#      -> 1st box: enter problem
#      -> 2nd box: enter population
#      -> 3rd box: enter outcome
#      -> 4th box: enter full need statement
#      -> 5th box for notes?
#    -> statement goes to sheet and information is recorded in corresonding columns
# 5. option to enter more statements with a (+) button (with a unique ID for each statement, user doesn't need to see this, honestly)
# 6. statement goes to the google sheet, no AI necessary -- user sees message "Need statement(s) recorded!)
# Other Notes:
# -> code could lay foundation for detecting and sorting problem, population, and solution rather than manual entry
# -> could the observation bot page have a widget in the right-hand sidebar for entering need satements from that page? (in case something comes up from a conversation)

# I propose copying the code over form the Add Observation page, but removing the AI components -- only entering info from the user right to the log

import os
import csv
from datetime import date
from typing import Optional

import streamlit as st
from streamlit_extras.switch_page_button import switch_page

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pydantic import BaseModel, Field
from streamlit_extras.switch_page_button import switch_page



# Streamlit configuration
st.set_page_config(page_title="Log a Need Statement", page_icon="✏️")
st.markdown("# Add a New Need Statement")

# Constants
observations_csv = "observations.csv"

# Access GCP credentials from Streamlit secrets
creds_dict = {
    key: st.secrets["gcp_service_account"][key]
    for key in st.secrets["gcp_service_account"]
}

# Initialize session state variables
for key, default in {
    'need_statement': "",
    'problem': "",
    'population': "",
    'outcome': "",
    'notes': "",
    'need_statement_date': date.today(),
    'rerun': False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Define the NeedStatement model
class NeedStatement(BaseModel):
    problem: Optional[str] = Field(None, description="Describe the problem.")
    population: Optional[str] = Field(None, description="Who is affected?")
    outcome: Optional[str] = Field(None, description="Desired outcome?")
    full_statement: Optional[str] = Field(None, description="Full need statement.")
    notes: Optional[str] = Field(None, description="Additional notes.")

# Create CSV file if it doesn't exist
if not os.path.exists(observations_csv):
    statement_keys = ['problem', 'population', 'outcome', 'full_statement', 'notes', 'author', 'statement_date', 'statement_id']
    with open(observations_csv, "w") as csv_file:
        csv_writer = csv.writer(csv_file, delimiter=";")
        csv_writer.writerow(statement_keys)

# Function to add to Google Sheets
def addToGoogleSheets(statement_dict):
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.metadata.readonly"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        statement_sheet = client.open("Need Statements Record").sheet1
        headers = statement_sheet.row_values(1)
        row_to_append = [str(statement_dict.get(header, "")) for header in headers]
        statement_sheet.append_row(row_to_append)
        return True
    except Exception as e:
        st.error(f"Error adding to Google Sheets: {str(e)}")
        return False

# Function for need statement ID generation and updating
def generate_statement_id(statement_date, counter):
    return f"NS{statement_date.strftime('%y%m%d')}{counter:04d}"

def update_statement_id():
    stmt_date_str = st.session_state['need_statement_date'].strftime('%y%m%d')
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.metadata.readonly"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    statement_sheet = client.open("Need Statements Record").sheet1
    stmt_date_ids = [stmt_id for stmt_id in statement_sheet.col_values(1) if stmt_id.startswith(f"NS{stmt_date_str}")]
    counter = int(stmt_date_ids[-1][-4:]) + 1 if stmt_date_ids else 1
    st.session_state['statement_id'] = generate_statement_id(st.session_state['need_statement_date'], counter)

# Streamlit UI components
col1, col2 = st.columns(2)

with col1:
    st.date_input("Statement Date", date.today(), on_change=update_statement_id, key="need_statement_date")

with col2:
    if 'statement_id' not in st.session_state:
        update_statement_id()
    st.text_input("Statement ID:", value=st.session_state['statement_id'], disabled=True)

st.text_input("Problem:", key="problem")
st.text_input("Population:", key="population")
st.text_input("Outcome:", key="outcome")
st.text_area("Full Need Statement:", height=100, key="need_statement")
st.text_area("Notes (Optional):", height=100, key="notes")

# Submit Button
if st.button("Submit Need Statement"):
    need_statement_data = {
        "problem": st.session_state['problem'],
        "population": st.session_state['population'],
        "outcome": st.session_state['outcome'],
        "full_statement": st.session_state['need_statement'],
        "notes": st.session_state['notes'],
        "author": "Auto-generated",  # Placeholder for author, modify as needed
        "statement_date": st.session_state['need_statement_date'],
        "statement_id": st.session_state['statement_id'],
    }

    if addToGoogleSheets(need_statement_data):
        st.success("Need statement(s) recorded!")
        st.session_state['rerun'] = True
        st.rerun()
    else:
        st.error("Error recording the need statement, please try again.")

# Clear Button
if st.button("Clear Form"):
    for key in ['need_statement', 'problem', 'population', 'outcome', 'notes']:
        st.session_state[key] = ""

st.markdown("---")

if st.button("Back to Main Menu"):
    switch_page("main_menu")
