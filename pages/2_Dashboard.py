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

 


# Function to get Google Sheets connection
def get_google_sheet(sheet_name, worksheet_name):
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.metadata.readonly",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open(sheet_name).worksheet(st.session_state['worksheet_name'])
    return sheet

# Function to read the note from Google Sheets
def read_note_from_gsheet(sheet_name, worksheet_name):
    sheet = get_google_sheet(sheet_name, st.session_state['worksheet_name'])
    try:
        st.session_state['note'] = sheet.cell(1, 1).value  # Read the content of cell A1
    except:
        st.session_state['note'] = ""
    return st.session_state['note']


       

# Function to save the note to Google Sheets
def save_note_to_gsheet(note, sheet_name, worksheet_name):
    sheet = get_google_sheet(sheet_name, st.session_state['worksheet_name'])
    sheet.update_cell(1, 1, st.session_state['note'])  # Save the content to cell A1

def refreshSheet():
    worksheet_name = worksheet_mapping[selected_user]
    read_note_from_gsheet(sheet_name, st.session_state['worksheet_name'])

def displaytextbox():
    # st.session_state['user_note']
    # Display a text area for the user to write their note, leveraging session state
    refreshSheet()
    st.session_state['user_note'] = st.text_area("Your Notes", value=st.session_state["note"], height=175)


st.set_page_config(page_title="HealthTech Wayfinder", page_icon="📍")

# Initialize cookies manager
cookies = CookieManager()


st.markdown("# Welcome!")
#

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

#initialize session states below functions


if "note" not in st.session_state:
    st.session_state["note"] = read_note_from_gsheet(sheet_name, st.session_state['worksheet_name'])


# col1, col2 = st.columns(2)
col1, col2, col3 = st.columns([2, 2, 1])


with col1:
    # st.header("Observation Tools")
    st.markdown('<h1 style="font-size:30px;">Observation Tools</h1>', unsafe_allow_html=True)


    with st.container(border=True):
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

        if st.button(":hourglass: Weekly Review (coming soon)"):
            ""
            # switch_page("Tips_for_Observations")
    #st.image("https://static.streamlit.io/examples/cat.jpg")

with col2:
    # st.header("Need Statement Tools")
    st.markdown('<h1 style="font-size:30px;">Need Statement Tools</h1>', unsafe_allow_html=True)

    
    with st.container(border=True):
        if st.button(":pencil2: Create a Need Statement"):
            switch_page("Need_Statement_Logger")

        if st.button(":pencil: Edit a Need Statement"):
            switch_page("Need_Statement_Editor")

        if st.button(":hourglass: Scope Need Statements (coming soon)"):
            ""

        if st.button(":hourglass: Need Statement Lens (coming soon)"):
            ""


with col3:

    # Streamlit app layout
    # Map selected user to worksheet
    worksheet_mapping = {
        "Deb": "Sheet1",
        "Kyle": "Sheet2",
        "Lois": "Sheet3",
        "Ryan": "Sheet4"
    }
    st.markdown('<h1 style="font-size:30px;">Notes</h1>', unsafe_allow_html=True)

    # st.selectbox("Select an option", ["Option 1", "Option 2", "Option 3"], on_change=update_value)

    # Dropdown for selecting a user
    selected_user = st.selectbox("Select user", users, on_change=displaytextbox)
    # refreshSheet()
    displaytextbox()
        
    
        
    # # Check if the refresh button is pressed
    # if st.button("Refresh"):
    #     # Reload the note from Google Sheets
    #     st.session_state["note"] = read_note_from_gsheet(sheet_name, st.session_state['worksheet_name'])
    #     # st.success("Refreshed!")
        
   
        
    # Save the note when the button is pressed
    if st.button("Save"):
        st.session_state["note"] = st.session_state['user_note']  # Update session state
        save_note_to_gsheet(st.session_state['user_note'], sheet_name, st.session_state['worksheet_name'])
        st.success(f"{selected_user}'s note has been saved successfully!")
    

st.markdown("---")


# Log Out Button with rerun or meta refresh
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    if st.button(":paperclip: Feedback & Support"):
        switch_page("Feedback_&_Support")


with col3:
    if st.button("Log Out"):
        # Option 1: Use experimental rerun
        log_out() 

        # Option 2: Use meta refresh (only if necessary)
        # st.markdown('<meta http-equiv="refresh" content="0; url=/streamlit_app" />', unsafe_allow_html=True)


######


# # Apply custom CSS to use Helvetica font
# st.markdown(
#     """
#     <style>
#     @import url('https://fonts.googleapis.com/css2?family=Helvetica:wght@400;700&display=swap');

#     html, body, [class*="css"]  {
#         font-family: 'Helvetica', sans-serif;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )




# # # Your logo URL
# # logo_url = "https://raw.githubusercontent.com/Aks-Dmv/bio-design-hms/main/Logo-HealthTech.png"  # Replace with the actual URL of your logo

# # Display the title with the logo below it
# # st.markdown(
# #     f"""
# #     <div style="text-align: center;">
# #         <h1>THIS IS A TEST 👺</h1>
# #          <img src="{logo_url}" alt="Logo" style="width:350px; height:auto;">
# #     </div>
# #     """,
# #     unsafe_allow_html=True,
# # )


# # st.markdown("---")

# # Apply custom CSS to use Helvetica font
# # st.markdown(
# #     """
# #     <style>
# #     @import url('https://fonts.googleapis.com/css2?family=Helvetica:wght@400;700&display=swap');

# #     html, body, [class*="css"]  {
# #         font-family: 'Helvetica', sans-serif;
# #     }
# #     </style>
# #     """,
# #     unsafe_allow_html=True,
# # )

# # Your logo URL
# logo_url = "https://raw.githubusercontent.com/Aks-Dmv/bio-design-hms/main/Logo-HealthTech.png"  # Replace with a different URL if necessary

# # Display the title with the logo below it
# st.markdown(
#         f"""
#         <div style="text-align: center;">
#             <h1>Dashboard</h1>
#              <img src="{logo_url}" alt="Logo" style="width:350px; height:auto;">
#         </div>
#         """,
#         unsafe_allow_html=True,
# )
    
# # st.markdown("---")

# st.markdown("<h3 style='text-align: center;'>What would you like to do?</h3>", unsafe_allow_html=True)



# # # def main():
# # st.markdown("<h1 style='text-align: center;'>HealthTech Wayfinder</h1>", unsafe_allow_html=True)
# # st.markdown("<h3 style='text-align: center;'>What would you like to do?</h3>", unsafe_allow_html=True)


# # ######

# col1, col2 = st.columns([1, 3])
# with col2:
#     if st.button("🔍 Record a New Observation"):
#         switch_page("Record_New_Observation")

#     if st.button("✅ Tips for your Observations"):
#         switch_page("Tips_for_Observations")

#     if st.button("❓ Chat with Observations"):
#         switch_page("Ask_the_Observations")

#     if st.button("📊 Glossary"):
#         switch_page("Glossary")

#     if st.button("📒 View All Observations"):
#         switch_page("View_All_Observations")

# st.markdown("---")
    
# # Create columns to position the Log Out button on the right
# col1, col2, col3 = st.columns([3, 1, 1])
# with col3:
#     if st.button("Log Out"):
#         # switch_page("/")

#     # Adjust the URL to the correct path of your main script
#         st.markdown('<meta http-equiv="refresh" content="0; url=/streamlit_app" />', unsafe_allow_html=True)


# #    if st.button("Go to Main"):
# #        st.markdown('<meta http-equiv="refresh" content="0; url=./" />', unsafe_allow_html=True)
