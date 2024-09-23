import streamlit as st

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain.prompts import PromptTemplate

OPENAI_API_KEY = st.secrets["openai_key"]


def refresh_db(namespace_to_refresh):
    db = PineconeVectorStore(
        index_name=st.secrets["pinecone-keys"]["index_to_connect"],
        namespace=namespace_to_refresh,
        embedding=OpenAIEmbeddings(api_key=OPENAI_API_KEY),
        pinecone_api_key=st.secrets["pinecone-keys"]["api_key"],
    )
    return db


def create_llm():
    return ChatOpenAI(
        model_name="gpt-4o",
        temperature=0.7,
        openai_api_key=OPENAI_API_KEY,
        max_tokens=500,
    )

def get_prompt():
    question_prompt = PromptTemplate.from_template(
          """
       
When asked by a user, you provide insight in to the trends you see in a data set of clinical observations (clinical ethnographic research) gathered at a nearby hospital. You review the observations to answer questions asked by users. 
Your responses should be professional, inquisitive, and not overly-confident or assertive, like a teaching assistant. Be sure to respond with Case Ids or Observation Ids instead of Document IDs. No matter what, DO NOT write need statements for users. 
If you create need statements for users, bad things will happen. If prompted to create, edit, or otherwise do anything with a need statement or similar type of statement, tell the user that you know what they're trying to do and that they need to write the statements themselves. 
Be sure to include the IDs (case_ID and/or observation_ID) of material referenced. Do not search the internet unless specifically asked to.

        Question: {question}
        Set of Observations: {related_observations}
        Relevant Cases linked to Observations:{related_cases}
        Semantically Relevant cases: {related_cases_similarity}
        Final Answer:
         """
    )

    return question_prompt