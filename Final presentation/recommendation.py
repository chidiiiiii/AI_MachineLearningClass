# Content-based movie recommendations (Netflix-style: similar titles from taste text).
# Uses TF-IDF over genres + keywords from TMDB-style data.
#
# Model build is deferred until the first recommend() call (fast import).
# After the first build, a joblib cache speeds up the next runs unless CSVs change.
import ast
from pathlib import Path

import joblib # Saves the model to make it faster to load
import pandas as pd # Data manipulation
from sklearn.feature_extraction.text import TfidfVectorizer # Convert words into numbers
from sklearn.metrics.pairwise import cosine_similarity # Compares how two movies are similar

_DIR = Path(__file__).resolve().parent
_CACHE_PATH = _DIR / "recommendation_model.joblib"
# Rebuild cache if any of these are newer than the cache file
_CACHE_DEPS = (
    _DIR / "movies_metadata.csv",
    _DIR / "keywords.csv",
    _DIR / "movies.py",
    Path(__file__).resolve(),
)

movies = None
_vectorizer = None
_tfidf_matrix = None


def _parse_json_name_list(text):
    """Turn TMDB JSON list columns into plain name strings."""
    if pd.isna(text) or text == "":
        return []
    try:
        data = ast.literal_eval(text)
        if not isinstance(data, list):
            return []
        return [
            str(item["name"])
            for item in data
            if isinstance(item, dict) and "name" in item
        ]
    except (ValueError, SyntaxError, TypeError):
        return []


def _prepare_movies(df: pd.DataFrame) -> pd.DataFrame:
    out = df.dropna(subset=["title"]).copy()
    out["genres_list"] = out["genres"].apply(_parse_json_name_list)
    out["keywords_list"] = out["keywords"].apply(_parse_json_name_list)
    gl, kl = out["genres_list"].tolist(), out["keywords_list"].tolist()
    out["combined"] = [" ".join(g + k).lower() for g, k in zip(gl, kl)]
    out = out[out["combined"].str.len() > 0].reset_index(drop=True)
    return out


def _cache_fresh() -> bool: # Checks if the cache is fresh
    if not _CACHE_PATH.is_file():
        return False
    cache_mtime = _CACHE_PATH.stat().st_mtime
    for p in _CACHE_DEPS:
        if p.is_file() and p.stat().st_mtime > cache_mtime:
            return False
    return True


def _load_from_cache():
    global movies, _vectorizer, _tfidf_matrix
    blob = joblib.load(_CACHE_PATH)
    movies = blob["movies"]
    _vectorizer = blob["vectorizer"]
    _tfidf_matrix = blob["matrix"]


def _build_and_save_cache(): 
    global movies, _vectorizer, _tfidf_matrix
    from movies import movies_keywords as _mk

    movies = _prepare_movies(_mk)
    _vectorizer = TfidfVectorizer(
        stop_words="english",
        min_df=2,
        ngram_range=(1, 2),
        max_features=50000,
    )
    _tfidf_matrix = _vectorizer.fit_transform(movies["combined"]) # Every movie is a point
    joblib.dump(
        {"movies": movies, "vectorizer": _vectorizer, "matrix": _tfidf_matrix},
        _CACHE_PATH,
    )


def ensure_model(*, verbose: bool = False) -> None:
    """
    Build or load the TF-IDF index (first call is slow; later calls use cache).
    Call this if you want to warm the model without running recommend().
    """
    global movies, _vectorizer, _tfidf_matrix
    if _tfidf_matrix is not None:
        return
    if _cache_fresh():
        if verbose:
            print(f"Loading model from cache ({_CACHE_PATH.name}) ...")
        _load_from_cache()
        if verbose:
            print(f"Ready ({len(movies):,} movies).")
        return
    if verbose:
        print("Building TF-IDF index (first time or data changed); this can take ~30-90s ...")
    _build_and_save_cache()
    if verbose:
        print(f"Saved cache to {_CACHE_PATH.name}. Ready ({len(movies):,} movies).")


def _format_names(label: str, names: list, max_show: int = 30) -> str:
    if not names:
        return f"  {label}: (none)"
    shown = names[:max_show]
    tail = ""
    if len(names) > max_show:
        tail = f" ... (+{len(names) - max_show} more)"
    return f"  {label}: {', '.join(shown)}{tail}"


def recommend(
    movie_title: str,
    num_recommendations: int = 10,
    with_scores: bool = False,
    with_tags: bool = False, 
):
    """
    Recommend movies whose genre/keyword profile is closest in cosine space.

    Parameters
    ----------
    movie_title : str
        Exact title as in the dataset (matching is case-insensitive).
    num_recommendations : int
        How many other movies to return (excluding the seed title).
    with_scores : bool
        If True, return list of (title, similarity) tuples instead of titles only.
    with_tags : bool
        If True with with_scores, each item is (title, score, genres_list, keywords_list).
        Ignored unless with_scores is True.
    """
    ensure_model(verbose=False)

    title_key = movie_title.strip().lower()
    mask = movies["title"].str.lower().str.strip() == title_key
    if not mask.any():
        if with_scores and with_tags:
            return [("Movie not found in dataset", 0.0, [], [])]
        if with_scores:
            return [("Movie not found in dataset", 0.0)]
        return ["Movie not found in dataset"]

    idx = int(movies[mask].index[0])

    sims = cosine_similarity(_tfidf_matrix[idx : idx + 1], _tfidf_matrix).ravel() # Compares how similar the movie is to the other movies
    ranked = sorted(enumerate(sims), key=lambda x: x[1], reverse=True) # Sorts the movies by how similar they are to the seed movie

    results = []
    for row_i, score in ranked[1 : num_recommendations + 1]:
        row = movies.iloc[row_i]
        t = row["title"]
        if with_scores and with_tags:
            results.append(
                (t, float(score), list(row["genres_list"]), list(row["keywords_list"]))
            )
        elif with_scores:
            results.append((t, float(score)))
        else:
            results.append(t)
    return results


if __name__ == "__main__":
    import sys

    raw = sys.argv[1:]
    quiet = any(a in ("--quiet", "-q") for a in raw)
    args = [a for a in raw if a not in ("--quiet", "-q")]

    if args:
        movie_name = " ".join(args).strip()
    else:
        movie_name = input("Enter a movie title: ").strip()

    if not movie_name:
        print("No title entered. Exiting.")
        raise SystemExit(0)

    ensure_model(verbose=True)

    print(f"\nRecommendations for '{movie_name}' (content-based, genres + keywords)\n")

    if not quiet:
        title_key = movie_name.strip().lower()
        seed_mask = movies["title"].str.lower().str.strip() == title_key
        if seed_mask.any():
            seed = movies[seed_mask].iloc[0]
            print("Your movie (what the model uses):")
            print(_format_names("Genres", seed["genres_list"]))
            print(_format_names("Keywords", seed["keywords_list"]))
            print()

    lines = recommend(
        movie_name,
        num_recommendations=10,
        with_scores=True,
        with_tags=not quiet,
    )

    for line in lines:
        if quiet:
            title, score = line
            print(f"  {score:.4f}  {title}")
        else:
            title, score, genres, kws = line
            print(f"* {score:.4f}  {title}")
            print(_format_names("  Genres", genres))
            print(_format_names("  Keywords", kws))
            print()
