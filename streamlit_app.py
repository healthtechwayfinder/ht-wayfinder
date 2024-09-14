import streamlit as st
from streamlit_extras.switch_page_button import switch_page
import streamlit_cookies_manager
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests

# Initialize cookies manager
cookies = streamlit_cookies_manager.CookieManager()

# OAuth setup: Using Streamlit secrets instead of client_secret.json
def get_google_oauth_flow():
    client_config = {
        "web": {
            "client_id": st.secrets["google_oauth"]["client_id"],
            "project_id": st.secrets["google_oauth"]["project_id"],
            "auth_uri": st.secrets["google_oauth"]["auth_uri"],
            "token_uri": st.secrets["google_oauth"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["google_oauth"]["auth_provider_x509_cert_url"],
            "client_secret": st.secrets["google_oauth"]["client_secret"],
            "redirect_uris": st.secrets["google_oauth"]["redirect_uris"]
        }
    }

    # Initialize the flow with redirect URI from secrets
    flow = Flow.from_client_config(
        client_config,
        scopes=["https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"]
    )
    flow.redirect_uri = st.secrets["google_oauth"]["redirect_uris"][0]
    return flow

# Get Google Authorization URL
def initiate_google_flow():
    flow = get_google_oauth_flow()
    auth_url, state = flow.authorization_url(prompt='consent')
    st.session_state['oauth_state'] = state  # Save state for verification later
    return auth_url

# Exchange the authorization code for credentials and verify email
def exchange_code_for_credentials(flow, code):
    flow.fetch_token(code=code)
    credentials = flow.credentials

    # Verify the token and get user info (email)
    try:
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, requests.Request(), st.secrets["google_oauth"]["client_id"]
        )
    except ValueError:
        st.error("Invalid Google OAuth token. Please try again.")
        return None

    # Extract email from the id_info
    user_email = id_info.get('email', None)
    if not user_email:
        st.error("Could not retrieve email from Google account.")
        return None

    return user_email

# Check if the user selected "Stay logged in" and is already logged in via cookies
def check_stay_logged_in():
    if "login_status" not in st.session_state:
        st.session_state["login_status"] = "not_logged_in"

    # Since cookies are automatically loaded when the CookieManager is initialized,
    # you can directly check for the 'logged_in' cookie
    if cookies.get("logged_in") == "true":
        st.session_state["login_status"] = "success"

# Function to handle Google login and email verification
def handle_google_login():
    query_params = st.experimental_get_query_params()
    if 'code' in query_params and 'oauth_state' in st.session_state:
        flow = get_google_oauth_flow()

        # Verify state matches
        if query_params.get('state', [''])[0] == st.session_state['oauth_state']:
            user_email = exchange_code_for_credentials(flow, query_params['code'][0])

            if user_email:
                # Load allowed emails from st.secrets
                allowed_emails = st.secrets["allowed_emails"]["emails"]

                # Compare user_email to allowed_emails list
                if user_email in allowed_emails:
                    st.session_state["login_status"] = "success"
                    st.session_state["google_user"] = user_email  # Store the email for later use
                    st.success(f"Google login successful for {user_email}!")
                    return True  # Indicate successful login
                else:
                    # Do not redirect unauthorized users, show error instead
                    st.error("Unauthorized email. Access denied.")
                    return False  # Indicate unauthorized login

    return False

# Main login function
def main():
    st.markdown("<h2 style='text-align: center;'>Welcome back! </h2>", unsafe_allow_html=True)

    logo_url = "https://raw.githubusercontent.com/Aks-Dmv/bio-design-hms/main/Logo-HealthTech.png"
    st.markdown(
        f"""
        <div style="text-align: center;">
            <h1>HealthTech Wayfinder</h1>
            <img src="{logo_url}" alt="Logo" style="width:350px; height:auto;">
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Google Login
    st.write("Or use Google to log in:")
    if st.button("Login with Google"):
        auth_url = initiate_google_flow()
        st.markdown(f"<a href='{auth_url}' target='_blank'>Click here to log in with Google</a>", unsafe_allow_html=True)

    # Handle Google login and only proceed if authorized
    if handle_google_login():
        # Redirect only after a successful login
        switch_page("Dashboard")

# Main app logic
if __name__ == "__main__":
    # Check if the user chose to stay logged in
    check_stay_logged_in()

    # Ensure user is logged in before allowing access to the Dashboard
    if st.session_state.get("login_status") == "success":
        # User is logged in, show sidebar and redirect to the Dashboard
        st.sidebar.write("You are logged in!")
        switch_page("Dashboard")
    else:
        # Show the login form
        main()

