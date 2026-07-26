from flask import Flask, request, jsonify
from imdb import Cinemagoer

app = Flask(__name__)
ia = Cinemagoer()

@app.route("/", methods=["GET"])
def imdb_search():
    query = request.args.get("query")

    if not query:
        return jsonify({
            "status": False,
            "message": "Missing query parameter"
        }), 400

    try:
        results = ia.search_movie(query)

        if not results:
            return jsonify({
                "status": False,
                "message": "No results found"
            }), 404

        movie = results[0]
        ia.update(movie)

        data = {
            "status": True,
            "title": movie.get("title"),
            "year": movie.get("year"),
            "imdb_id": f"tt{movie.movieID}",
            "kind": movie.get("kind"),
            "rating": movie.get("rating"),
            "genres": movie.get("genres"),
            "plot": movie.get("plot outline"),
            "runtime": movie.get("runtimes"),
            "languages": movie.get("languages"),
            "countries": movie.get("countries"),
            "cast": [x["name"] for x in movie.get("cast", [])[:10]],
            "directors": [x["name"] for x in movie.get("director", [])],
            "writers": [x["name"] for x in movie.get("writer", [])],
        }

        return jsonify(data)

    except Exception as e:
        return jsonify({
            "status": False,
            "error": str(e)
        }), 500

app = app
