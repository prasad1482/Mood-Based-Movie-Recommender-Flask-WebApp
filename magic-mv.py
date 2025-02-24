from flask import Flask, render_template, request
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")  # Load API key from .env

app = Flask(__name__)

# Fetch TMDB genre list
def get_tmdb_genres():
    url = "https://api.themoviedb.org/3/genre/movie/list"
    params = {"api_key": TMDB_API_KEY}  # Use the loaded API key
    response = requests.get(url, params=params)
    return {genre["name"].lower(): genre["id"] for genre in response.json()["genres"]}

# Map moods to TMDB genre IDs
genre_name_to_id = get_tmdb_genres()
mood_to_genre_ids = {
    "adventurous": ["action", "adventure"],
    "romantic": ["romance"],
    "funny": ["comedy"],
    "scared": ["horror"],
    "thoughtful": ["drama", "mystery"]
}

# Convert genre names to IDs
for mood, genres in mood_to_genre_ids.items():
    mood_to_genre_ids[mood] = [genre_name_to_id[genre] for genre in genres]

# Recommendation function
def recommend_movies(mood):
    genre_ids = mood_to_genre_ids.get(mood.lower(), [])
    if not genre_ids:
        return []
    
    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "with_genres": ",".join(map(str, genre_ids)),
        "sort_by": "popularity.desc",
        "primary_release_year": 2024,
        "vote_count.gte": 100
    }
    response = requests.get(url, params=params)
    return response.json()["results"][:6]  # Top 6 movies

# Routes
@app.route('/', methods=['GET', 'POST'])
def home():
    recommendations = []
    mood = ""
    if request.method == 'POST':
        mood = request.form['mood']
        recommendations = recommend_movies(mood)
    return render_template('magic-mv-web.html', recommendations=recommendations, mood=mood)

if __name__ == '__main__':
    app.run(debug=True)