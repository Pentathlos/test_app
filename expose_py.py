import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from dotenv import load_dotenv
from urllib.parse import parse_qs
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

load_dotenv()

class ConsultMeteo(BaseHTTPRequestHandler):
    api_key = os.getenv('API_KEY')
    api_url = "https://api.openweathermap.org/data/2.5/weather"

    def do_GET(self):
        if self.path == '/':
            self.show_html('demo_py.html')  
        elif self.path.startswith('/resultat'):
            self.show_result(self.path)  
        else:
            self.send_error(404, 'Page non trouvée')

    def do_POST(self):
        if self.path == '/submit':
            self.get_parameter() 
        else:
            self.send_error(404, 'Route non trouvée')

    def get_parameter(self):
        try:
            data = self.rfile.read(int(self.headers.get('Content-Length', 0))).decode('utf-8') #lecture du contenu en octet et décodage en charactères
            city = parse_qs(data).get('city', [None])[0]
            if not city:
                self.send_error(400, 'Le paramètre "city" est manquant')
                return

            # Récupère les données météorologiques
            response = self.get_meteo(city)

        
            query_string = f"city={city}&temperature={response['temperature']}&weather={response['weather']}&humidity={response['humidity']}"
            self.send_response(303)  
            self.send_header('Location', f'/resultat?{query_string}')
            self.end_headers()

        except Exception as e:
            self.send_error(500, f'Erreur interne: {str(e)}')

    def show_html(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                html = file.read()
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
        except Exception as e:
            self.send_error(500, f'Erreur lors de la lecture du fichier: {str(e)}')

    def get_meteo(self, city):
        try:
            url = f"{self.api_url}?q={city}&appid={self.api_key}&units=metric"
            with urlopen(url) as response:
                data = json.load(response)

            if "main" not in data or "weather" not in data:
                return {"error": "Données météo non disponibles pour cette ville."}

            return {
                "city": city,
                "temperature": data["main"]["temp"],
                "weather": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"]
            }

        except HTTPError as e:
            return {"error": f"Erreur HTTP: {e.code}"}
        except URLError as e:
            return {"error": f"Erreur de connexion: {str(e)}"}
        except Exception as e:
            return {"error": f"Une erreur inattendue est survenue: {str(e)}"}

        
        
    def show_result(self, path):
        query = parse_qs(path.split('?')[1])
        city = query.get('city', [''])[0]
        temperature = query.get('temperature', [''])[0]
        weather = query.get('weather', [''])[0]
        humidity = query.get('humidity', [''])[0]

        try:
            with open('reponse.html', 'r', encoding='utf-8') as file:
                result_html = file.read()

            result_html = result_html.replace('{{city}}', city).replace('{{temperature}}', temperature).replace('{{weather}}', weather).replace('{{humidity}}', humidity)
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(result_html.encode('utf-8'))

        except Exception as e:
            self.send_error(500, f'Erreur lors de la lecture du fichier de résultats: {str(e)}')

if __name__ == '__main__':
    server_address = ('127.0.1.1', 5002)
    httpd = HTTPServer(server_address, ConsultMeteo)
    print(f'Serveur Python démarré sur http://{server_address[0]}:{server_address[1]}')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nArrêt du serveur...")
        httpd.server_close()
