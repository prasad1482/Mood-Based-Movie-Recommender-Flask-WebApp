import pandas as pd

# Load the data
movies = pd.read_csv('movies.csv')
ratings = pd.read_csv('ratings.csv')
# Mood-to-genre mapping
mood_to_genre = {
    'adventurous': ['Action', 'Adventure', 'Thriller'],
    'romantic': ['Romance', 'Drama'],
    'funny': ['Comedy'],
    'scared': ['Horror', 'Thriller'],
    'thoughtful': ['Documentary', 'Drama']
}
# Recommendation function
def recommend_movies(mood, num_recommendations=5):
    target_genres = mood_to_genre.get(mood.lower(), [])
    if not target_genres:
        return "Oops! Mood not recognized. Try adventurous, romantic, etc."
    
    filtered_movies = movies[movies['genres'].apply(
        lambda x: any(genre in x for genre in target_genres)
    )]
    
    movie_ratings = pd.merge(filtered_movies, ratings, on='movieId')
    avg_ratings = movie_ratings.groupby('title')['rating'].mean().sort_values(ascending=False)
    
    return avg_ratings.head(num_recommendations)

# Ask user for mood
user_mood = input("How are you feeling today? (adventurous, romantic, etc.): ")
recommendations = recommend_movies(user_mood)

print("\nHere are your movie recommendations:")
print(recommendations)