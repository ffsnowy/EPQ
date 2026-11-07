import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import MemoryCacheHandler
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(page_title="EchoMood")

# Configure Spotify API
def get_setting(name):
    value = os.getenv(name)
    if not value:
        try:
            value = st.secrets[name]
        except Exception:
            value = None
    return value

client_id = get_setting('CLIENT_ID')
client_secret = get_setting('CLIENT_SECRET')
redirect_uri = get_setting('REDIRECT_URI')

if not (client_id and client_secret and redirect_uri):
    st.error("Missing Spotify settings. Add CLIENT_ID, CLIENT_SECRET and REDIRECT_URI under Manage app > Settings > Secrets.")
    st.stop()

sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope="user-top-read user-library-read playlist-modify-public",
    cache_handler=MemoryCacheHandler()
)

st.title("EchoMood")

# Step 1: Spotify sends the user back here with ?code=... in the URL
if "token_info" not in st.session_state and "code" in st.query_params:
    code = st.query_params["code"]
    try:
        st.session_state["token_info"] = sp_oauth.get_access_token(code, check_cache=False)
    except Exception as e:
        st.error(f"Login failed: {e}")
    st.query_params.clear()
    st.rerun()

# Step 2: Not logged in, so show the login button
if "token_info" not in st.session_state:
    st.link_button("Log in with Spotify", sp_oauth.get_authorize_url())
    st.stop()

# Step 3: Logged in, so show the dashboard
sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])
user_data = sp.current_user()
st.subheader(f"Welcome, {user_data['display_name']}")
st.json(user_data)

if st.button("Log out"):
    del st.session_state["token_info"]
    st.rerun()