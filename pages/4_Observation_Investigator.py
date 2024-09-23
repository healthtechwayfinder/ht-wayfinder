import streamlit as st

from langchain.callbacks import get_openai_callback
from langchain.schema import StrOutputParser
from langchain.prompts import PromptTemplate

from utils.login_utils import check_if_already_logged_in
from utils.google_sheet_utils import create_new_chat_sheet, get_case_descriptions_from_case_ids
from utils.llm_utils import refresh_db, create_llm
from utils.page_formatting import add_investigator_formatting
from utils.initialize_session import initialize_investigator_session

check_if_already_logged_in()
add_investigator_formatting()
initialize_investigator_session()



# Handle new input
if prompt := st.chat_input("What would you like to ask?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Perform similarity search using Pinecone
    updated_observations_db = refresh_db(namespace_to_refresh="observations")
    related_observations = updated_observations_db.similarity_search(prompt, k=10)
    # related_observations = st.session_state['observation_google_sheet'] # Placeholder for now
    print(related_observations)

    # get case ids from metadata of related observations
    case_ids = []
    for observation in related_observations:
        if 'case_id' in observation.metadata:
            case_ids.append(observation.metadata['case_id'])

    print("Fetching case descriptions for case ids: ", case_ids)
    related_cases = get_case_descriptions_from_case_ids(case_ids)
    print(related_cases)

    updated_cases_db = refresh_db(namespace_to_refresh="cases")
    related_cases_similarity = updated_cases_db.similarity_search(prompt, k=4)

       
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
    
    observation_chat_chain = (
        question_prompt | llm | StrOutputParser()
    )

    with get_openai_callback() as cb:
        output = observation_chat_chain.invoke({"question": prompt, 
                                                "related_observations": related_observations,
                                                "related_cases": related_cases,
                                                "related_cases_similarity": related_cases_similarity},)

    # Update the conversation history
    st.session_state.messages.append({"role": "assistant", "content": output})

    # Display the response
    with st.chat_message("assistant"):
        st.markdown(output)
        # st.markdown("---")
        # st.markdown("### Related Observations")
        # for i, observation in enumerate(related_observations):
        #     st.write(f"{i+1}. {observation}")

    # Store chat in the current sheet
    st.session_state.chat_sheet.append_row([st.session_state.messages[-2]['content'], st.session_state.messages[-1]['content']])


st.markdown("---")

# Spacer to push the button to the bottom
st.write(" " * 50)
