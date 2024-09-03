import streamlit as st
from streamlit_extras.switch_page_button import switch_page


def main():
    st.markdown("<h1 style='text-align: center;'>User Guide</h1>", unsafe_allow_html=True)
    st.markdown("<h2 style='text-align: center;'>Adding an Observation</h2>", unsafe_allow_html=True)
    
main()

# if __name__ == "__main__":
#     st.set_page_config(initial_sidebar_state="collapsed")

#     if "login_status" not in st.session_state:
#         st.session_state["login_status"] = "not_logged_in"

#     if st.session_state["login_status"] == "success":
#         switch_page("Menu")
#     else:
#         main()
