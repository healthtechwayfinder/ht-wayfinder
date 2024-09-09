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

# Print test 
terms = observation_sheet.col_values(1)  # Terms are in column 1
definitions = observation_sheet.col_values(2)  # Definitions are in column 2

# Combine terms and definitions into a list of tuples
terms_definitions = list(zip(terms[1:], definitions[1:]))  # Skip header row

# Sort the list alphabetically by the term
sorted_terms_definitions = sorted(terms_definitions, key=lambda x: x[0].lower())


# Add custom CSS to make the container scrollable
st.markdown("""
    <style>
    .scrollable-container {
        height: 300px;
        overflow-y: scroll;
        border: 1px solid #ccc;
        padding: 10px;
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

# Add custom CSS for white search bar
st.markdown("""
    <style>
    input[type="text"] {
        background-color: white !important;
        color: black !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Search bar for filtering terms
search_term = st.text_input("Search Glossary")

# Button to toggle input fields
if st.button("Add a New Term"):
    st.session_state["show_new_term_fields"] = not st.session_state["show_new_term_fields"]

# Conditionally display the input fields for adding a new term and definition
if st.session_state["show_new_term_fields"]:
    st.text_input("Enter a new term:", key="new_term")
    st.text_area("Enter the definition for the new term:", key="new_definition")

    # Submit New Term button
    if st.button("Submit New Term"):
        # Ensure that both new_term and new_definition are filled
        if st.session_state["new_term"].strip() and st.session_state["new_definition"].strip():
            # Add the new term and definition to the list
            sorted_terms_definitions.append((st.session_state["new_term"], st.session_state["new_definition"]))
            sorted_terms_definitions = sorted(sorted_terms_definitions, key=lambda x: x[0].lower())

            # Update Google Sheets with the new term and definition
            observation_sheet.append_row([st.session_state["new_term"], st.session_state["new_definition"]])
            st.success(f"Term '{st.session_state['new_term']}' has been added successfully!")

            # Reset input fields and hide them by triggering a rerun
            st.session_state["new_term"] = ""  # Reset new term field
            st.session_state["new_definition"] = ""  # Reset new definition field
            st.session_state["show_new_term_fields"] = False
            st.experimental_rerun()  # Rerun the app to reflect changes

        else:
            st.error("Please enter both a term and a definition.")

# Search bar for filtering terms
search_term = st.text_input("Search Glossary", key="search_term")

# Filter the glossary based on the search term (case-insensitive)
filtered_terms_definitions = [item for item in sorted_terms_definitions if search_term.lower() in item[0].lower()]



# Add custom CSS to make the container scrollable
st.markdown("""
    <style>
    .scrollable-container {
        height: 300px;
        overflow-y: scroll;
        border: 1px solid #ccc;
        padding: 10px;
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

# Scrollable container to display terms and their definitions with Edit buttons
with st.container():
    st.markdown("<div class='scrollable-container'>", unsafe_allow_html=True)

    # Display the terms and their definitions with Edit buttons
    for idx, (term, definition) in enumerate(filtered_terms_definitions):
        # Create unique keys for each term to avoid key conflicts
        term_key = f"term_{idx}"
        definition_key = f"definition_{idx}"
        edit_button_key = f"edit_button_{idx}"
        edit_mode_key = f"edit_mode_{idx}"

        # Check if we're in edit mode for this specific term
        if edit_mode_key not in st.session_state:
            st.session_state[edit_mode_key] = False

        # Create columns for term/definition and the Edit button
        col1, col2 = st.columns([8, 2])

        with col1:
            if not st.session_state[edit_mode_key]:
                # Display term and definition in normal mode
                st.markdown(f"**{term}**: {definition}")
            else:
                # Display editable fields when in edit mode
                st.text_input("Edit term", value=term, key=term_key)
                st.text_area("Edit definition", value=definition, key=definition_key)

        with col2:
            if not st.session_state[edit_mode_key]:
                # Display the Edit button
                if st.button("Edit", key=edit_button_key):
                    st.session_state[edit_mode_key] = True
            else:
                # Display Save and Cancel buttons when in edit mode
                if st.button("Save", key=f"save_button_{idx}"):
                    # Save changes to Google Sheets
                    row_index = terms.index(term) + 2  # Adjust for zero-index and header
                    updated_term = st.session_state[term_key]
                    updated_definition = st.session_state[definition_key]
                    observation_sheet.update(f'A{row_index}', updated_term)
                    observation_sheet.update(f'B{row_index}', updated_definition)
                    st.session_state[edit_mode_key] = False
                    st.success(f"Term '{updated_term}' has been updated.")

                if st.button("Cancel", key=f"cancel_button_{idx}"):
                    st.session_state[edit_mode_key] = False

    st.markdown("</div>", unsafe_allow_html=True)


# # Render the HTML content inside the scrollable container
# st.markdown(html_content, unsafe_allow_html=True)
# # Display the terms and their definitions with Edit buttons
# for idx, (term, definition) in enumerate(filtered_terms_definitions):
#     # Create columns for term/definition and the Edit button
#     col1, col2 = st.columns([8, 2])  # Adjust the column widths to fit your layout

#     with col1:
#         # Display term and definition
#         st.markdown(f"**{term}**: {definition}")

#     with col2:
#         if f"edit_button_{idx}" not in st.session_state:
#             st.session_state[f"edit_button_{idx}"] = False

#         # Display the Edit button in the second column with a unique key
#         if st.button("Edit", key=f"edit_button_trigger_{idx}"):
#             st.session_state[f"edit_button_{idx}"] = True

#         # If in edit mode, show the editable fields in the same place
#         if st.session_state[f"edit_button_{idx}"]:
#             with st.form(key=f"edit_form_{idx}"):
#                 edited_term = st.text_input("Edit term:", value=term, key=f"edit_term_{idx}")
#                 edited_definition = st.text_area("Edit definition:", value=definition, key=f"edit_definition_{idx}")
#                 save_button = st.form_submit_button("Save")
#                 cancel_button = st.form_submit_button("Cancel")

#                 if save_button:
#                     # Save changes to Google Sheets
#                     row_index = terms.index(term) + 1
#                     observation_sheet.update(f'A{row_index}', edited_term)
#                     observation_sheet.update(f'B{row_index}', edited_definition)
#                     st.session_state[f"edit_button_{idx}"] = False
#                     st.success(f"Term '{edited_term}' has been updated.")

#                 if cancel_button:
#                     st.session_state[f"edit_button_{idx}"] = False


# Render the HTML content inside the scrollable container
st.markdown(html_content, unsafe_allow_html=True)

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

########################## past retrieval of glossary: 

# # Retrieve values from specific columns in the Google Sheet
# column_values = observation_sheet.col_values(10)  # Terms are in column 10
# observation_ids = observation_sheet.col_values(1)  # Observation IDs are in column 1

# # Initialize dictionaries to store term counts and relevant observation IDs
# term_counts = {}
# relevant_observation_ids = {}

# # Process the column values and count occurrences of each term
# for i, value in enumerate(column_values[1:]):  # Skip the header row
#     if value:  # Ensure the string is not empty
#         terms = [term.strip() for term in value.split(",")]
#         for term in terms:
#             if term in term_counts:
#                 term_counts[term] += 1
#                 relevant_observation_ids[term].append(observation_ids[i+1])
#             else:
#                 term_counts[term] = 1
#                 relevant_observation_ids[term] = [observation_ids[i+1]]

# # Set up OpenAI API key for making requests
# openai.api_key = st.secrets["openai_key"]

# # Function to retrieve a medical term's definition using OpenAI
# def get_definition(term):
#     try:
#         messages = [
#             {"role": "system", "content": "You are a helpful assistant that provides concise definitions of medical terms."},
#             {"role": "user", "content": f"Define the following medical term: {term}"}
#         ]
#         response = openai.ChatCompletion.create(
#             model='gpt-4',
#             messages=messages,
#         )
#         return response.choices[0].message['content']
#     except Exception as e:
#         return f"Error: {e}"

# # Display the terms, their counts, and definitions
# st.write("Unique terms, their counts, and definitions:")

# # Sort terms alphabetically for display
# sorted_terms = sorted(term_counts.keys())

# for term in sorted_terms:
#     capitalized_term = term.capitalize()
#     definition = get_definition(term)
#     st.write(f"""
# - **{capitalized_term}** ({term_counts[term]}): {definition}  
# _Relevant observation IDs:_ {', '.join(relevant_observation_ids[term])}
#     """)

# st.markdown("---")

