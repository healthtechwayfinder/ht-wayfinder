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

creds_dict = st.secrets["gwf_service_account"]
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.metadata.readonly"
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
glossary_sheet = client.open("Glossary").sheet1

def clear_row_by_term(term_to_search, glossary_sheet):
    """
    Searches the first column of a Google Sheet for a term and clears the contents of the corresponding row.

    Args:
    - term_to_search: The term to search for in the first column.
    - glossary_sheet: The gspread sheet object where the operation will take place.
    """
    # Get all values in the first column (Terms column)
    terms_list = glossary_sheet.col_values(1)  # Column 1 is typically the "Term" column
    
    try:
        # Find the row index of the term (0-based, so we add 1 for 1-based indexing)
        row_index = terms_list.index(term_to_search) + 1  # 1-based index for Google Sheets
        
        # Get the number of columns in the sheet to clear all cells in the row
        num_cols = glossary_sheet.col_count
        
        # Clear the contents of the row by replacing it with empty strings
        # glossary_sheet.update(f'A{row_index}:Z{row_index}', [[''] * num_cols])
        sheet1.delete_row(row_index)
        
        print(f"Cleared contents of row {row_index} for term '{term_to_search}'")
        
    except ValueError:
        print(f"Term '{term_to_search}' not found in the glossary.")


# if 'term_to_search' not in st.session_state:
#     st.session_state['term_to_search'] = ""

term_to_search = st.text_input("Enter your input:")
if st.button('Say hello'):
    clear_row_by_term(term_to_search, glossary_sheet)
    st.write('Deleted')

