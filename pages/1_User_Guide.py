import streamlit as st
from streamlit_extras.switch_page_button import switch_page


def main():
    st.markdown("<h1 style='text-align: center;'>User Guide: Observations</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Add an Observation</h3>", unsafe_allow_html=True)
    # add in a description of this feature
    
    st.markdown("<h3 style='text-align: center;'>Chat with Observations</h3>", unsafe_allow_html=True)
    # add in a description of this feature

    st.markdown("<h3 style='text-align: center;'>View Observations</h3>", unsafe_allow_html=True)
    # add in a description of this feature
    
    st.markdown("<h3 style='text-align: center;'>Glossary</h3>", unsafe_allow_html=True)
    # add in a description of this feature

    st.markdown("<h1 style='text-align: center;'>User Guide: Need Statements</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center;'>Create a Need Statement</h3>", unsafe_allow_html=True)
    # add in a description of this feature

    st.markdown("<h3 style='text-align: center;'>Scope a Need Statement</h3>", unsafe_allow_html=True)
    # add in a description of this feature

    st.markdown("<h3 style='text-align: center;'>Create Need Statement Variants</h3>", unsafe_allow_html=True)
    # add in a description of this feature



    
main()

# if __name__ == "__main__":
#     st.set_page_config(initial_sidebar_state="collapsed")

#     if "login_status" not in st.session_state:
#         st.session_state["login_status"] = "not_logged_in"

#     if st.session_state["login_status"] == "success":
#         switch_page("Menu")
#     else:
#         main()
