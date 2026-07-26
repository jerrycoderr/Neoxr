from imdb import Cinemagoer

ia = Cinemagoer()

def handler(request):
    query = request.args.get("query")

    if not query:
        return {
            "statusCode": 400,
            "body": {
                "status": False,
                "message": "Missing query parameter"
            }
        }

    try:
        results = ia.search_movie(query)

        if not results:
            return {
                "statusCode": 404,
                "body": {
                    "status": False,
                    "message": "No results found"
                }
            }

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
            "cast": [x["name"] for x in movie.get("cast", [])[:5]],
            "directors": [x["name"] for x in movie.get("director", [])],
        }

        return {
            "statusCode": 200,
            "body": data
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": {
                "status": False,
                "error": str(e)
            }
        }
