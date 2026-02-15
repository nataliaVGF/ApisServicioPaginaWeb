from dotenv import load_dotenv
from flask import Flask, request, render_template
import requests
import os
import base64

# 🔹 Cargar variables del .env
load_dotenv()

# 🔹 API Keys
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

if not YOUTUBE_API_KEY:
    raise ValueError("No se encontró YOUTUBE_API_KEY en variables de entorno")
if not NEWS_API_KEY:
    raise ValueError("No se encontró NEWS_API_KEY en variables de entorno")
if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    raise ValueError("No se encontraron las credenciales de Spotify en variables de entorno")


# 🔹 Clase para noticias
class NewsDataHubAPI:
    BASE_URL = "https://api.newsdatahub.com/v1/news"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def buscar_noticias(self, termino: str, idioma="es", pais="mx", cantidad=6):
        headers = {
            'X-API-Key': self.api_key,
            'User-Agent': 'NewsDataHub-API-Client/1.0'
        }
        
        params = {
            "q": termino,
            "language": idioma,
            "country": pais,
            "per_page": cantidad
        }
        
        try:
            response = requests.get(self.BASE_URL, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            noticias = []
            results = data.get("data", [])
            
            for article in results:
                url = article.get("article_link") or article.get("url") or article.get("link")
                descripcion = article.get("description", "")
                if descripcion and len(descripcion) > 200:
                    descripcion = descripcion[:200] + "..."
                elif not descripcion:
                    descripcion = "Sin descripción disponible"
                
                if url and url != "#":
                    noticia = {
                        "titulo": article.get("title", "Sin título"),
                        "descripcion": descripcion,
                        "url": url,
                        "fuente": article.get("source_title", "Fuente desconocida"),
                        "fecha": article.get("pub_date", "Fecha desconocida")
                    }
                    noticias.append(noticia)
            
            print(f"✅ Se encontraron {len(noticias)} noticias")
            return noticias
            
        except requests.RequestException as e:
            print(f"❌ Error al consultar la API de noticias: {e}")
            return []


# 🔹 Clase para Spotify Podcasts
class SpotifyAPI:
    AUTH_URL = "https://accounts.spotify.com/api/token"
    BASE_URL = "https://api.spotify.com/v1"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None

    def _get_access_token(self):
        """Obtener token de acceso usando Client Credentials Flow"""
        try:
            # Codificar credenciales en base64
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_string.encode("utf-8")
            auth_base64 = base64.b64encode(auth_bytes).decode("utf-8")

            headers = {
                "Authorization": f"Basic {auth_base64}",
                "Content-Type": "application/x-www-form-urlencoded"
            }

            data = {"grant_type": "client_credentials"}

            response = requests.post(self.AUTH_URL, headers=headers, data=data)
            response.raise_for_status()
            
            json_result = response.json()
            self.access_token = json_result.get("access_token")
            print(f"✅ Token de Spotify obtenido correctamente")
            return self.access_token

        except requests.RequestException as e:
            print(f"❌ Error al obtener token de Spotify: {e}")
            return None

    def buscar_podcasts(self, termino: str, idioma="es", cantidad=6):
        """Buscar podcasts en Spotify"""
        if not self.access_token:
            self._get_access_token()

        if not self.access_token:
            print("❌ No se pudo obtener el token de acceso")
            return []

        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }

        params = {
            "q": termino,
            "type": "show",  # 'show' es el tipo para podcasts
            "market": "MX",  # Mercado mexicano
            "limit": cantidad
        }

        try:
            response = requests.get(f"{self.BASE_URL}/search", headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            podcasts = []
            shows = data.get("shows", {}).get("items", [])

            for show in shows:
                # Obtener la imagen más grande disponible
                images = show.get("images", [])
                imagen = images[0].get("url") if images else ""

                podcast = {
                    "nombre": show.get("name", "Sin nombre"),
                    "descripcion": show.get("description", "Sin descripción")[:200] + "..." if show.get("description") else "Sin descripción",
                    "publisher": show.get("publisher", "Desconocido"),
                    "url": show.get("external_urls", {}).get("spotify", "#"),
                    "imagen": imagen,
                    "total_episodios": show.get("total_episodes", 0)
                }
                podcasts.append(podcast)

            print(f"✅ Se encontraron {len(podcasts)} podcasts")
            return podcasts

        except requests.RequestException as e:
            print(f"❌ Error al buscar podcasts: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"📄 Respuesta del servidor: {e.response.text}")
            return []


# 🔹 Inicializar Flask y APIs
app = Flask(__name__)
news_api = NewsDataHubAPI(NEWS_API_KEY)
spotify_api = SpotifyAPI(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)


# 🔹 Ruta principal
@app.route("/", methods=["GET"])
def index():
    tema = request.args.get("tema")
    videos = []
    noticias = []
    podcasts = []
    error = None

    if tema:
        # ---- Buscar videos en YouTube ----
        url_youtube = "https://www.googleapis.com/youtube/v3/search"
        params_youtube = {
            "part": "snippet",
            "q": tema,
            "type": "video",
            "maxResults": 6,
            "key": YOUTUBE_API_KEY
        }

        try:
            response = requests.get(url_youtube, params=params_youtube)
            if response.status_code == 200:
                data = response.json()
                for item in data.get("items", []):
                    video_id = item['id']['videoId']
                    videos.append({
                        "title": item["snippet"]["title"],
                        "channel": item["snippet"]["channelTitle"],
                        "url": f"https://www.youtube.com/embed/{video_id}",
                        "video_id": video_id,
                        "thumbnail": item["snippet"]["thumbnails"]["high"]["url"]
                    })
            else:
                print(f"⚠️ Error en YouTube API: {response.status_code}")
        except Exception as e:
            print(f"❌ Error al buscar videos: {e}")

        # ---- Buscar noticias ----
        noticias = news_api.buscar_noticias(tema)

        # ---- Buscar podcasts en Spotify ----
        podcasts = spotify_api.buscar_podcasts(tema)
        
        if not noticias and not videos and not podcasts:
            error = f"No se encontraron resultados para '{tema}'"

    return render_template("index.html", videos=videos, noticias=noticias, podcasts=podcasts, error=error, tema=tema)


# 🔹 Ejecutar app
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)