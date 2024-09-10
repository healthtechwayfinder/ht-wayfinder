import streamlit as st
from streamlit_extras.switch_page_button import switch_page

from pydantic import BaseModel, Field
from typing import Optional
import csv
import os



#import streamlit as st

# Apply custom CSS to use Helvetica font
# st.markdown(
#     """
#     <style>
#     @import url('https://fonts.googleapis.com/css2?family=Helvetica:wght@400;700&display=swap');
#     html, body, [class*="css"]  {
#         font-family: 'Helvetica', sans-serif;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )


st.set_page_config(page_title="HealthTech Wayfinder", page_icon="📍")

st.markdown("# Welcome!")



col1, col2 = st.columns(2)

with col1:
    st.header("Observation Tools")
    if st.button("🔍 Record a New Observation"):
        switch_page("Record_New_Observation")

    if st.button("❓ Chat with Observations"):
        switch_page("Ask_the_Observations")

    if st.button("📒 View All Observations"):
        switch_page("View_All_Observations")
        
    if st.button("📊 Glossary"):
        switch_page("Glossary")

    if st.button("✅ Weekly Review (coming soon)"):
        switch_page("Tips_for_Observations")
    #st.image("https://static.streamlit.io/examples/cat.jpg")

with col2:
    st.header("Need Statement Tools")
    if st.button("🔍 Create a Need Statement"):
        switch_page("Need_Statement_Logger")

    if st.button("✅ Scope Need Statements (coming soon)"):
        switch_page("Tips_for_Observations")

    #st.image("https://static.streamlit.io/examples/dog.jpg")


# Your logo URL (replace if necessary)
# logo_url = "https://raw.githubusercontent.com/Aks-Dmv/bio-design-hms/main/Logo-HealthTech.png"

# Display the title with the logo below it
# st.markdown(
#     f"""
#     <div style="text-align: center;">
#         <h1>Dashboard</h1>
#         <img src="{logo_url}" alt="Logo" style="width:350px; height:auto;">
#     </div>
#     """,
#     unsafe_allow_html=True,
# )

st.markdown("---")

# st.markdown("<h3 style='text-align: center;'>What would you like to do?</h3>", unsafe_allow_html=True)

# Button functionality
# col1, col2 = st.columns([1, 3])
# with col2:
#     if st.button("🔍 Record a New Observation"):
#         switch_page("Record_New_Observation")

#     if st.button("✅ Tips for your Observations"):
#         switch_page("Tips_for_Observations")

#     if st.button("❓ Chat with Observations"):
#         switch_page("Ask_the_Observations")

#     if st.button("📊 Glossary"):
#         switch_page("Glossary")

#     if st.button("📒 View All Observations"):
#         switch_page("View_All_Observations")

# st.markdown("---")

# Log Out Button with rerun or meta refresh
col1, col2, col3 = st.columns([3, 1, 1])
with col3:
    if st.button("Log Out"):
        # Option 1: Use experimental rerun
        st.experimental_rerun()

        # Option 2: Use meta refresh (only if necessary)
        # st.markdown('<meta http-equiv="refresh" content="0; url=/streamlit_app" />', unsafe_allow_html=True)


######


# # Apply custom CSS to use Helvetica font
# st.markdown(
#     """
#     <style>
#     @import url('https://fonts.googleapis.com/css2?family=Helvetica:wght@400;700&display=swap');

#     html, body, [class*="css"]  {
#         font-family: 'Helvetica', sans-serif;
#     }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )




# # # Your logo URL
# # logo_url = "https://raw.githubusercontent.com/Aks-Dmv/bio-design-hms/main/Logo-HealthTech.png"  # Replace with the actual URL of your logo

# # Display the title with the logo below it
# # st.markdown(
# #     f"""
# #     <div style="text-align: center;">
# #         <h1>THIS IS A TEST 👺</h1>
# #          <img src="{logo_url}" alt="Logo" style="width:350px; height:auto;">
# #     </div>
# #     """,
# #     unsafe_allow_html=True,
# # )


# # st.markdown("---")

# # Apply custom CSS to use Helvetica font
# # st.markdown(
# #     """
# #     <style>
# #     @import url('https://fonts.googleapis.com/css2?family=Helvetica:wght@400;700&display=swap');

# #     html, body, [class*="css"]  {
# #         font-family: 'Helvetica', sans-serif;
# #     }
# #     </style>
# #     """,
# #     unsafe_allow_html=True,
# # )

# # Your logo URL
# logo_url = "https://raw.githubusercontent.com/Aks-Dmv/bio-design-hms/main/Logo-HealthTech.png"  # Replace with a different URL if necessary

# # Display the title with the logo below it
# st.markdown(
#         f"""
#         <div style="text-align: center;">
#             <h1>Dashboard</h1>
#              <img src="{logo_url}" alt="Logo" style="width:350px; height:auto;">
#         </div>
#         """,
#         unsafe_allow_html=True,
# )
    
# # st.markdown("---")

# st.markdown("<h3 style='text-align: center;'>What would you like to do?</h3>", unsafe_allow_html=True)



# # # def main():
# # st.markdown("<h1 style='text-align: center;'>HealthTech Wayfinder</h1>", unsafe_allow_html=True)
# # st.markdown("<h3 style='text-align: center;'>What would you like to do?</h3>", unsafe_allow_html=True)


# # ######

# col1, col2 = st.columns([1, 3])
# with col2:
#     if st.button("🔍 Record a New Observation"):
#         switch_page("Record_New_Observation")

#     if st.button("✅ Tips for your Observations"):
#         switch_page("Tips_for_Observations")

#     if st.button("❓ Chat with Observations"):
#         switch_page("Ask_the_Observations")

#     if st.button("📊 Glossary"):
#         switch_page("Glossary")

#     if st.button("📒 View All Observations"):
#         switch_page("View_All_Observations")

# st.markdown("---")
    
# # Create columns to position the Log Out button on the right
# col1, col2, col3 = st.columns([3, 1, 1])
# with col3:
#     if st.button("Log Out"):
#         # switch_page("/")

#     # Adjust the URL to the correct path of your main script
#         st.markdown('<meta http-equiv="refresh" content="0; url=/streamlit_app" />', unsafe_allow_html=True)


# #    if st.button("Go to Main"):
# #        st.markdown('<meta http-equiv="refresh" content="0; url=./" />', unsafe_allow_html=True)
