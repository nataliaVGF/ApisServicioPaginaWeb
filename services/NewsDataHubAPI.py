import requests

def obtener_noticias(query, language='es', country='mx', page_size=6):
    url = "https://api.newsdatahub.com/v1/news"
    
    headers = {
        'X-API-Key': 'ndh_4p_RzLk-NLn_Q3zttF0TdEolG41UEDuRCS7PRe8cYzM',
        'User-Agent': 'NewsDataHub-API-Client/1.0'
    }
    
    params = {
        'q': query,
        'language': language,
        'country': country,
        'per_page': page_size  # Nota: es 'per_page', no 'page_size'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al consultar la API: {e}")
        return None

# Ejemplo de uso
noticias = obtener_noticias('redes')
if noticias:
    print(noticias)