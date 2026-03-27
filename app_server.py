import os
import sqlite3
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import hashlib

app = Flask(__name__, static_folder='public')
CORS(app)

DB_PATH = 'database.db'

# --- Preload Data Sets ---
DEFAULT_EVENTS_EN = [
    { "id": "ev-1", "title": "Sunset Rooftop DJ Set", "type": "music", "source": "tiktok", "sourceName": "@medellinbeats", "price": "$50.000 COP", "trending": True, "date": "This Friday, 6 PM", "location": "Calle 10A #36-22, El Poblado, Medellín", "lat": 6.2088, "lng": -75.5677, "image": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=600&q=80", "desc": "Experience the best sunset view in Poblado with deep house beats. Spotted trending on TikTok, this rooftop is the place to be. Ticket includes one complimentary welcome drink.", "embedUrl": "https://www.tiktok.com/embed/v2/7617913913945984263" },
    { "id": "ev-2", "title": "Modern Art After Hours", "type": "art", "source": "insta", "sourceName": "@mammedellin", "price": "Free", "trending": False, "date": "Wednesday, 7 PM", "location": "Cra. 44 #19a-100 (MAMM), Ciudad del Río", "lat": 6.2235, "lng": -75.5756, "image": "https://images.unsplash.com/photo-1536924940846-227afb31e2a5?auto=format&fit=crop&w=600&q=80", "desc": "Exclusive after-hours access to the new immersive exhibition. Live ambient music and wine tasting. Perfect for a chic mid-week escape.", "embedUrl": "https://www.instagram.com/p/CqzhCUSO_Qj/embed" },
    { "id": "ev-3", "title": "Hidden Gastronomy Tour", "type": "food", "source": "tiktok", "sourceName": "@foodie_paisa", "price": "$120.000 COP", "trending": False, "date": "Saturday, 12 PM", "location": "Av. 74B #39B-12, Laureles, Medellín", "lat": 6.2413, "lng": -75.5947, "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=600&q=80", "desc": "A secret 5-stop food tour highlighting the best undiscovered street food and high-end bites in Laureles. Bring an empty stomach!", "embedUrl": "https://www.tiktok.com/embed/v2/7161821896790936838" },
    { "id": "ev-4", "title": "Underground Tech Rave", "type": "music", "source": "insta", "sourceName": "@underground.mde", "price": "$80.000 COP", "trending": True, "date": "Saturday, 11 PM", "location": "Cra. 43G #24-10, Barrio Colombia, Medellín", "lat": 6.2201, "lng": -75.5721, "image": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80", "desc": "Industrial warehouse party featuring international techno DJs. The location is sent exclusively via DM, but we have the scoop here.", "embedUrl": "https://www.instagram.com/p/CrTzYwzOCrB/embed" }
]

DEFAULT_EVENTS_ES = [
    { "id": "ev-1", "title": "DJ Set en Azotea al Atardecer", "type": "music", "source": "tiktok", "sourceName": "@medellinbeats", "price": "$50.000 COP", "trending": True, "date": "Este Viernes, 6 PM", "location": "Calle 10A #36-22, El Poblado, Medellín", "lat": 6.2088, "lng": -75.5677, "image": "https://images.unsplash.com/photo-1516450360452-9312f5e86fc7?auto=format&fit=crop&w=600&q=80", "desc": "Experimenta la mejor vista del atardecer en el Poblado con ritmos de deep house. Tendencia en TikTok, esta terraza es el lugar ideal. La entrada incluye una bebida de cortesía.", "embedUrl": "https://www.tiktok.com/embed/v2/7617913913945984263" },
    { "id": "ev-2", "title": "Arte Moderno Después de Horas", "type": "art", "source": "insta", "sourceName": "@mammedellin", "price": "Gratis", "trending": False, "date": "Miércoles, 7 PM", "location": "Cra. 44 #19a-100 (MAMM), Ciudad del Río", "lat": 6.2235, "lng": -75.5756, "image": "https://images.unsplash.com/photo-1536924940846-227afb31e2a5?auto=format&fit=crop&w=600&q=80", "desc": "Acceso exclusivo fuera de horario a la nueva exposición inmersiva. Música ambiental en vivo y cata de vinos. Perfecto para un escape chic a mitad de semana.", "embedUrl": "https://www.instagram.com/p/CqzhCUSO_Qj/embed" },
    { "id": "ev-3", "title": "Tour Gastronómico Oculto", "type": "food", "source": "tiktok", "sourceName": "@foodie_paisa", "price": "$120.000 COP", "trending": False, "date": "Sábado, 12 PM", "location": "Av. 74B #39B-12, Laureles, Medellín", "lat": 6.2413, "lng": -75.5947, "image": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=600&q=80", "desc": "Un tour gastronómico secreto de 5 paradas destacando la mejor comida callejera por descubrir y bocados de alta gama en Laureles. ¡Ven con el estómago vacío!", "embedUrl": "https://www.tiktok.com/embed/v2/7161821896790936838" },
    { "id": "ev-4", "title": "Rave Techno Subterráneo", "type": "music", "source": "insta", "sourceName": "@underground.mde", "price": "$80.000 COP", "trending": True, "date": "Sábado, 11 PM", "location": "Cra. 43G #24-10, Barrio Colombia, Medellín", "lat": 6.2201, "lng": -75.5721, "image": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80", "desc": "Fiesta industrial en una bodega con DJs de techno internacionales. La ubicación se envía exclusivamente por DM, pero aquí tenemos la primicia.", "embedUrl": "https://www.instagram.com/p/CrTzYwzOCrB/embed" }
]

ui_translations = {
    "en": {
        "nav_events": "Events", "nav_map": "Map", "nav_trending": "Trending", "nav_explore": "Explore",
        "hero_title": "DISCOVER MEDELLÍN", "hero_sub": "Find curated events based on trending spots from TikTok and Instagram. Immersive experiences wait in the city of eternal spring.",
        "back_btn": "← Back to Details", "detail_location": "Location", "detail_date": "Date & Time",
        "detail_cost": "Cost", "detail_map_btn": "View Ubication on Map & Routes", "detail_uber_btn": "🚗 Get Ride with Uber",
        "detail_info_btn": "Get Info / Tickets", "user_location": "You are here"
    },
    "es": {
        "nav_events": "Eventos", "nav_map": "Mapa", "nav_trending": "Tendencias", "nav_explore": "Explorar",
        "hero_title": "DESCUBRE MEDELLÍN", "hero_sub": "Encuentra eventos curados basados en los lugares de moda en TikTok e Instagram. Experiencias inmersivas te esperan en la ciudad de la eterna primavera.",
        "back_btn": "← Volver a Detalles", "detail_location": "Ubicación", "detail_date": "Fecha y Hora",
        "detail_cost": "Costo", "detail_map_btn": "Ver Ubicación en Mapa y Rutas", "detail_uber_btn": "🚗 Viajar con Uber",
        "detail_info_btn": "Más info / Entradas", "user_location": "Estás aquí"
    }
}

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        internal_id TEXT,
        title TEXT,
        type TEXT,
        source TEXT,
        sourceName TEXT,
        price TEXT,
        trending BOOLEAN,
        date TEXT,
        location TEXT,
        lat REAL,
        lng REAL,
        image TEXT,
        desc TEXT,
        embedUrl TEXT,
        lang TEXT,
        status TEXT NOT NULL,
        organizer_id INTEGER
    )''')
    
    # Create default admin if not exists
    c.execute("SELECT id FROM users WHERE email='admin@urbandiscovery.com'")
    if not c.fetchone():
        c.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)", 
                  ('admin@urbandiscovery.com', hash_pw('admin123'), 'admin'))
    
    # Preload default events if table is empty
    c.execute("SELECT COUNT(*) FROM events")
    if c.fetchone()[0] == 0:
        for ev in DEFAULT_EVENTS_EN:
            c.execute('''INSERT INTO events 
                (internal_id, title, type, source, sourceName, price, trending, date, location, lat, lng, image, desc, embedUrl, lang, status, organizer_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                (ev['id'], ev['title'], ev['type'], ev['source'], ev['sourceName'], ev['price'], ev['trending'], ev['date'], ev['location'], ev['lat'], ev['lng'], ev['image'], ev['desc'], ev['embedUrl'], 'en', 'approved', 1))
        
        for ev in DEFAULT_EVENTS_ES:
            c.execute('''INSERT INTO events 
                (internal_id, title, type, source, sourceName, price, trending, date, location, lat, lng, image, desc, embedUrl, lang, status, organizer_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                (ev['id'], ev['title'], ev['type'], ev['source'], ev['sourceName'], ev['price'], ev['trending'], ev['date'], ev['location'], ev['lat'], ev['lng'], ev['image'], ev['desc'], ev['embedUrl'], 'es', 'approved', 1))
    
    conn.commit()
    conn.close()

# Avoid caching in dev
@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response

# Static routing
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return app.send_static_file(path)

# --- API Endpoints ---
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    # Transform flat lat/lng back to coords array for the frontend
    if 'lat' in d and 'lng' in d:
        d['coords'] = [d['lat'], d['lng']]
    if 'internal_id' in d:
        d['id'] = d['internal_id']
    return d

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = dict_factory
    return conn

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT id, email, role FROM users WHERE email=? AND password_hash=?", (email, hash_pw(password)))
    user = c.fetchone()
    conn.close()
    
    if user:
        return jsonify({"success": True, "user": user})
    return jsonify({"success": False, "message": "Invalid email or password"})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user') # 'user' or 'organizer' (simulated payment later)
    
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)", (email, hash_pw(password), role))
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        return jsonify({"success": True, "user": {"id": user_id, "email": email, "role": role}})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "message": "Email already exists"})

@app.route('/api/events', methods=['GET'])
def get_events():
    lang = request.args.get('lang', 'en')
    admin_view = request.args.get('admin', 'false') == 'true'
    
    conn = get_db()
    c = conn.cursor()
    
    if admin_view:
        # Admins see all events for verification
        c.execute("SELECT * FROM events WHERE lang=?", (lang,))
    else:
        # Normal users only see approved events
        c.execute("SELECT * FROM events WHERE lang=? AND status='approved'", (lang,))
        
    events = c.fetchall()
    conn.close()
    
    ui = ui_translations.get(lang, ui_translations['en'])
    
    return jsonify({
        "events": events,
        "ui": ui
    })

@app.route('/api/events', methods=['POST'])
def create_event():
    # Only Organizers should call this
    data = request.json
    
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('''INSERT INTO events 
            (internal_id, title, type, source, sourceName, price, trending, date, location, lat, lng, image, desc, embedUrl, lang, status, organizer_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)''', 
            (f"new-{data['title'][:3]}", data['title'], data['type'], 'custom', data.get('sourceName', 'Organizer'), data['price'], False, data['date'], data['location'], data['lat'], data['lng'], data['image'], data['desc'], '', 'en', data.get('organizer_id', 0)))
        
        # Insert Spanish copy (auto-translated basically or just duplicate for demo)
        c.execute('''INSERT INTO events 
            (internal_id, title, type, source, sourceName, price, trending, date, location, lat, lng, image, desc, embedUrl, lang, status, organizer_id) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)''', 
            (f"new-{data['title'][:3]}", data['title'], data['type'], 'custom', data.get('sourceName', 'Organizer'), data['price'], False, data['date'], data['location'], data['lat'], data['lng'], data['image'], data['desc'], '', 'es', data.get('organizer_id', 0)))
            
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Event submitted for admin verification"})
    except Exception as e:
        conn.close()
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/admin/verify/<string:event_id>', methods=['POST'])
def verify_event(event_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE events SET status='approved' WHERE internal_id=?", (event_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/admin/reject/<string:event_id>', methods=['POST'])
def reject_event(event_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE events SET status='rejected' WHERE internal_id=?", (event_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/user/upgrade', methods=['POST'])
def upgrade_user():
    user_id = request.json.get('id')
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET role='organizer' WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


# ========================================
# BOT CONTROL PANEL API ENDPOINTS
# ========================================
import threading

@app.route('/api/bot/scan-url', methods=['POST'])
def bot_scan_url():
    """Process a single TikTok URL through the AI bot pipeline."""
    url = request.json.get('url', '')
    if 'tiktok.com' not in url.lower():
        return jsonify({"success": False, "message": "Solo se soportan URLs de TikTok"})
    
    try:
        from ai_event_bot import get_tiktok_metadata, process_event, inject_to_database
        metadata = get_tiktok_metadata(url)
        if metadata['success']:
            event = process_event(metadata, url)
            injected = inject_to_database(event)
            if injected:
                return jsonify({"success": True, "message": f"Evento '{event['title']}' procesado y guardado como pendiente.", "event": event})
            else:
                return jsonify({"success": False, "message": "Evento duplicado o error en la BD."})
        return jsonify({"success": False, "message": "No se pudo extraer metadata del video."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/bot/accounts', methods=['GET'])
def bot_get_accounts():
    """Return the list of tracked TikTok accounts."""
    try:
        from ai_event_bot import TRACKED_ACCOUNTS
        return jsonify({"success": True, "accounts": TRACKED_ACCOUNTS})
    except Exception as e:
        return jsonify({"success": False, "accounts": [], "message": str(e)})

@app.route('/api/bot/accounts', methods=['POST'])
def bot_update_accounts():
    """Update the tracked accounts list at runtime."""
    new_accounts = request.json.get('accounts', [])
    try:
        import ai_event_bot
        ai_event_bot.TRACKED_ACCOUNTS = new_accounts
        return jsonify({"success": True, "message": f"Lista actualizada: {len(new_accounts)} cuentas."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/bot/scan-all', methods=['POST'])
def bot_scan_all():
    """Trigger a full scan of all tracked accounts in a background thread."""
    try:
        from ai_event_bot import scan_tracked_accounts
        
        def run_scan():
            scan_tracked_accounts()
        
        t = threading.Thread(target=run_scan, daemon=True)
        t.start()
        return jsonify({"success": True, "message": "Rastreo iniciado en segundo plano. Los eventos apareceran como pendientes."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/bot/stats', methods=['GET'])
def bot_stats():
    """Return bot statistics from the database."""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as count FROM events WHERE source='tiktok' AND status='pending'")
    pending = c.fetchone()['count']
    c.execute("SELECT COUNT(*) as count FROM events WHERE source='tiktok' AND status='approved'")
    approved = c.fetchone()['count']
    c.execute("SELECT COUNT(*) as count FROM events WHERE source='tiktok'")
    total = c.fetchone()['count']
    conn.close()
    return jsonify({"success": True, "pending": pending, "approved": approved, "total": total})


# Initialize DB on import (works with both dev server and Gunicorn)
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    print(f"Starting Flask API Server with RBAC on port {port}...")
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)

