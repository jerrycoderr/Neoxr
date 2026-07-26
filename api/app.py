import os
import re
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Replace with your TMDB API Key (v3)
TMDB_API_KEY = "7dda7d9a179f825b2e92e75ed67fa185"

def get_imdb_poster(imdb_id):
    """
    Fetches the official poster directly from IMDb's Suggestion CDN API 
    (bypasses Vercel HTML scraping blocks).
    """
    if not imdb_id:
        return None

    try:
        # Use IMDb's unblocked Suggestion JSON API
        url = f"https://v3.sg.media-imdb.com/suggestion/x/{imdb_id}.json"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        res = requests.get(url, headers=headers, timeout=5)

        if res.status_code == 200:
            data = res.json()
            items = data.get("d", [])
            for item in items:
                if item.get("id") == imdb_id:
                    image_info = item.get("i", {})
                    image_url = image_info.get("imageUrl")
                    if image_url:
                        # Remove thumbnail cropping to get full high-res official IMDb poster
                        return re.sub(r'\._V1_.*?\.', '.', image_url)
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

        first_movie = results[0]
        movie_id = first_movie["id"]

        # Step 2: Fetch detailed info + IMDb ID + Credits
        detail_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits,external_ids"
        movie = requests.get(detail_url).json()

        imdb_id = movie.get("external_ids", {}).get("imdb_id")

        # Step 3: Fetch exact official IMDb poster from IMDb CDN
        poster_url = get_imdb_poster(imdb_id)

        # Fallback to TMDB poster if IMDb poster is unavailable
        if not poster_url and movie.get("poster_path"):
            poster_url = f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}"

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
            "poster": poster_url,
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
