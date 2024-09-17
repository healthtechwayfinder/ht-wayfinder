import time
import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from datetime import date
import logging
logging.basicConfig(level=logging.INFO)

import gspread
from oauth2client.service_account import ServiceAccountCredentials


from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

import json
import os
import csv

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


# Team Scratchpad
# open google sheets to the notepad file
# import any notes from the cell
#  if notes, populate the widget
#  if no notes, leave blank
#  user can edit
#  if user clicks update, they save their notes

sheet_name = 'Team Scratchpad'
worksheet_name = 'Sheet1'
# List of users (you can replace or load these dynamically)
users = ["Deb", "Kyle", "Lois", "Ryan"]


def get_google_sheet(sheet_name, worksheet_name):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).worksheet(worksheet_name)
    return sheet



# Function to read the note from Google Sheets
def read_note_from_gsheet(sheet_name, worksheet_name):
    sheet = get_google_sheet(sheet_name, worksheet_name)
    try:
        note = sheet.cell(1, 1).value  # Read the content of cell A1
    except:
        note = ""
    return note

# Function to save the note to Google Sheets
def save_note_to_gsheet(note, sheet_name, worksheet_name):
    sheet = get_google_sheet(sheet_name, worksheet_name)
    sheet.update_cell(1, 1, note)  # Save the content to cell A1



# Streamlit app layout
st.title("Scratchpad 📝")

# Dropdown for selecting a user
selected_user = st.selectbox("Select user", users)



if selected_user:

    if selected_user == "Deb":
        worksheet_name = 'Sheet1'
    elif selected_user == "Kyle":
        wworksheet_name = 'Sheet2'
    elif selected_user == "Lois":
        worksheet_name = 'Sheet3'
    elif selected_user == "Ryan":
        worksheet_name = 'Sheet4'

    # Load the note from Google Sheets
    note = read_note_from_gsheet(sheet_name, worksheet_name)



# Display a text area for the user to write their note
user_note = st.text_area("Your Note", value=note, height=300)

# Save the note when the button is pressed
if st.button("Save Note"):
    save_note_to_gsheet(user_note, sheet_name, worksheet_name)
    st.success("Your note has been saved successfully!")

# Provide feedback that the note is auto-loaded from Google Sheets on app load
st.caption("This notepad autosaves your note to Google Sheets and reloads it when you reopen the app.")


