from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from spotipy.oauth2 import SpotifyOAuth
from spotipy import Spotify
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

# Allow frontend and Qt app to access backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Spotify OAuth setup
sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),  # e.g. http://localhost:8000/callback
    scope="user-read-playback-state user-modify-playback-state user-read-currently-playing"
)

# Store tokens in memory (replace with DB or file for persistence)
user_tokens = {}

@app.get("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return {"auth_url": auth_url}

@app.get("/callback")
def callback(code: str):
    try:
        token_info = sp_oauth.get_access_token(code)
        access_token = token_info["access_token"]
        refresh_token = token_info["refresh_token"]
        user_tokens["access_token"] = access_token
        user_tokens["refresh_token"] = refresh_token
        return FileResponse("callback.html")  # Adjust path if needed
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def get_spotify_client():
    if "access_token" not in user_tokens:
        raise HTTPException(status_code=401, detail="User not authenticated")
    return Spotify(auth=user_tokens["access_token"])

@app.get("/track")
def get_current_track():
    sp = get_spotify_client()
    playback = sp.current_playback()
    if not playback or not playback.get("item"):
        return {"name": "No track playing", "artist": ""}
    track = playback["item"]
    return {
        "name": track["name"],
        "artist": track["artists"][0]["name"],
        "album": track["album"]["name"],
        "image": track["album"]["images"][0]["url"]
    }

@app.post("/play")
def play():
    sp = get_spotify_client()
    sp.start_playback()
    return {"status": "playing"}

@app.post("/pause")
def pause():
    sp = get_spotify_client()
    sp.pause_playback()
    return {"status": "paused"}

@app.post("/next")
def next_track():
    sp = get_spotify_client()
    sp.next_track()
    return {"status": "skipped"}

@app.post("/previous")
def previous_track():
    sp = get_spotify_client()
    sp.previous_track()
    return {"status": "reversed"}
