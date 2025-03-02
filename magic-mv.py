import sys
import codecs
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import timedelta
import requests
import os
from dotenv import load_dotenv
from fuzzywuzzy import process
from textblob import TextBlob
import spacy
from apscheduler.schedulers.background import BackgroundScheduler

# Force UTF-8 encoding
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Load environment variables
load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Load spaCy model for NLP
nlp = spacy.load("en_core_web_sm")

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    favorites = db.relationship('Favorite', backref='user', lazy=True)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

# User loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Fetch TMDB genre list
def get_tmdb_genres():
    url = "https://api.themoviedb.org/3/genre/movie/list"
    params = {"api_key": TMDB_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return {genre["name"].lower(): genre["id"] for genre in response.json()["genres"]}
    except requests.exceptions.RequestException as e:
        print(f"Error fetching genres: {e}".encode('utf-8', 'replace'))
        return {}

# Fetch trending movies
def get_trending_movies():
    url = "https://api.themoviedb.org/3/trending/movie/week"
    params = {"api_key": TMDB_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()["results"][:5]  # Fetch top 5 trending movies
    except requests.exceptions.RequestException as e:
        print(f"Error fetching trending movies: {e}".encode('utf-8', 'replace'))
        return []

# Correct spelling using fuzzywuzzy
def correct_spelling(text):
    mood_keywords = [
        "adventurous", "romantic", "scared", "thoughtful", "nostalgic", 
        "inspired", "angry", "arrogant", "sad", "joyful", "neutral"
    ]
    corrected_text = []
    for word in text.split():
        closest_match, confidence = process.extractOne(word, mood_keywords)
        if confidence > 70:  # Only correct if confidence is high
            corrected_text.append(closest_match)
        else:
            corrected_text.append(word)
    return " ".join(corrected_text)

# NLP-based mood detection
def detect_mood_from_text(text):
    # Correct spelling
    corrected_text = correct_spelling(text)
    print(f"Corrected text: {corrected_text}".encode('utf-8', 'replace'))  # Debug print

    # Sentiment analysis
    blob = TextBlob(corrected_text)
    sentiment = blob.sentiment.polarity
    print(f"Sentiment polarity: {sentiment}".encode('utf-8', 'replace'))  # Debug print

    # Mood detection based on sentiment
    if sentiment > 0.6:
        print("Detected mood: joyful".encode('utf-8', 'replace'))
        return "joyful"
    elif sentiment < -0.6:
        print("Detected mood: sad".encode('utf-8', 'replace'))
        return "sad"

    # Mood detection based on keywords
    doc = nlp(corrected_text)
    keywords = [token.text.lower() for token in doc if token.is_alpha]
    print(f"Keywords extracted: {keywords}".encode('utf-8', 'replace'))  # Debug print

    mood_keywords = {
        "adventurous": ["adventure", "climb", "explore", "mountain", "hike", "trek", "journey", "thrill", "adrenaline"],
        "romantic": ["love", "romantic", "heart", "kiss", "date", "relationship", "couple", "passion", "affection"],
        "scared": ["scary", "fear", "horror", "afraid", "terrified", "spooky", "creepy", "panic", "frightened"],
        "thoughtful": ["think", "deep", "philosophy", "reflect", "ponder", "meditate", "contemplate", "introspective", "serious"],
        "nostalgic": ["nostalgia", "memory", "past", "childhood", "old", "remember", "reminisce", "retro", "vintage"],
        "inspired": ["inspire", "motivate", "dream", "achieve", "goal", "ambition", "aspire", "encourage", "uplift"],
        "angry": ["angry", "furious", "rage", "irritated", "annoyed", "mad", "frustrated", "outraged"],
        "arrogant": ["arrogant", "cocky", "conceited", "proud", "boastful", "egotistical", "self-centered"],
        "sad": ["sad", "depressed", "unhappy", "gloomy", "heartbroken", "melancholy", "sorrow", "tearful"],
        "joyful": ["joyful", "happy", "cheerful", "excited", "delighted", "ecstatic", "elated", "blissful"]
    }

    for mood, words in mood_keywords.items():
        if any(word in keywords for word in words):
            print(f"Detected mood: {mood}".encode('utf-8', 'replace'))
            return mood

    # Fallback to sentiment if no keywords match
    if sentiment > 0:
        print("Fallback mood: joyful".encode('utf-8', 'replace'))
        return "joyful"
    elif sentiment < 0:
        print("Fallback mood: sad".encode('utf-8', 'replace'))
        return "sad"

    print("No specific mood detected. Using fallback: neutral".encode('utf-8', 'replace'))
    return "neutral"  # Fallback mood

# Map moods to TMDB genre IDs
genre_name_to_id = get_tmdb_genres()
mood_to_genre_ids = {
    "adventurous": ["action", "adventure"],
    "romantic": ["romance"],
    "funny": ["comedy"],
    "scared": ["horror"],
    "thoughtful": ["drama", "mystery"],
    "joyful": ["comedy", "animation"],
    "sad": ["drama", "romance"],
    "angry": ["action", "thriller"],
    "nostalgic": ["history", "family"],
    "inspired": ["documentary", "history"],
    "neutral": ["drama", "comedy"]  # Add this line
}

# Convert genre names to IDs
for mood, genres in mood_to_genre_ids.items():
    mood_to_genre_ids[mood] = [genre_name_to_id.get(genre, None) for genre in genres if genre in genre_name_to_id]

# Fuzzy search function
def find_closest_mood(user_input):
    print(f"User input: {user_input}".encode('utf-8', 'replace'))  # Debug print
    closest_match, confidence = process.extractOne(user_input, mood_to_genre_ids.keys())
    print(f"Closest match: {closest_match}, Confidence: {confidence}".encode('utf-8', 'replace'))  # Debug print
    return closest_match if confidence > 40 else None  # Lowered threshold to 40

# Recommendation function
def recommend_movies(mood):
    closest_mood = find_closest_mood(mood)
    if not closest_mood:
        print("No closest mood found.".encode('utf-8', 'replace'))
        return []
    genre_ids = mood_to_genre_ids.get(closest_mood.lower(), [])
    if not genre_ids:
        print(f"No genre IDs found for mood: {closest_mood}".encode('utf-8', 'replace'))
        return []
    url = "https://api.themoviedb.org/3/discover/movie"
    params = {
        "api_key": TMDB_API_KEY,
        "with_genres": ",".join(map(str, genre_ids)),
        "sort_by": "popularity.desc",
        "primary_release_year": 2024,
        "vote_count.gte": 100
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        movies = response.json()["results"][:6]
        print(f"Movies fetched: {movies}".encode('utf-8', 'replace'))  # Debug print
        return movies
    except requests.exceptions.RequestException as e:
        print(f"Error fetching movies: {e}".encode('utf-8', 'replace'))
        return []

# Routes
@app.route('/')
def home():
    trending_movies = get_trending_movies()
    return render_template('index.html', trending_movies=trending_movies)

@app.route('/recommend', methods=['POST'])
def recommend():
    user_input = request.form['mood']
    detected_mood = detect_mood_from_text(user_input)
    if detected_mood:
        recommendations = recommend_movies(detected_mood)
        return render_template('recommendations.html', recommendations=recommendations, mood=detected_mood)
    else:
        flash("No mood detected. Try again!", "error")
        return redirect(url_for('home'))

# Add to Favorites Route
@app.route('/add_favorite/<int:movie_id>', methods=['POST'])
@login_required  # Ensure only logged-in users can add favorites
def add_favorite(movie_id):
    if not current_user.is_authenticated:
        flash("You need to log in to add favorites.", "error")
        return redirect(url_for('login'))

    # Check if the movie is already in favorites
    favorite = Favorite.query.filter_by(movie_id=movie_id, user_id=current_user.id).first()
    if favorite:
        flash("This movie is already in your favorites!", "info")
    else:
        # Add the movie to favorites
        new_favorite = Favorite(movie_id=movie_id, user_id=current_user.id)
        db.session.add(new_favorite)
        db.session.commit()
        flash("Movie added to favorites!", "success")

    return redirect(url_for('home'))

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # Add password hashing in production
            login_user(user)
            flash("Login successful!", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid username or password", "error")
    return render_template('login.html')

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash("Username already exists", "error")
        else:
            new_user = User(username=username, password=password)  # Hash password in production
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
    return render_template('register.html')

# Scheduler to refresh data
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    scheduler = BackgroundScheduler()
    scheduler.add_job(get_tmdb_genres, 'interval', hours=24)
    scheduler.start()
    app.run(debug=True)