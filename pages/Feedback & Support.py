import streamlit as st

def feedback_support_page():
    st.title("Feedback & Support")

    st.write("""
    We value your feedback and are here to help! You can use the forms below to report any issues or send us questions and feedback.
    """)

    st.subheader("Report an Issue")
    st.write("If you're experiencing a problem, please let us know using the form below:")

    # Embed the Google Form for reporting an issue (Replace with your form URL)
    report_issue_form_url = "https://docs.google.com/forms/d/e/1FAIpQLScQTy8j_HBSIM1Ukh6jdIfxCW2K1XJXr4ChVSqxJxtyLoP2hA/viewform?embedded=true"
    st.markdown(f'<iframe src="{report_issue_form_url}" width="100%" height="800px" frameborder="0" marginheight="0" marginwidth="0">Loading…</iframe>', unsafe_allow_html=True)

    st.subheader("Send Feedback or Ask a Question")
    st.write("Have feedback or questions? Please use the form below to reach out to us:")

    # Embed the Google Form for feedback or questions (Replace with your form URL)
    feedback_form_url = "https://docs.google.com/forms/d/e/your-google-form-id/viewform?embedded=true"
    st.markdown(f'<iframe src="{feedback_form_url}" width="100%" height="800px" frameborder="0" marginheight="0" marginwidth="0">Loading…</iframe>', unsafe_allow_html=True)

# Run the feedback & support page
if __name__ == '__main__':
    feedback_support_page()





#________________________OLD TIPS FOR OBSERVATIONS_______________________

# import streamlit as st
# from streamlit_extras.switch_page_button import switch_page

# st.set_page_config(page_title="Tips for Observations", page_icon="✅")
# import streamlit as st
# from streamlit_extras.switch_page_button import switch_page
# import pandas as pd


# from langchain_openai import ChatOpenAI
# from langchain.chains import LLMChain
# from langchain.output_parsers import PydanticOutputParser
# from langchain.callbacks import get_openai_callback
# from langchain.schema import StrOutputParser
# from langchain.schema.runnable import RunnableLambda
# from langchain.prompts import PromptTemplate
# from langchain_community.embeddings import OpenAIEmbeddings


# from pydantic import BaseModel, Field
# from typing import Optional
# from datetime import date

# import json
# # If using st.secrets
# creds_dict = st.secrets["gcp_service_account"]
# #calling google sheets
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials

# # Set up the connection to Google Sheets
# creds_dict = st.secrets["gcp_service_account"]
# scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.metadata.readonly"]
# creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
# client = gspread.authorize(creds)
# sheet = client.open("BioDesign Observation Record").sheet1

# # Load data from Google Sheets and convert to DataFrame
# try:
#     values = sheet.get_all_values()
#     if not values:
#         st.error("The Google Sheet appears to be empty.")
#     else:
#         headers = values.pop(0)  # Remove the first row as headers
#         df = pd.DataFrame(values, columns=headers)
        
#         # Select Observation ID and Observation columns
#         observation_id_col = "observation_id"  # Update this to the correct name
#         observation_text_col = "observation"  # Update this to the correct name
        
#         # Create a dropdown menu for selecting Observation ID
#         observation_id = st.selectbox("Select an Observation ID", df[observation_id_col])
        
#         # Retrieve the corresponding observation text based on the selected Observation ID
#         selected_observation = df[df[observation_id_col] == observation_id][observation_text_col].values[0]
        
#         # Display the selected observation
#         st.write("Selected Observation:")
#         st.write(selected_observation)

#         # Function to get tips from the observation
#         def get_tips_from_observation(observation):
#             llm = ChatOpenAI(
#                 model_name="gpt-4o",
#                 temperature=0.7,
#                 openai_api_key=st.secrets["openai_key"],
#                 max_tokens=500,
#             )

#             questions_list = """
#             Problem definition:
#             What was the stated or principle cause of the problem you observed?
#             What other things could have caused or contributed to this problem?
#             What could have been done to avoid the problem?
#             What other problems exist because this problem exists?
#             Stakeholder definition:
#             Specific description of who specifically had this problem (Man, Woman, Child, Age, Socio-economic background, etc.)
#             Are there any other populations that would have this problem? (all OR patients, all patients over 65, all patients with CF, etc.)
#             Are there any populations that experience the same problem with more severity than what was observed?
#             Are there any populations that experience the same problem with less severity than what was observed?
#             Outcome definition:
#             What is the desired outcome with current treatments?
#             What is the ideal outcome desired to lessen the problem to a manageable amount?
#             What is the desired outcome to eliminate the problem?
#             What is the outcome if you prevented the problem?
#             """

#             observation_prompt = PromptTemplate.from_template(
#             """
#             You help me by giving me the most relevant two questions from the list that have not been answered in the following observation.
#             The observation is about a medical procedure and the questions are about the problem, stakeholders, and outcomes.
#             The answers should not be present but the chosen two questions must be very relevant to the observation.
#             Be concise in your output, and give a maximum of the two questions!

#             List of questions: {questions_list}

#             Observation: {observation}
#             Output:"""
#             )

#             observation_chain = LLMChain(
#                 prompt=observation_prompt,
#                 llm=llm,
#                 output_parser=StrOutputParser()
#             )

#             with get_openai_callback() as cb:
#                 output = observation_chain.run({"observation": observation, "questions_list": questions_list})

#             return output

#         # Button to get tips for the selected observation
#         if st.button("Get Tips for this Observation"):
#             tips = get_tips_from_observation(selected_observation)
#             st.markdown(tips)

# except KeyError as e:
#     st.error(f"Column not found: {e}")
# except Exception as e:
#     st.error(f"An error occurred: {e}")

# st.markdown("---")

# # Apply custom CSS to make the button blue
# st.markdown("""
#     <style>
#     div.stButton > button {
#         background-color: #365980;
#         color: white;
#         font-size: 16px;
#         padding: 10px 20px;
#         border: none;
#         border-radius: 5px;
#     }
#     div.stButton > button:hover {
#         background-color: #2c4a70;
#         color: white;
#     }
#     </style>
#     """, unsafe_allow_html=True)



# # Create a button using Streamlit's native functionality
# if st.button("Back to Main Menu"):
#     switch_page("main_menu")
