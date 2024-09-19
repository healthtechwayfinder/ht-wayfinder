import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from pydantic import BaseModel, Field
from typing import Optional
import csv
import os

from streamlit_cookies_manager import CookieManager

import time
from datetime import date
import logging
logging.basicConfig(level=logging.INFO)

import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="HealthTech Wayfinder", page_icon="📍", layout="wide")







st.markdown("# H1 Heading")
st.markdown("## H2 Heading")
st.markdown("### H3 Heading")
st.markdown("#### H4 Heading")
st.markdown("##### H5 Heading")
st.markdown("###### H6 Heading")





if "worksheet_name" not in st.session_state:
    st.session_state["worksheet_name"] = "Sheet1"

if "user_note" not in st.session_state:
    st.session_state["user_note"] = ""

# Define the Google Sheets credentials and scope
creds_dict = {
    "type" : st.secrets["gwf_service_account"]["type"],
    "project_id" : st.secrets["gwf_service_account"]["project_id"],
    "private_key_id" : st.secrets["gwf_service_account"]["private_key_id"],
    "private_key" : st.secrets["gwf_service_account"]["private_key"].replace('\\n', '\n'),  # Fix formatting
    "client_email" : st.secrets["gwf_service_account"]["client_email"],
    "client_id" : st.secrets["gwf_service_account"]["client_id"],
    "auth_uri" : st.secrets["gwf_service_account"]["auth_uri"],
    "token_uri" : st.secrets["gwf_service_account"]["token_uri"],
    "auth_provider_x509_cert_url" : st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url" : st.secrets["gwf_service_account"]["client_x509_cert_url"],
    "universe_domain": st.secrets["gwf_service_account"]["universe_domain"],
}

# Google Sheets settings
sheet_name = 'Team Scratchpad'
users = ["Deb", "Kyle", "Lois", "Ryan"]

# Initialize the CookieManager and check its status
cookies = CookieManager()

if not cookies.ready():
    # While cookies are being processed, show a placeholder to avoid the box flickering
    st.warning("Loading... please wait while we initialize.")
    st.stop()  # Stop the script execution until cookies are ready

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

# Callback function to update the note when user selection changes
def update_note():
    worksheet_name = worksheet_mapping[st.session_state["selected_user"]]
    st.session_state["note"] = read_note_from_gsheet(sheet_name, worksheet_name)

# Main app content starts here
st.markdown("# Welcome!")

# Function to handle logout
def log_out():
    # Clear session state to log out
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Clear cookies if used for login
    if "logged_in" in cookies:
        cookies["logged_in"] = None  # Clear the logged_in cookie by setting it to None
        cookies.save()  # Save changes to the browser

    # Redirect to the main URL of your app
    st.markdown('<meta http-equiv="refresh" content="0; url=https://healthtech-wayfinder.streamlit.app/">', unsafe_allow_html=True)

# Layout
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    st.markdown('<h1 style="font-size:30px;">Observation Tools</h1>', unsafe_allow_html=True)
    with st.container():
        if st.button("🏥 Record a New Case"):
            switch_page("Case_Logger")
        
        if st.button("🔍 Record a New Observation"):
            switch_page("Observation_Logger")
    
        if st.button("❓ Chat with Observations"):
            switch_page("Observation_Investigator")
    
        if st.button("📒 View Observation, Case, & Need Logs"):
            switch_page("Cases_&_Observations_Dataset")
            
        if st.button("📊 View Glossary"):
            switch_page("Glossary")

with col2:
    st.markdown('<h1 style="font-size:30px;">Need Statement Tools</h1>', unsafe_allow_html=True)
    with st.container():
        if st.button(":pencil2: Create a Need Statement"):
            switch_page("Need_Statement_Logger")

        if st.button(":pencil: Edit a Need Statement"):
            switch_page("Need_Statement_Editor")

with col3:
    st.markdown('<h1 style="font-size:30px;">Notes</h1>', unsafe_allow_html=True)
    
    worksheet_mapping = {
        "Deb": "Sheet1",
        "Kyle": "Sheet2",
        "Lois": "Sheet3",
        "Ryan": "Sheet4"
    }

    # User selection dropdown
    if "selected_user" not in st.session_state:
        st.session_state["selected_user"] = users[0]
    
    st.selectbox(
        "Select User", 
        users, 
        key="selected_user", 
        on_change=update_note
    )

    # Initialize the note if not set
    if "note" not in st.session_state:
        update_note()

    # Display the text area for notes
    user_note = st.text_area("Add Notes", value=st.session_state["note"], height=300)

    # Save the note when the button is pressed
    if st.button("Save Note"):
        worksheet_name = worksheet_mapping[st.session_state["selected_user"]]
        st.session_state["note"] = user_note  # Update session state
        save_note_to_gsheet(user_note, sheet_name, worksheet_name)
        st.success(f"Note updated!")

st.markdown("---")



















# import time
# import streamlit as st
# from datetime import date
# import logging
# logging.basicConfig(level=logging.INFO)

# import gspread
# from oauth2client.service_account import ServiceAccountCredentials

# # Define the Google Sheets credentials and scope
# creds_dict = {
#     "type" : st.secrets["gwf_service_account"]["type"],
#     "project_id" : st.secrets["gwf_service_account"]["project_id"],
#     "private_key_id" : st.secrets["gwf_service_account"]["private_key_id"],
#     "private_key" : st.secrets["gwf_service_account"]["private_key"].replace('\\n', '\n'),  # Fix formatting
#     "client_email" : st.secrets["gwf_service_account"]["client_email"],
#     "client_id" : st.secrets["gwf_service_account"]["client_id"],
#     "auth_uri" : st.secrets["gwf_service_account"]["auth_uri"],
#     "token_uri" : st.secrets["gwf_service_account"]["token_uri"],
#     "auth_provider_x509_cert_url" : st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
#     "client_x509_cert_url" : st.secrets["gwf_service_account"]["client_x509_cert_url"],
#     "universe_domain": st.secrets["gwf_service_account"]["universe_domain"],
# }

# # Google Sheets settings
# sheet_name = 'Team Scratchpad'
# users = ["Deb", "Kyle", "Lois", "Ryan"]

# # Function to get Google Sheets connection
# def get_google_sheet(sheet_name, worksheet_name):
#     scope = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.metadata.readonly",
#     ]
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#     client = gspread.authorize(creds)
#     sheet = client.open(sheet_name).worksheet(worksheet_name)
#     return sheet

# # Function to read the note from Google Sheets
# def read_note_from_gsheet(sheet_name, worksheet_name):
#     sheet = get_google_sheet(sheet_name, worksheet_name)
#     try:
#         note = sheet.cell(1, 1).value  # Read the content of cell A1
#     except:
#         note = ""
#     return note

# # Function to save the note to Google Sheets
# def save_note_to_gsheet(note, sheet_name, worksheet_name):
#     sheet = get_google_sheet(sheet_name, worksheet_name)
#     sheet.update_cell(1, 1, note)  # Save the content to cell A1

# # Callback function to update the note when user selection changes
# def update_note():
#     worksheet_name = worksheet_mapping[st.session_state["selected_user"]]
#     st.session_state["note"] = read_note_from_gsheet(sheet_name, worksheet_name)

# # Streamlit app layout
# st.title("Scratchpad 📝")

# # Map selected user to worksheet
# worksheet_mapping = {
#     "Deb": "Sheet1",
#     "Kyle": "Sheet2",
#     "Lois": "Sheet3",
#     "Ryan": "Sheet4"
# }

# # Dropdown for selecting a user with on_change callback to update note
# if "selected_user" not in st.session_state:
#     st.session_state["selected_user"] = users[0]  # Default to the first user

# st.selectbox(
#     "Select user", 
#     users, 
#     key="selected_user", 
#     on_change=update_note
# )

# # Initialize session state for note if not already set
# if "note" not in st.session_state:
#     update_note()

# # Display a text area for the user to write their note, leveraging session state
# user_note = st.text_area("Your Note", value=st.session_state["note"], height=300)

# # Save the note when the button is pressed
# if st.button("Save Note"):
#     worksheet_name = worksheet_mapping[st.session_state["selected_user"]]
#     st.session_state["note"] = user_note  # Update session state
#     save_note_to_gsheet(user_note, sheet_name, worksheet_name)
#     st.success(f"{st.session_state['selected_user']}'s note has been saved successfully!")

# # Check if the refresh button is pressed
# if st.button("Refresh Note"):
#     worksheet_name = worksheet_mapping[st.session_state["selected_user"]]
#     st.session_state["note"] = read_note_from_gsheet(sheet_name, worksheet_name)
#     st.success(f"{st.session_state['selected_user']}'s note has been refreshed!")


# import time
# import streamlit as st
# from datetime import date
# import logging
# logging.basicConfig(level=logging.INFO)

# import gspread
# from oauth2client.service_account import ServiceAccountCredentials

# # Define the Google Sheets credentials and scope
# creds_dict = {
#     "type" : st.secrets["gwf_service_account"]["type"],
#     "project_id" : st.secrets["gwf_service_account"]["project_id"],
#     "private_key_id" : st.secrets["gwf_service_account"]["private_key_id"],
#     "private_key" : st.secrets["gwf_service_account"]["private_key"].replace('\\n', '\n'),  # Fix formatting
#     "client_email" : st.secrets["gwf_service_account"]["client_email"],
#     "client_id" : st.secrets["gwf_service_account"]["client_id"],
#     "auth_uri" : st.secrets["gwf_service_account"]["auth_uri"],
#     "token_uri" : st.secrets["gwf_service_account"]["token_uri"],
#     "auth_provider_x509_cert_url" : st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
#     "client_x509_cert_url" : st.secrets["gwf_service_account"]["client_x509_cert_url"],
#     "universe_domain": st.secrets["gwf_service_account"]["universe_domain"],
# }

# # Google Sheets settings
# sheet_name = 'Team Scratchpad'
# users = ["Deb", "Kyle", "Lois", "Ryan"]


# # Function to get Google Sheets connection
# def get_google_sheet(sheet_name, worksheet_name):
#     scope = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.metadata.readonly",
#     ]
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#     client = gspread.authorize(creds)
#     sheet = client.open(sheet_name).worksheet(worksheet_name)
#     return sheet

# # Function to read the note from Google Sheets
# def read_note_from_gsheet(sheet_name, worksheet_name):
#     sheet = get_google_sheet(sheet_name, worksheet_name)
#     try:
#         note = sheet.cell(1, 1).value  # Read the content of cell A1
#     except:
#         note = ""
#     return note

# # Function to save the note to Google Sheets
# def save_note_to_gsheet(note, sheet_name, worksheet_name):
#     sheet = get_google_sheet(sheet_name, worksheet_name)
#     sheet.update_cell(1, 1, note)  # Save the content to cell A1





# # Streamlit app layout
# st.title("Scratchpad 📝")


# # Dropdown for selecting a user
# selected_user = st.selectbox("Select user", users)

# # Map selected user to worksheet
# worksheet_mapping = {
#     "Deb": "Sheet1",
#     "Kyle": "Sheet2",
#     "Lois": "Sheet3",
#     "Ryan": "Sheet4"
# }
# worksheet_name = worksheet_mapping[selected_user]

# # Initialize session state if it doesn't exist
# if "note" not in st.session_state:
#     st.session_state["note"] = read_note_from_gsheet(sheet_name, worksheet_name)


# # Check if the refresh button is pressed
# if st.button("Refresh Note"):
#     # Reload the note from Google Sheets
#     st.session_state["note"] = read_note_from_gsheet(sheet_name, worksheet_name)
#     # st.success("Refreshed!")

# # Display a text area for the user to write their note, leveraging session state
# user_note = st.text_area("Your Note", value=st.session_state["note"], height=300)

# # Save the note when the button is pressed
# if st.button("Save Note"):
#     st.session_state["note"] = user_note  # Update session state
#     save_note_to_gsheet(user_note, sheet_name, worksheet_name)
#     st.success(f"{selected_user}'s note has been saved successfully!")










# import time
# import streamlit as st
# from streamlit_extras.switch_page_button import switch_page
# from datetime import date
# import logging
# logging.basicConfig(level=logging.INFO)

# import gspread
# from oauth2client.service_account import ServiceAccountCredentials


# creds_dict = {
#     "type" : st.secrets["gwf_service_account"]["type"],
#     "project_id" : st.secrets["gwf_service_account"]["project_id"],
#     "private_key_id" : st.secrets["gwf_service_account"]["private_key_id"],
#     "private_key" : st.secrets["gwf_service_account"]["private_key"].replace('\\n', '\n'),  # Ensure newlines
#     "client_email" : st.secrets["gwf_service_account"]["client_email"],
#     "client_id" : st.secrets["gwf_service_account"]["client_id"],
#     "auth_uri" : st.secrets["gwf_service_account"]["auth_uri"],
#     "token_uri" : st.secrets["gwf_service_account"]["token_uri"],
#     "auth_provider_x509_cert_url" : st.secrets["gwf_service_account"]["auth_provider_x509_cert_url"],
#     "client_x509_cert_url" : st.secrets["gwf_service_account"]["client_x509_cert_url"],
#     "universe_domain": st.secrets["gwf_service_account"]["universe_domain"],
# }

# # Team Scratchpad
# sheet_name = 'Team Scratchpad'
# worksheet_name = 'Sheet1'
# # List of users (you can replace or load these dynamically)
# users = ["Deb", "Kyle", "Lois", "Ryan"]

# # Function to get Google Sheets connection
# def get_google_sheet(sheet_name, worksheet_name):
#     scope = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.metadata.readonly",
#     ]
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#     client = gspread.authorize(creds)
#     sheet = client.open(sheet_name).worksheet(worksheet_name)
#     return sheet

# # Function to read the note from Google Sheets
# def read_note_from_gsheet(sheet_name, worksheet_name):
#     sheet = get_google_sheet(sheet_name, worksheet_name)
#     try:
#         note = sheet.cell(1, 1).value  # Read the content of cell A1
#     except:
#         note = ""
#     return note

# # Function to save the note to Google Sheets
# def save_note_to_gsheet(note, sheet_name, worksheet_name):
#     sheet = get_google_sheet(sheet_name, worksheet_name)
#     sheet.update_cell(1, 1, note)  # Save the content to cell A1

# # Streamlit app layout
# st.title("Scratchpad 📝")

# # Dropdown for selecting a user
# selected_user = st.selectbox("Select user", users)

# # Update the worksheet name based on the selected user
# if selected_user == "Deb":
#     worksheet_name = 'Sheet1'
# elif selected_user == "Kyle":
#     worksheet_name = 'Sheet2'  # Fixed typo here
# elif selected_user == "Lois":
#     worksheet_name = 'Sheet3'
# elif selected_user == "Ryan":
#     worksheet_name = 'Sheet4'

# # Load the note from Google Sheets
# note = read_note_from_gsheet(sheet_name, worksheet_name)

# # Check if the refresh button is pressed
# if st.button("Refresh Note"):
#     note = read_note_from_gsheet(sheet_name, worksheet_name)
#     st.success(f"{selected_user}'s note has been refreshed!")

# # Display a text area for the user to write their note
# user_note = st.text_area("Your Note", value=note, height=300)

# # Save the note when the button is pressed
# if st.button("Save Note"):
#     save_note_to_gsheet(user_note, sheet_name, worksheet_name)
#     st.success(f"{selected_user}'s note has been saved successfully!")









# import time
# import streamlit as st
# from streamlit_extras.switch_page_button import switch_page
# from datetime import date
# import logging
# logging.basicConfig(level=logging.INFO)

# import gspread
# from oauth2client.service_account import ServiceAccountCredentials


# from pydantic import BaseModel, Field
# from typing import Optional
# from datetime import date, datetime

# import json
# import os
# import csv

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


# # Team Scratchpad
# # open google sheets to the notepad file
# # import any notes from the cell
# #  if notes, populate the widget
# #  if no notes, leave blank
# #  user can edit
# #  if user clicks update, they save their notes

# sheet_name = 'Team Scratchpad'
# worksheet_name = 'Sheet1'
# # List of users (you can replace or load these dynamically)
# users = ["Deb", "Kyle", "Lois", "Ryan"]


# def get_google_sheet(sheet_name, worksheet_name):
#     scope = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.metadata.readonly",
#     ]
#     creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
#     client = gspread.authorize(creds)
#     sheet = client.open(sheet_name).worksheet(worksheet_name)
#     return sheet



# # Function to read the note from Google Sheets
# def read_note_from_gsheet(sheet_name, worksheet_name):
#     sheet = get_google_sheet(sheet_name, worksheet_name)
#     try:
#         note = sheet.cell(1, 1).value  # Read the content of cell A1
#     except:
#         note = ""
#     return note

# # Function to save the note to Google Sheets
# def save_note_to_gsheet(note, sheet_name, worksheet_name):
#     sheet = get_google_sheet(sheet_name, worksheet_name)
#     sheet.update_cell(1, 1, note)  # Save the content to cell A1



# # Streamlit app layout
# st.title("Scratchpad 📝")

# # Dropdown for selecting a user
# selected_user = st.selectbox("Select user", users)


# if selected_user:

#     if selected_user == "Deb":
#         worksheet_name = 'Sheet1'
#     elif selected_user == "Kyle":
#         worksheet_name = 'Sheet2'
#     elif selected_user == "Lois":
#         worksheet_name = 'Sheet3'
#     elif selected_user == "Ryan":
#         worksheet_name = 'Sheet4'

#     # Load the note from Google Sheets
#     note = read_note_from_gsheet(sheet_name, worksheet_name)


# # Check if the refresh button is pressed
# if st.button("Refresh Note"):
#     # Reload the note from Google Sheets if "Refresh" is clicked
#     note = read_note_from_gsheet(sheet_name, worksheet_name)
#     # st.success(f"{selected_user}'s note has been refreshed!")
# else:
#     # Load the note from the selected user's worksheet (initial load)
#     note = read_note_from_gsheet(sheet_name, worksheet_name)


# # Display a text area for the user to write their note
# user_note = st.text_area("Your Note", value=note, height=300)

# # Save the note when the button is pressed
# if st.button("Save Note"):
#     save_note_to_gsheet(user_note, sheet_name, worksheet_name)
#     st.success("Your note has been saved successfully!")

# # Provide feedback that the note is auto-loaded from Google Sheets on app load
# # st.caption("This notepad autosaves your note to Google Sheets and reloads it when you reopen the app.")


