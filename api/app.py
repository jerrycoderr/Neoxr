import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Replace with your free OMDb API key (or set OMDB_API_KEY environment variable in Vercel)
OMDB_API_KEY = "c7a99ffc"

@app.route("/", methods=["GET"])
def imdb_search():
    query = request.args.get("query")

    if not query:
        return jsonify({
            "status": False,
            "message": "Missing query parameter"
        }), 400

    try:
        # Search movie via OMDb
        url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&s={query}"
        response = requests.get(url).json()

        if response.get("Response") == "False":
            return jsonify({
                "status": False,
                "message": response.get("Error", "No results found")
            }), 404

        # Get first result details
        first_movie_id = response["Search"][0]["imdbID"]
        detail_url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&i={first_movie_id}&plot=full"
        movie = requests.get(detail_url).json()

        data = {
            "status": True,
            "title": movie.get("Title"),
            "year": movie.get("Year"),
            "imdb_id": movie.get("imdbID"),
            "kind": movie.get("Type"),
            "rating": movie.get("imdbRating"),
            "genres": movie.get("Genre", "").split(", ") if movie.get("Genre") else [],
            "plot": movie.get("Plot"),
            "runtime": movie.get("Runtime"),
            "languages": movie.get("Language"),
            "countries": movie.get("Country"),
            "cast": movie.get("Actors", "").split(", ") if movie.get("Actors") else [],
            "directors": movie.get("Director", "").split(", ") if movie.get("Director") else [],
            "writers": movie.get("Writer", "").split(", ") if movie.get("Writer") else [],
            "poster": movie.get("Poster")
        }

        return jsonify(data)

    except Exception as e:
        return jsonify({
            "status": False,
            "error": str(e)
        }), 500
