import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import MemoryCacheHandler
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ModuleNotFoundError:
    pass  # on Streamlit Cloud, the keys come from Secrets instead

st.set_page_config(page_title="EchoMood")

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

# Step 3: Logged in
sp = spotipy.Spotify(auth=st.session_state["token_info"]["access_token"])

try:
    user_data = sp.current_user()
except spotipy.SpotifyException:
    # The login has expired (they last about an hour), so log in again
    del st.session_state["token_info"]
    st.rerun()

st.subheader(f"Welcome, {user_data['display_name']}")

if st.button("Log out"):
    del st.session_state["token_info"]
    st.rerun()


# Genres belong to artists, not songs, so we look them up one artist at a time.
# The cache stops us asking Spotify about the same artist twice.
@st.cache_data(ttl=3600, show_spinner=False)
def get_artist_genres(_sp, artist_id):
    try:
        return _sp.artist(artist_id).get("genres", [])
    except Exception:
        return []


def format_duration(ms):
    total_seconds = ms // 1000
    return f"{total_seconds // 60}:{total_seconds % 60:02d}"


time_ranges = {
    "Last 4 weeks": "short_term",
    "Last 6 months": "medium_term",
    "All time": "long_term",
}
choice = st.selectbox("Time period", list(time_ranges.keys()))
count = st.slider("How many songs", 10, 50, 20)

with st.spinner("Loading your songs..."):
    results = sp.current_user_top_tracks(limit=count, time_range=time_ranges[choice])
    tracks = results["items"]

    if not tracks:
        st.info("No listening data found for that period yet.")

    for track in tracks:
        col_img, col_info = st.columns([1, 5])

        with col_img:
            images = track["album"]["images"]
            if images:
                best = images[1] if len(images) > 1 else images[0]
                st.image(best["url"], width=90)

        with col_info:
            artist_names = ", ".join(a["name"] for a in track["artists"])

            genres = []
            for a in track["artists"]:
                for g in get_artist_genres(sp, a["id"]):
                    if g not in genres:
                        genres.append(g)
            genre_text = ", ".join(genres) if genres else "No genre listed by Spotify"

            st.markdown(f"**{track['name']}**")
            st.write(f"Artist(s): {artist_names}")
            st.write(f"Length: {format_duration(track['duration_ms'])}")
            st.write(f"Genre(s): {genre_text}")

        st.divider()