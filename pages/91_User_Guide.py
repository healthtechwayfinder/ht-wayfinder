import streamlit as st
from streamlit_extras.switch_page_button import switch_page


from utils.login_utils import check_if_already_logged_in

check_if_already_logged_in()



def main():
    # Title & basic info
    st.markdown("<h1 style='text-align: left;'>Wayfinder User Guide:</h1>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    st.write("Follow this link for documentationa and examples for each of Wayfinder's features.")

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
    
    # Create a button to external user guide notion page
    st.link_button("Healthtech Wayfinder User Guide", "https://fixed-desert-9cd.notion.site/HealthTech-Wayfinder-User-Guide-1d770314f70c4dfbbb398f8a374e1dcb")


# run page    
main()

# if __name__ == "__main__":
#     st.set_page_config(initial_sidebar_state="collapsed")

#     if "login_status" not in st.session_state:
#         st.session_state["login_status"] = "not_logged_in"

#     if st.session_state["login_status"] == "success":
#         switch_page("Menu")
#     else:
#         main()
