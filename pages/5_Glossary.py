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
import time

# Set up the Streamlit page
st.set_page_config(page_title="Glossary", page_icon="📊")
st.markdown("# Glossary")

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
variants = observation_sheet.col_values(3)  # Variants are in column 3

# Combine terms and definitions into a list of tuples
# terms_definitions = list(zip(terms[1:], definitions[1:]))  # Skip header row
glossary_db = {}

for idx in range(1, len(terms)):

    glossary_db[terms[idx]] = {
        'definition': definitions[idx],
    }

    if idx < len(variants):
        glossary_db[terms[idx]]['variant'] = variants[idx]

# Sort the list alphabetically by the term
sorted_glossary_terms = sorted(glossary_db.keys())


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

# # Search bar for filtering terms
# search_term = st.text_input("Search Glossary")


# Button to toggle input fields for a new term
if st.button("Add a New Term"):
    st.session_state["show_new_term_fields"] = not st.session_state["show_new_term_fields"]

# Conditionally display the input fields for adding a new term and definition
if st.session_state["show_new_term_fields"]:
    new_term_input = st.text_input("Enter a new term:", value=st.session_state["new_term"])
    new_variant_input = st.text_input("Enter a variant (if applicable):", value=st.session_state.get("new_variant", ""))
    new_definition_input = st.text_area("Enter the definition for the new term:", value=st.session_state["new_definition"])

    # Update the session state values based on user input
    st.session_state["new_term"] = new_term_input
    st.session_state["new_variant"] = new_variant_input
    st.session_state["new_definition"] = new_definition_input

    # Submit New Term button
    if st.button("Submit New Term"):
        new_term = st.session_state["new_term"].strip()
        new_definition = st.session_state["new_definition"].strip()

        if new_term and new_definition:
            # Check for duplicate term
            if new_term.lower() in [t.lower() for t in terms]:
                idx = next(i for i, t in enumerate(terms) if t.lower() == new_term.lower())
                existing_def = definitions[idx]

                if st.checkbox(f"Add a new definition to the existing term '{new_term}'?"):
                    # Append new definition to the existing one
                    updated_definition = existing_def + "\n" + new_definition
                    observation_sheet.update(f'B{idx+1}', updated_definition)  # Update Google Sheets
                    st.success(f"New definition added to '{new_term}'")
                else:
                    st.warning(f"Term '{new_term}' already exists with definition: {existing_def}")
            else:
                # Add new term and definition
                new_term = new_term.capitalize()
                new_definition = new_definition.capitalize()
                new_variant = new_variant_input.capitalize() if new_variant_input else None
                observation_sheet.append_row([new_term, new_definition, new_variant])
                st.success(f"Term '{new_term}' has been added successfully!")

            # Clear the session state for inputs
            st.session_state["new_term"] = ""
            st.session_state["new_definition"] = ""
            st.session_state["show_new_term_fields"] = False
            st.rerun()
        else:
            st.error("Please enter both a term and a definition.")


# Search bar for filtering terms
search_term = st.text_input("Search Glossary", key="search_term")

# Filter the glossary based on the search term (case-insensitive)
filtered_terms = [item for item in sorted_glossary_terms if search_term.lower() in item.lower()]


def onEditClickFunction(edit_mode_key):
    print(f"Edit button clicked for term {edit_mode_key}" )
    st.session_state[edit_mode_key] = True

def onCancelClickFunction(edit_mode_key):
    print(f"Cancel button clicked for term {edit_mode_key}" )
    st.session_state[edit_mode_key] = False

# Display the terms and their definitions inside the scrollable container
for idx, term in enumerate(filtered_terms):
    definition = glossary_db[term]['definition']
    variant = glossary_db[term].get('variant', None)

    term_key = f"term_{idx}"
    definition_key = f"definition_{idx}"
    edit_mode_key = f"edit_mode_{idx}"
    variant_key = f"variant_{idx}"

    # Initialize edit mode in session state
    if edit_mode_key not in st.session_state:
        st.session_state[edit_mode_key] = False

    col1, col2 = st.columns([8, 2])

    with col1:
        if not st.session_state[edit_mode_key]:
            # Display term and definition in normal mode
            if variant:
                st.markdown(f"**{term}** ({variant}): {definition}")
            else:
                st.markdown(f"**{term}**: {definition}")
        else:
            # Display editable fields in edit mode
            st.text_input("Edit term", value=term, key=term_key)

            if variant:
                st.text_input("Edit variant", value=variant, key=variant_key)
            else:
                st.session_state[variant_key] = None

            st.text_area("Edit definition", value=definition, key=definition_key)


    with col2:
        if not st.session_state[edit_mode_key]:
            if st.button("Edit", key=f"edit_button_{idx}", on_click=onEditClickFunction, args=(edit_mode_key,)):
                # st.session_state[edit_mode_key] = True
                print(f"Edit button clicked for term {edit_mode_key}" )
                pass
        else:
            if st.button("Save", key=f"save_button_{idx}"):
                # Save changes to Google Sheets
                row_index = terms.index(term) + 1 
                updated_term = st.session_state[term_key]
                updated_definition = st.session_state[definition_key]
                updated_variant = st.session_state[variant_key]
                print("Updating for term with index: ", row_index)
                observation_sheet.update(values=[[updated_term]], range_name=f'A{row_index}')
                observation_sheet.update(values=[[updated_definition]], range_name=f'B{row_index}')
                if updated_variant:
                    observation_sheet.update(values=[[updated_variant]], range_name=f'C{row_index}') 
                st.success(f"Term '{updated_term}' has been updated.")
                time.sleep(3)
                st.session_state[edit_mode_key] = False
                st.rerun()
            if st.button("Cancel", key=f"cancel_button_{idx}", on_click=onCancelClickFunction, args=(edit_mode_key,)):
                # st.session_state[edit_mode_key] = False
                pass

    # add a break line
    st.markdown("<br>", unsafe_allow_html=True)

if st.button("Back to Main Menu"):
    switch_page("main_menu")

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

