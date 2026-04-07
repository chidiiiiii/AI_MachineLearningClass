# Content-based movie recommendations (Netflix-style: similar titles from taste text).
# Uses TF-IDF over genres + keywords from TMDB-style data.
import ast
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from movies import movies_keywords


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
    out["combined"] = out.apply(
        lambda row: " ".join(row["genres_list"] + row["keywords_list"]).lower(),
        axis=1,
    )
    out = out[out["combined"].str.len() > 0].reset_index(drop=True)
    return out


movies = _prepare_movies(movies_keywords)

# English stop words + light n-grams help match phrasing like "dark knight" / "crime drama"
_vectorizer = TfidfVectorizer(
    stop_words="english",
    min_df=2,
    ngram_range=(1, 2),
    max_features=50000,
)
_tfidf_matrix = _vectorizer.fit_transform(movies["combined"])


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
    title_key = movie_title.strip().lower()
    mask = movies["title"].str.lower().str.strip() == title_key
    if not mask.any():
        if with_scores and with_tags:
            return [("Movie not found in dataset", 0.0, [], [])]
        if with_scores:
            return [("Movie not found in dataset", 0.0)]
        return ["Movie not found in dataset"]

    # Row position in `movies` / _tfidf_matrix (0 .. n-1)
    idx = int(movies[mask].index[0])

    # One row vs all columns — avoids building an n×n similarity matrix (too large for ~45k films)
    sims = cosine_similarity(_tfidf_matrix[idx : idx + 1], _tfidf_matrix).ravel()
    ranked = sorted(enumerate(sims), key=lambda x: x[1], reverse=True)

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
