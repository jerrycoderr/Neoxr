import requests
import json
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from rembg import remove
import os

# Disable parallel processing (fix for Vercel)
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
# --------------------------
# Pretty JSON Response
# --------------------------
class PrettyJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(content, indent=4, ensure_ascii=False).encode("utf-8")

app = FastAPI(
    title="AI ClearCut - Background Remover | JerryCoder",
    default_response_class=PrettyJSONResponse
)

# --------------------------
# CORS
# --------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------
# Root
# --------------------------
@app.get("/")
async def root():
    return {
        "message": "API running 🚀",
        "endpoints": {
            "POST /upload": "Upload image",
            "GET /json?url=": "Image URL"
        }
    }

# --------------------------
# Process Image
# --------------------------
def process_image(img_bytes: bytes):
    try:
        output_bytes = remove(img_bytes)

        files = {"file": ("output.png", output_bytes, "image/png")}
        r = requests.post(
            "https://ar-hosting.pages.dev/upload",
            files=files,
            timeout=20
        )

        r.raise_for_status()
        data = r.json()

        if "url" in data:
            return {
                "status": "success",
                "url": data["url"]
            }

        return {"status": "error", "message": "Upload failed"}

    except Exception as e:
        return {"status": "error", "message": str(e)}


# --------------------------
# GET URL Method (YOUR NEED ✅)
# --------------------------
@app.get("/json")
async def from_url(url: str = Query(...)):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()

        return process_image(resp.content)

    except Exception as e:
        return {"status": "error", "message": str(e)}
