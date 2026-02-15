from dotenv import load_dotenv 
# 🔹 Carga variables del .env
from flask import Flask, request, render_template
import requests
import os
  
load_dotenv() 
app = Flask(__name__)

# Obtener API Key desde variable de entorno
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Validar que exista
if not YOUTUBE_API_KEY:
    raise ValueError("No se encontró la variable de entorno YOUTUBE_API_KEY")

@app.route("/", methods=["GET"])
def buscar():
    tema = request.args.get("tema")
    videos = []

    if tema:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": tema,
            "type": "video",
            "maxResults": 5,
            "key": YOUTUBE_API_KEY
        }

        response = requests.get(url, params=params)
        print("STATUS:", response.status_code)

        if response.status_code == 200:
            data = response.json()

            for item in data.get("items", []):
                videos.append({
                    "title": item["snippet"]["title"],
                    "channel": item["snippet"]["channelTitle"],
                    "url": f"https://www.youtube.com/embed/{item['id']['videoId']}",
                    "thumbnail": item["snippet"]["thumbnails"]["high"]["url"]
                })
        else:
            print("Error en API:", response.text)

    return render_template("index.html", videos=videos)


if __name__ == "__main__":
    app.run(debug=True)
