import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Replace with your TMDB API Key (v3)
TMDB_API_KEY = "7dda7d9a179f825b2e92e75ed67fa185"

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

        # Step 2: Fetch detailed info + IMDb ID + Credits (Cast/Director)
        detail_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits,external_ids"
        movie = requests.get(detail_url).json()

        # Step 3: Poster image URL formatting
        poster_path = movie.get("poster_path")
        poster_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None

        credits = movie.get("credits", {})
        cast = [member["name"] for member in credits.get("cast", [])[:10]]
        directors = [member["name"] for member in credits.get("crew", []) if member.get("job") == "Director"]
        writers = [member["name"] for member in credits.get("crew", []) if member.get("job") in ["Writer", "Screenplay"]]

        data = {
            "status": True,
            "title": movie.get("title"),
            "year": movie.get("release_date", "").split("-")[0] if movie.get("release_date") else None,
            "imdb_id": movie.get("external_ids", {}).get("imdb_id"),
            "kind": "movie",
            "rating": str(round(movie.get("vote_average", 0), 1)),
            "genres": [g["name"] for g in movie.get("genres", [])],
            "plot": movie.get("overview"),
            "runtime": f"{movie.get('runtime')} mins" if movie.get("runtime") else None,
            "languages": [l["english_name"] for l in movie.get("spoken_languages", [])],
            "countries": [c["name"] for c in movie.get("origin_country", [])],
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
