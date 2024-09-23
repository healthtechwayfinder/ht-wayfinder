import streamlit as st
from utils.llm_utils import refresh_db
from utils.google_sheet_utils import get_case_descriptions_from_case_ids

def fetch_similar_data(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Perform similarity search using Pinecone
    updated_observations_db = refresh_db(namespace_to_refresh="observations")
    related_observations = updated_observations_db.similarity_search(prompt, k=10)

    # get case ids from metadata of related observations
    case_ids = []
    for observation in related_observations:
        if 'case_id' in observation.metadata:
            case_ids.append(observation.metadata['case_id'])

    related_cases = get_case_descriptions_from_case_ids(case_ids)

    updated_cases_db = refresh_db(namespace_to_refresh="cases")
    related_cases_similarity = updated_cases_db.similarity_search(prompt, k=4)

    return {"question": prompt, 
            "related_observations": related_observations,
            "related_cases": related_cases,
            "related_cases_similarity": related_cases_similarity}