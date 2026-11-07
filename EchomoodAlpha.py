from flask import Flask, request, redirect, session, jsonify
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configure Spotify API
sp_oauth = SpotifyOAuth(
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    redirect_uri=os.getenv('REDIRECT_URI'),
    scope="user-top-read user-library-read playlist-modify-public"
)

@app.route('/')
def home():
    return '<a href="/login">Log in with Spotify</a>'

@app.route('/login')
def login():
    return redirect(sp_oauth.get_authorize_url())

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect('/dashboard')

@app.route('/dashboard')
def dashboard():
    token_info = session.get('token_info', None)
    if not token_info:
        return redirect('/login')
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_data = sp.current_user()
    return jsonify(user_data)

if __name__ == '__main__':
    app.run(debug=True)