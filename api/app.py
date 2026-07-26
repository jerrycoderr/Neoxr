import os
import re
import json
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Replace with your TMDB API Key (v3)
TMDB_API_KEY = "7dda7d9a179f825b2e92e75ed67fa185"

def get_imdb_poster(imdb_id):
    """
    Fetches the exact official poster directly from IMDb page schema data.
    """
    if not imdb_id:
        return None

    try:
        url = f"https://www.imdb.com/title/{imdb_id}/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code == 200:
            # Extract structured JSON-LD data from IMDb HTML
            match = re.search(r'<script type="application/ld\+json">(.*?)</script>', response.text, re.DOTALL)
            if match:
                data = json.loads(match.group(1))
                poster = data.get("image")
                if poster:
                    # Strip resolution crop params to get original high-res poster
                    return re.sub(r'\._V1_.*?\.', '.', poster)
    except Exception:
        pass

    return None

@app.route("/", methods=["GET"])
def search_movie():
    query = request.args.get("query")

    if not query:
        return jsonify({
            "status": False,
            "message": "Missing query parameter"
        }), 400

    try:
        # Step 1: Search movie on TMDB
        search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
        search_res = requests.get(search_url).json()

        results = search_res.get("results", [])
        if not results:
            return jsonify({
                "status": False,
                "message": "No results found"
            }), 404

        movie_id = results[0]["id"]

        # Step 2: Fetch details + IMDb ID + Credits
        detail_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits,external_ids"
        movie = requests.get(detail_url).json()

        imdb_id = movie.get("external_ids", {}).get("imdb_id")

        # Step 3: Get exact official IMDb poster
        imdb_poster_url = get_imdb_poster(imdb_id)

        # Fallback to TMDB poster if IMDb poster fetching fails
        if not imdb_poster_url and movie.get("poster_path"):
            imdb_poster_url = f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}"

        credits = movie.get("credits", {})
        cast = [member.get("name") for member in credits.get("cast", [])[:10] if member.get("name")]
        directors = [member.get("name") for member in credits.get("crew", []) if member.get("job") == "Director"]
        writers = [member.get("name") for member in credits.get("crew", []) if member.get("job") in ["Writer", "Screenplay"]]

        data = {
            "status": True,
            "title": movie.get("title"),
            "year": movie.get("release_date", "").split("-")[0] if movie.get("release_date") else None,
            "imdb_id": imdb_id,
            "kind": "movie",
            "rating": str(round(movie.get("vote_average", 0), 1)),
            "genres": [g.get("name") for g in movie.get("genres", []) if g.get("name")],
            "plot": movie.get("overview"),
            "runtime": f"{movie.get('runtime')} mins" if movie.get("runtime") else None,
            "languages": [l.get("english_name") for l in movie.get("spoken_languages", []) if l.get("english_name")],
            "countries": [c.get("name") for c in movie.get("production_countries", []) if c.get("name")],
            "poster": imdb_poster_url,
            "cast": cast,
            "directors": directors,
            "writers": writers
        }

        return jsonify(data)

    except Exception as e:
        return jsonify({
            "status": False,
            "error": str(e)
        }), 500
