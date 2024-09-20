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

OPENAI_API_KEY = st.secrets["openai_key"]


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
creds_dict = st.secrets["gwf_service_account"]
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
if "new_variant" not in st.session_state:
    st.session_state["new_variant"] = ""


# Print test 
terms = observation_sheet.col_values(1)  # Terms are in column 1
definitions = observation_sheet.col_values(2)  # Definitions are in column 2
variants = observation_sheet.col_values(3)  # Variants are in column 3
related_cases = observation_sheet.col_values(4)  # Related Cases are in column 4

# Combine terms and definitions into a list of tuples
# terms_definitions = list(zip(terms[1:], definitions[1:]))  # Skip header row
glossary_db = []
term_and_variants = []
for idx in range(1, len(terms)):

    item = {
        'term': terms[idx],
        'definition': definitions[idx],
        'related_cases': related_cases[idx] if idx < len(related_cases) else ''
    }
    term_and_variant = terms[idx]

    if idx < len(variants):
        item['variant'] = variants[idx]
        term_and_variant += ' (' + variants[idx] + ')'
    else:
        term_and_variant += ' ()'

    # Add the related cases field
    if idx < len(related_cases):
        item['related_cases'] = related_cases[idx]

    glossary_db.append(item)
    terms.append(terms[idx])
    term_and_variants.append(term_and_variant)

# Sort the list alphabetically by the term
# Sort the list alphabetically by the term, then by variant (if any)
sorted_glossary_db = sorted(glossary_db, key=lambda x: (x['term'].lower(), x.get('variant', '').lower()))

def generateVariantName(term, definition, existing_definitions=[], existing_variants=[]):
    llm = ChatOpenAI(
        model_name="gpt-4o",
        temperature=0.7,
        openai_api_key=OPENAI_API_KEY,
        max_tokens=500,
    )


    variantNamePrompt = PromptTemplate.from_template(
"""
You help giving a one word unique variant name for a term and its target definition. This is because a term can have multiple definitions and it is useful to have a variant name to distinguish between them.
Give only one word as the variant name for target term.

term: {term}
target definition for this term: {definition}
other definitions for the same term: {existing_definitions}
other variants for the same term: {existing_variants}
Output Variant Name for target definition:
"""
)
    variant_chain = (
        variantNamePrompt | llm | StrOutputParser()
    )

    # with get_openai_callback() as cb:
    output = variant_chain.invoke({"term": term, "definition": definition, 
                                   "existing_definitions": existing_definitions, "existing_variants": existing_variants})

    return output

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
        new_variant = st.session_state["new_variant"].strip()
        new_definition = st.session_state["new_definition"].strip()

        if len(new_variant) > 0:
            new_term_and_variant = new_term + ' (' + new_variant + ')'
        else:
            new_term_and_variant = new_term + ' ()'

        print("New term and variant: ", new_term_and_variant)

        if new_term_and_variant and new_definition:
            # Check for duplicate term
            if new_term in terms:
                print("Duplicate term found for ", new_term)

                # get all variants and definitions for the term
                existing_variants = []
                existing_definitions = []

                for item in glossary_db:
                    if item['term'] == new_term:
                        existing_variant = item.get('variant', '')
                        existing_def = item['definition']

                        if existing_variant == '':
                            old_variant = generateVariantName(new_term, existing_def, existing_definitions = [new_definition])
                            print("Generated variant name for old definition: ", old_variant)
                            if old_variant:
                                update_idx = term_and_variants.index(new_term_and_variant)+2
                                observation_sheet.update(values=[[old_variant]], range_name=f'C{update_idx}')
                                existing_variant = old_variant

                        existing_variants.append(existing_variant)
                        existing_definitions.append(existing_def)

                new_variant_input = generateVariantName(new_term, new_definition, 
                                                        existing_definitions=existing_definitions, 
                                                        existing_variants=existing_variants)
                print("Generated variant name: ", new_variant_input)
                st.warning(f"Term '{new_term}' already exists with definition: {existing_def}. Creating new variant {new_variant_input} for this definition.")

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
# filtered_terms = [item for item in sorted_glossary_terms if search_term.lower() in item.lower()]
filtered_items = [item for item in sorted_glossary_db if search_term.lower() in item['term'].lower()]

def onEditClickFunction(edit_mode_key):
    print(f"Edit button clicked for term {edit_mode_key}" )
    st.session_state[edit_mode_key] = True

def onCancelClickFunction(edit_mode_key):
    print(f"Cancel button clicked for term {edit_mode_key}" )
    st.session_state[edit_mode_key] = False

# Display the terms and their definitions inside the scrollable container
for idx, item in enumerate(filtered_items):
    term = item['term']
    definition = item['definition']
    variant = item.get('variant', None)
    related_cases = item.get('related_cases', '')

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
            # Display related cases if available
            if related_cases:
                st.markdown(f"_Related Cases:_ {related_cases}")
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
                term_variant = term + ' (' + variant + ')' if variant else term
                row_index = term_and_variants.index(term_variant)+2
                print("Updating for term with index: ", row_index)
                
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
