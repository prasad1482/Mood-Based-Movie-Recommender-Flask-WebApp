from flask import Flask, render_template, request
import pandas as pd

app = Flask(__name__)

# Load data (same as before)
movies = pd.read_csv('movies.csv')
ratings = pd.read_csv('ratings.csv')

# Mood-to-genre mapping (same as before)
mood_to_genre = {
    'adventurous': ['Action', 'Adventure', 'Thriller'],
    'romantic': ['Romance', 'Drama'],
    'funny': ['Comedy'],
    'scared': ['Horror', 'Thriller'],
    'thoughtful': ['Documentary', 'Drama']
}

# Recommendation function (same as before)
def recommend_movies(mood):
    target_genres = mood_to_genre.get(mood.lower(), [])
    if not target_genres:
        return []
    filtered_movies = movies[movies['genres'].apply(lambda x: any(genre in x for genre in target_genres))]
    movie_ratings = pd.merge(filtered_movies, ratings, on='movieId')
    avg_ratings = movie_ratings.groupby('title')['rating'].mean().sort_values(ascending=False)
    return avg_ratings.head(5).index.tolist()  # Return top 5 movie titles

# Route for the homepage
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        user_mood = request.form['mood']
        recommendations = recommend_movies(user_mood)
        return render_template('magic-mv-web.html', recommendations=recommendations, mood=user_mood)
    return render_template('magic-mv-web.html')

if __name__ == '__main__':
    app.run(debug=True)