import pandas as pd

# Load the movies metadata
movies_metadata = pd.read_csv("movies_metadata.csv", low_memory=False)

# Create a new dataframe with the id, title, genres, and release date
movies = movies_metadata[['id', 'title', 'genres']]

# Some rows have invalid ids (e.g. date strings); coerce to NaN then drop
movies['id'] = pd.to_numeric(movies['id'], errors='coerce')
movies = movies.dropna(subset=['id'])
movies['id'] = movies['id'].astype(int)

#print(movies.head())
#print(movies.columns)
#print(movies.info())

keywords_metadata = pd.read_csv('keywords.csv')
# One row per movie id (keywords file can contain duplicate ids)
keywords_metadata = keywords_metadata.drop_duplicates(subset=["id"], keep="first")

movies_keywords = movies.merge(keywords_metadata, on="id", how="left")

MOVIES_KEYWORDS_CSV = "movies_keywords.csv"


if __name__ == "__main__":
    movies_keywords.to_csv(MOVIES_KEYWORDS_CSV, index=False, encoding="utf-8")
    print(f"Saved {len(movies_keywords):,} rows to {MOVIES_KEYWORDS_CSV}")