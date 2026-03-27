import http.server
import socketserver
import json
import urllib.parse
import os

PORT = 8081
DIRECTORY = "public"

events_en = [
    {
        "id": "ev-1",
        "title": "Sunset Rooftop DJ Set",
        "type": "music",
        "source": "tiktok",
        "sourceName": "@medellinbeats",
        "price": "$50.000 COP",
        "trending": True,
        "date": "This Friday, 6 PM",
        "location": "Calle 10A #36-22, El Poblado, Medellín",
        "coords": [6.2088, -75.5677],
        "image": "https://images.unsplash.com/photo-1571266028243-3716f02d2d2e?auto=format&fit=crop&w=600&q=80",
        "desc": "Experience the best sunset view in Poblado with deep house beats. Spotted trending on TikTok, this rooftop is the place to be. Ticket includes one complimentary welcome drink.",
        "embedUrl": "https://www.tiktok.com/embed/v2/7617913913945984263"
    },
    {
        "id": "ev-2",
        "title": "Modern Art After Hours",
        "type": "art",
        "source": "insta",
        "sourceName": "@mammedellin",
        "price": "Free",
        "date": "Wednesday, 7 PM",
        "location": "Cra. 44 #19a-100 (MAMM), Ciudad del Río",
        "coords": [6.2235, -75.5756],
        "image": "https://images.unsplash.com/photo-1536924940846-227afb31e2a5?auto=format&fit=crop&w=600&q=80",
        "desc": "Exclusive after-hours access to the new immersive exhibition. Live ambient music and wine tasting. Perfect for a chic mid-week escape.",
        "embedUrl": "https://www.instagram.com/p/CqzhCUSO_Qj/embed"
    },
    {
        "id": "ev-3",
        "title": "Hidden Gastronomy Tour",
        "type": "food",
        "source": "tiktok",
        "sourceName": "@foodie_paisa",
        "price": "$120.000 COP",
        "date": "Saturday, 12 PM",
        "location": "Av. 74B #39B-12, Laureles, Medellín",
        "coords": [6.2413, -75.5947],
        "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=600&q=80",
        "desc": "A secret 5-stop food tour highlighting the best undiscovered street food and high-end bites in Laureles. Bring an empty stomach!",
        "embedUrl": "https://www.tiktok.com/embed/v2/7161821896790936838"
    },
    {
        "id": "ev-4",
        "title": "Underground Tech Rave",
        "type": "music",
        "source": "insta",
        "sourceName": "@underground.mde",
        "price": "$80.000 COP",
        "trending": True,
        "date": "Saturday, 11 PM",
        "location": "Cra. 43G #24-10, Barrio Colombia, Medellín",
        "coords": [6.2201, -75.5721],
        "image": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80",
        "desc": "Industrial warehouse party featuring international techno DJs. The location is sent exclusively via DM, but we have the scoop here.",
        "embedUrl": "https://www.instagram.com/p/CrTzYwzOCrB/embed"
    }
]

events_es = [
    {
        "id": "ev-1",
        "title": "DJ Set en Azotea al Atardecer",
        "type": "music",
        "source": "tiktok",
        "sourceName": "@medellinbeats",
        "price": "$50.000 COP",
        "trending": True,
        "date": "Este Viernes, 6 PM",
        "location": "Calle 10A #36-22, El Poblado, Medellín",
        "coords": [6.2088, -75.5677],
        "image": "https://images.unsplash.com/photo-1571266028243-3716f02d2d2e?auto=format&fit=crop&w=600&q=80",
        "desc": "Experimenta la mejor vista del atardecer en el Poblado con ritmos de deep house. Tendencia en TikTok, esta terraza es el lugar ideal. La entrada incluye una bebida de cortesía.",
        "embedUrl": "https://www.tiktok.com/embed/v2/7617913913945984263"
    },
    {
        "id": "ev-2",
        "title": "Arte Moderno Después de Horas",
        "type": "art",
        "source": "insta",
        "sourceName": "@mammedellin",
        "price": "Gratis",
        "date": "Miércoles, 7 PM",
        "location": "Cra. 44 #19a-100 (MAMM), Ciudad del Río",
        "coords": [6.2235, -75.5756],
        "image": "https://images.unsplash.com/photo-1536924940846-227afb31e2a5?auto=format&fit=crop&w=600&q=80",
        "desc": "Acceso exclusivo fuera de horario a la nueva exposición inmersiva. Música ambiental en vivo y cata de vinos. Perfecto para un escape chic a mitad de semana.",
        "embedUrl": "https://www.instagram.com/p/CqzhCUSO_Qj/embed"
    },
    {
        "id": "ev-3",
        "title": "Tour Gastronómico Oculto",
        "type": "food",
        "source": "tiktok",
        "sourceName": "@foodie_paisa",
        "price": "$120.000 COP",
        "date": "Sábado, 12 PM",
        "location": "Av. 74B #39B-12, Laureles, Medellín",
        "coords": [6.2413, -75.5947],
        "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=600&q=80",
        "desc": "Un tour gastronómico secreto de 5 paradas destacando la mejor comida callejera por descubrir y bocados de alta gama en Laureles. ¡Ven con el estómago vacío!",
        "embedUrl": "https://www.tiktok.com/embed/v2/7161821896790936838"
    },
    {
        "id": "ev-4",
        "title": "Rave Techno Subterráneo",
        "type": "music",
        "source": "insta",
        "sourceName": "@underground.mde",
        "price": "$80.000 COP",
        "trending": True,
        "date": "Sábado, 11 PM",
        "location": "Cra. 43G #24-10, Barrio Colombia, Medellín",
        "coords": [6.2201, -75.5721],
        "image": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80",
        "desc": "Fiesta industrial en una bodega con DJs de techno internacionales. La ubicación se envía exclusivamente por DM, pero aquí tenemos la primicia.",
        "embedUrl": "https://www.instagram.com/p/CrTzYwzOCrB/embed"
    }
]

ui_translations = {
    "en": {
        "nav_events": "Events",
        "nav_map": "Map",
        "nav_trending": "Trending",
        "nav_explore": "Explore",
        "hero_title": "DISCOVER MEDELLÍN",
        "hero_sub": "Find curated events based on trending spots from TikTok and Instagram. Immersive experiences wait in the city of eternal spring.",
        "back_btn": "← Back to Details",
        "detail_location": "Location",
        "detail_date": "Date & Time",
        "detail_cost": "Cost",
        "detail_map_btn": "View Ubication on Map & Routes",
        "detail_uber_btn": "🚗 Get Ride with Uber",
        "detail_info_btn": "Get Info / Tickets",
        "user_location": "You are here"
    },
    "es": {
        "nav_events": "Eventos",
        "nav_map": "Mapa",
        "nav_trending": "Tendencias",
        "nav_explore": "Explorar",
        "hero_title": "DESCUBRE MEDELLÍN",
        "hero_sub": "Encuentra eventos curados basados en los lugares de moda en TikTok e Instagram. Experiencias inmersivas te esperan en la ciudad de la eterna primavera.",
        "back_btn": "← Volver a Detalles",
        "detail_location": "Ubicación",
        "detail_date": "Fecha y Hora",
        "detail_cost": "Costo",
        "detail_map_btn": "Ver Ubicación en Mapa y Rutas",
        "detail_uber_btn": "🚗 Viajar con Uber",
        "detail_info_btn": "Más info / Entradas",
        "user_location": "Estás aquí"
    }
}

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        
        if parsed_path.path == '/api/events':
            query = urllib.parse.parse_qs(parsed_path.query)
            lang = query.get('lang', ['en'])[0]
            
            data = {
                "events": events_es if lang == 'es' else events_en,
                "ui": ui_translations.get(lang, ui_translations['en'])
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))
            return
            
        return super().do_GET()

if __name__ == "__main__":
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()
