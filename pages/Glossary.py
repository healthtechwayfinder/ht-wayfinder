import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import pandas as pd
import openai
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnableLambda
from langchain.prompts import PromptTemplate
from langchain_pinecone import PineconeVectorStore
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
import json
import os
import csv

# Set up the Streamlit page
st.set_page_config(page_title="Glossary", page_icon="📊")
st.markdown("# Glossary")

# Authenticate and connect to Google Sheets using service account credentials
creds_dict = st.secrets["gcp_service_account"]
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.metadata.readonly"
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
observation_sheet = client.open("Glossary").sheet1

# Initialize session state variables if not already initialized
if "show_new_term_fields" not in st.session_state:
    st.session_state["show_new_term_fields"] = False
if "new_term" not in st.session_state:
    st.session_state["new_term"] = ""
if "new_definition" not in st.session_state:
    st.session_state["new_definition"] = ""

# Retrieve terms and definitions from Google Sheets
terms = sheet.col_values(1)  # Get all values in column 1
definitions = sheet.col_values(2)  # Get all values in column 2

# Check if columns have data and skip the header row
if len(terms) > 1 and len(definitions) > 1:
    terms = terms[1:]  # Skip header row
    definitions = definitions[1:]  # Skip header row
else:
    st.error("No data found in the Glossary sheet.")
    terms = []
    definitions = []

# Combine terms and definitions into a list of tuples and sort alphabetically
terms_definitions = sorted(list(zip(terms, definitions)), key=lambda x: x[0].lower())


# Add custom CSS for scrollable container and search bar
st.markdown("""
    <style>
    .scrollable-container {
        height: 300px;
        overflow-y: scroll;
        border: 1px solid #ccc;
        padding: 10px;
        font-size: 16px;
    }
    input[type="text"] {
        background-color: white !important;
        color: black !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Search bar for filtering terms
search_term = st.text_input("Search Glossary").lower()

# Filter terms based on the search query
filtered_terms_definitions = [item for item in terms_definitions if search_term in item[0].lower()]

# Button to toggle input fields for adding a new term
if st.button("Add a New Term"):
    st.session_state["show_new_term_fields"] = not st.session_state["show_new_term_fields"]

# Button to toggle input fields
if st.button("Add a New Term"):
    st.session_state["show_new_term_fields"] = not st.session_state["show_new_term_fields"]

# Conditionally display the input fields for adding a new term
if st.session_state["show_new_term_fields"]:
    st.text_input("Enter a new term:", key="new_term")
    st.text_area("Enter the definition for the new term:", key="new_definition")

    # Submit New Term button
    if st.button("Submit New Term"):
        if st.session_state["new_term"].strip() and st.session_state["new_definition"].strip():
            # Add the new term and definition to Google Sheets
            sheet.append_row([st.session_state["new_term"], st.session_state["new_definition"]])
            st.success(f"Term '{st.session_state['new_term']}' has been added.")
            st.session_state["new_term"] = ""
            st.session_state["new_definition"] = ""
            st.session_state["show_new_term_fields"] = False
            st.experimental_rerun()
        else:
            st.error("Please enter both a term and a definition.")

# Scrollable container to display terms and their definitions
with st.container():
    st.markdown("<div class='scrollable-container'>", unsafe_allow_html=True)

    # Display each term with its definition and edit button
    for idx, (term, definition) in enumerate(filtered_terms_definitions):
        col1, col2 = st.columns([8, 2])

        with col1:
            st.markdown(f"**{term}**: {definition}")

        with col2:
            if f"edit_button_{idx}" not in st.session_state:
                st.session_state[f"edit_button_{idx}"] = False

            if st.button("Edit", key=f"edit_button_trigger_{idx}"):
                st.session_state[f"edit_button_{idx}"] = True

        # Editable fields below the term and definition when "Edit" is clicked
        if st.session_state[f"edit_button_{idx}"]:
            with st.form(key=f"edit_form_{idx}"):
                edited_term = st.text_input("Edit term:", value=term, key=f"edit_term_{idx}")
                edited_definition = st.text_area("Edit definition:", value=definition, key=f"edit_definition_{idx}")
                save_button = st.form_submit_button("Save")
                cancel_button = st.form_submit_button("Cancel")

                if save_button:
                    # Save changes to Google Sheets
                    row_index = terms.index(term) + 2  # +2 to account for header and zero-indexing
                    sheet.update(f'A{row_index}', edited_term)
                    sheet.update(f'B{row_index}', edited_definition)
                    st.session_state[f"edit_button_{idx}"] = False
                    st.success(f"Term '{edited_term}' has been updated.")

                if cancel_button:
                    st.session_state[f"edit_button_{idx}"] = False

    st.markdown("</div>", unsafe_allow_html=True)

# Add custom CSS to style a large button
st.markdown("""
    <style>
    .big-button-container {
        display: flex;
        justify-content: center;
    }
    .big-button {
        font-size: 20px;
        padding: 10px 60px;
        background-color: #365980; /* blueish color */
        color: white;
        border: none;
        border-radius: 8px;
        cursor: pointer;
        text-align: center;
    }
    .big-button:hover {
        background-color: #c2c2c2; /* Grey */
    }
    </style>
    """, unsafe_allow_html=True)

# Create a button to go back to the main menu
st.markdown("""
    <div class="big-button-container">
        <button class="big-button" onclick="window.location.href='/?page=main_menu'">Back to Main Menu</button>
    </div>
    """, unsafe_allow_html=True)


###################
# import streamlit as st
# from streamlit_extras.switch_page_button import switch_page

# import pandas as pd

# import openai

# from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# from langchain.chains import LLMChain
# from langchain.output_parsers import PydanticOutputParser
# # from langchain.callbacks import get_openai_callback
# from langchain.schema import StrOutputParser
# from langchain.schema.runnable import RunnableLambda
# from langchain.prompts import PromptTemplate
# from langchain_pinecone import PineconeVectorStore

# import gspread
# from oauth2client.service_account import ServiceAccountCredentials


# from pydantic import BaseModel, Field
# from typing import Optional
# from datetime import date

# import json
# import os
# import csv


# st.set_page_config(page_title="Glossary", page_icon="📊")

# st.markdown("# Glossary")

# # If using st.secrets
# creds_dict = st.secrets["gcp_service_account"]

# # Set up the connection to Google Sheets
# scope = [
#         "https://www.googleapis.com/auth/spreadsheets",
#         "https://www.googleapis.com/auth/drive.metadata.readonly"
#         ]
# creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
# client = gspread.authorize(creds)
# observation_sheet = client.open("BioDesign Observation Record").sheet1

# # Retrieve all values in a specific column
# # For example, to get all values in column A (the first column):
# column_values = observation_sheet.col_values(10)  # 1 represents the first column
# observation_ids = observation_sheet.col_values(1)  # 1 represents the first column

# # # Display the values in the Streamlit app
# # st.write("New Terms:")
# # st.write(column_values)

# # Initialize a dictionary to hold the terms and their counts
# term_counts = {}
# relevant_observation_ids = {}

# # Skip the first row (header) and process the rest
# for i, value in enumerate(column_values[1:]):
#     if value:  # Check if the string is not empty
#         terms = [term.strip() for term in value.split(",")]
#         for term in terms:
#             if term in term_counts:
#                 term_counts[term] += 1
#                 relevant_observation_ids[term].append(observation_ids[i+1])
#             else:
#                 term_counts[term] = 1
#                 relevant_observation_ids[term] = [observation_ids[i+1]]

# # # Display the unique terms with their counts
# # st.write("Unique terms and their counts:")
# # for term, count in term_counts.items():
# #     st.write(f"- {term} ({count})")

# # Set up OpenAI API key
# openai.api_key = st.secrets["openai_key"]
# #openai.api_key = st.secrets["openai"]["api_key"]
# #OPENAI_API_KEY = st.secrets["openai_key"]

# # Function to get a definition from OpenAI
# def get_definition(term):
#     openai_client = openai.OpenAI(api_key=openai.api_key)
    
#     try:
#         messages = [
#             {"role": "system", "content": "You are a helpful assistant that provides concise definitions of medical terms."},
#             {"role": "user", "content": f"Define the following medical term: {term}"}
#         ]
#         response = openai_client.chat.completions.create(
#             model='gpt-4o-mini',
#             messages=messages,
#         )
#         definition = response.choices[0].message.content
    
#         return definition
#     except Exception as e:
#         return f"Error: {e}"

# # Display the unique terms with their counts and definitions
# st.write("Unique terms, their counts, and definitions:")

# # Sort the terms alphabetically
# sorted_terms = sorted(term_counts.keys())

# for term in sorted_terms:
#     capitalized_term = term.capitalize()
#     definition = get_definition(term)
#     st.write(f"""
# - **{capitalized_term}** ({term_counts[term]}): {definition}  \n
# _Relevant observation IDs:_ {','.join(relevant_observation_ids[term])}
#     """)


# st.markdown("---")

# # Add custom CSS for a larger button
# st.markdown("""
#     <style>
#     .big-button-container {
#         display: flex;
#         justify-content: center;
#     }
#     .big-button {
#         font-size: 20px;
#         padding: 10px 60px;
#         background-color: #365980; /* blueish color */
#         color: white;
#         border: none;
#         border-radius: 8px;
#         cursor: pointer;
#         text-align: center;
#     }
#     .big-button:hover {
#         background-color: #c2c2c2; /* Grey */
#     }
#     </style>
#     """, unsafe_allow_html=True)

# # Create a container to hold the button with the custom class
# st.markdown("""
#     <div class="big-button-container">
#         <button class="big-button" onclick="window.location.href='/?page=main_menu'">Back to Main Menu</button>
#     </div>
#     """, unsafe_allow_html=True)

