import streamlit as st

from langchain.schema import StrOutputParser
from langchain.prompts import PromptTemplate

from utils.login_utils import check_if_already_logged_in
from utils.google_sheet_utils import create_new_chat_sheet, get_case_descriptions_from_case_ids
from utils.llm_utils import create_llm
from utils.page_formatting import add_investigator_formatting
from utils.initialize_session import initialize_investigator_session
from utils.chatbot_utils import fetch_similar_data

check_if_already_logged_in()
add_investigator_formatting()
initialize_investigator_session()


# Handle new input
if prompt := st.chat_input("What would you like to ask?"):
    fetched_data_dict = fetch_similar_data(prompt)
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

    llm = create_llm()
    
    observation_chat_chain = (question_prompt | llm | StrOutputParser())

    invoke_chain_and_update_session(observation_chat_chain, fetched_data_dict)

st.markdown("---")

# Spacer to push the button to the bottom
st.write(" " * 50)
