"""
==========================================================================
  URBAN DISCOVERY - AI EVENT BOT V2 (Automated + Gemini AI)
  
  Modos de uso:
    1. Manual:    python ai_event_bot.py "https://tiktok.com/..."
    2. Automatico: python ai_event_bot.py --auto
    
  El modo automatico rastrea cuentas de TikTok cada 6 horas,
  extrae metadatos de videos nuevos, los analiza con Gemini AI,
  y los inyecta en la base de datos como eventos 'pending'.
==========================================================================
"""

import sys
import json
import sqlite3
import requests
import random
import os
import re
import time
import threading
from datetime import datetime

# Fix Windows console encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
DB_PATH = 'database.db'

# ============================================================
# CONFIGURACION: Cuentas de TikTok a rastrear automaticamente
# Agrega o quita cuentas aqui para controlar que creadores sigue el bot
# ============================================================
TRACKED_ACCOUNTS = [
    "quehacerenmde",
    "medellin.travel", 
    "foodie_paisa",
    "medellinbeats",
    "planesmedellin",
    "colombia.travel",
    "medabordo",
]

# Intervalo entre rastreos automaticos (en segundos)
SCAN_INTERVAL = 6 * 60 * 60  # 6 horas

# ============================================================
# GEMINI AI - Analisis inteligente de contenido
# ============================================================
def analyze_with_gemini(text, author):
    """Usa Gemini AI real para extraer datos estructurados de un video."""
    if not GEMINI_API_KEY:
        print("[!] No se encontro GEMINI_API_KEY en .env - usando analisis simulado")
        return None
    
    try:
        from google import genai
        
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = f"""Eres un asistente experto en eventos de Medellin, Colombia. 
Analiza la siguiente descripcion de un video de TikTok y extrae informacion de eventos.

Titulo/Descripcion del video: "{text}"
Autor: @{author}

Responde UNICAMENTE con un JSON valido (sin markdown, sin comentarios) con esta estructura exacta:
{{
    "title": "Nombre corto y atractivo del evento o lugar (maximo 40 caracteres)",
    "type": "music" o "art" o "food" (elige la categoria mas apropiada),
    "price": "Precio estimado en COP o 'Gratis' si parece gratuito",
    "date": "Fecha/hora si se menciona, o 'Consultar en video' si no es clara",
    "location": "Direccion o barrio en Medellin si se menciona, o 'Medellin, Antioquia'",
    "lat": numero decimal de latitud en Medellin (entre 6.15 y 6.35),
    "lng": numero decimal de longitud en Medellin (entre -75.65 y -75.50),
    "description": "Descripcion atractiva de 1-2 lineas para el evento"
}}

Si no puedes determinar un campo con certeza, usa valores razonables para Medellin.
La latitud debe estar entre 6.15 y 6.35, la longitud entre -75.65 y -75.50."""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        # Limpiar la respuesta de posibles bloques de codigo markdown
        raw = response.text.strip()
        raw = re.sub(r'^```json\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw)
        
        parsed = json.loads(raw)
        print(f"[+] Gemini AI respondio exitosamente: {parsed['title']}")
        return parsed
        
    except json.JSONDecodeError as e:
        print(f"[!] Gemini devolvio un JSON invalido: {e}")
        print(f"    Respuesta cruda: {raw[:200]}")
        return None
    except Exception as e:
        print(f"[!] Error conectando con Gemini AI: {e}")
        return None


# ============================================================
# EXTRACCION DE METADATOS DE TIKTOK
# ============================================================
def get_tiktok_metadata(url):
    """Extrae metadatos de un video de TikTok usando multiples estrategias."""
    print(f"[*] Analizando URL: {url}")
    
    # Estrategia 1: oEmbed API oficial
    try:
        encoded_url = requests.utils.quote(url)
        res = requests.get(f"https://www.tiktok.com/oembed?url={encoded_url}", timeout=10)
        if res.status_code == 200:
            data = res.json()
            print("[+] Exito via oEmbed API")
            return {
                "success": True,
                "title": data.get("title", "Evento Desconocido"),
                "author": data.get("author_name", "Organizador"),
                "thumbnail": data.get("thumbnail_url", ""),
                "embedUrl": url 
            }
    except Exception:
        pass
    
    # Estrategia 2: Scraping de meta-tags HTML
    print("[*] oEmbed fallido, intentando scraping de meta-tags...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        res = requests.get(url, headers=headers, timeout=15)
        html = res.text
        
        title_match = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]*)"', html)
        image_match = re.search(r'<meta[^>]*property="og:image"[^>]*content="([^"]*)"', html)
        author_match = re.search(r'<meta[^>]*name="author"[^>]*content="([^"]*)"', html)
        
        title = title_match.group(1) if title_match else "Evento TikTok Descubierto"
        image = image_match.group(1) if image_match else ""
        author = author_match.group(1) if author_match else "TikTok Creator"
        
        if title != "Evento TikTok Descubierto" or image:
            print("[+] Exito via meta-tags HTML")
            return {"success": True, "title": title, "author": author, "thumbnail": image, "embedUrl": url}
    except Exception:
        pass
    
    # Estrategia 3: Datos minimos desde la URL
    print("[*] Fallback: extrayendo datos minimos de la URL")
    video_id = url.split('/')[-1].split('?')[0]
    username = re.search(r'@([^/]+)', url)
    author_name = username.group(1) if username else "desconocido"
    
    return {
        "success": True,
        "title": f"Video de @{author_name} (ID: {video_id[:8]})",
        "author": author_name,
        "thumbnail": "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80",
        "embedUrl": url
    }


# ============================================================
# PROCESAMIENTO DE EVENTO CON IA
# ============================================================
def process_event(metadata, original_url):
    """Procesa metadatos extraidos usando Gemini AI o logica simulada."""
    video_id = original_url.split('/')[-1].split('?')[0]
    
    # Intentar analisis con Gemini AI real
    ai_result = analyze_with_gemini(metadata['title'], metadata['author'])
    
    if ai_result:
        # Usar datos de Gemini AI real
        event = {
            "title": ai_result.get('title', metadata['title'][:40]),
            "type": ai_result.get('type', 'art'),
            "source": "tiktok",
            "sourceName": "@" + metadata['author'].replace(" ", ""),
            "price": ai_result.get('price', '$0 - Consultar'),
            "trending": True,
            "date": ai_result.get('date', 'Consultar en video'),
            "location": ai_result.get('location', 'Medellin, Antioquia'),
            "lat": float(ai_result.get('lat', 6.2442)),
            "lng": float(ai_result.get('lng', -75.5812)),
            "image": metadata['thumbnail'] or "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80",
            "desc": f"[IA Gemini] {ai_result.get('description', metadata['title'])}",
            "embedUrl": f"https://www.tiktok.com/embed/v2/{video_id}" if video_id.isdigit() else original_url
        }
    else:
        # Fallback: logica simulada (sin API key o si Gemini falla)
        raw_title = metadata['title'].lower()
        event = {
            "title": metadata['title'][:40] + ("..." if len(metadata['title']) > 40 else ""),
            "type": "food" if any(w in raw_title for w in ["comida","restaurante","pizza","comer","gastronomia"]) 
                    else ("music" if any(w in raw_title for w in ["fiesta","concierto","dj","musica","reggaeton"]) 
                    else "art"),
            "source": "tiktok",
            "sourceName": "@" + metadata['author'].replace(" ", ""),
            "price": "$0 - Consultar",
            "trending": True,
            "date": "Por definir (Ver Video)",
            "location": "Medellin, Antioquia",
            "lat": 6.2442 + random.uniform(-0.02, 0.02),
            "lng": -75.5812 + random.uniform(-0.02, 0.02),
            "image": metadata['thumbnail'] or "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=600&q=80",
            "desc": f"[Bot V2] Descubierto: {metadata['title']}. Requiere verificacion.",
            "embedUrl": f"https://www.tiktok.com/embed/v2/{video_id}" if video_id.isdigit() else original_url
        }
    
    return event


# ============================================================
# INYECCION A BASE DE DATOS
# ============================================================
def inject_to_database(event_data):
    """Inserta un evento procesado en la base de datos SQLite."""
    print("[*] Inyectando evento a la Base de Datos bajo estado [PENDING]...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    try:
        internal_id = f"ai-{event_data['sourceName']}-{str(event_data['lat'])[-4:]}"
        
        # Verificar que no sea duplicado
        c.execute("SELECT COUNT(*) FROM events WHERE internal_id=?", (internal_id,))
        if c.fetchone()[0] > 0:
            print(f"[!] Evento duplicado detectado ({internal_id}), saltando...")
            conn.close()
            return False
        
        for lang in ['en', 'es']:
            c.execute('''INSERT INTO events 
                (internal_id, title, type, source, sourceName, price, trending, date, location, lat, lng, image, desc, embedUrl, lang, status, organizer_id) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)''', 
                (internal_id, event_data['title'], event_data['type'], event_data['source'], 
                 event_data['sourceName'], event_data['price'], event_data['trending'], 
                 event_data['date'], event_data['location'], event_data['lat'], event_data['lng'], 
                 event_data['image'], event_data['desc'], event_data['embedUrl'], lang, 0))

        conn.commit()
        print(f"[OK] Evento '{event_data['title']}' inyectado exitosamente!")
        conn.close()
        return True
    except Exception as e:
        print(f"[ERROR] Fallo inyectando a la DB: {e}")
        conn.close()
        return False


# ============================================================
# RASTREO AUTOMATICO DE CUENTAS
# ============================================================
def scan_tracked_accounts():
    """Busca videos recientes de las cuentas rastreadas usando oEmbed."""
    print(f"\n{'='*60}")
    print(f"  RASTREO AUTOMATICO - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Rastreando {len(TRACKED_ACCOUNTS)} cuentas...")
    print(f"{'='*60}\n")
    
    total_found = 0
    
    for account in TRACKED_ACCOUNTS:
        print(f"\n--- Rastreando @{account} ---")
        
        # Construir URL del perfil (TikTok no tiene API publica de listado,
        # pero podemos intentar obtener la pagina de perfil)
        profile_url = f"https://www.tiktok.com/@{account}"
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            res = requests.get(profile_url, headers=headers, timeout=15)
            html = res.text
            
            # Buscar IDs de videos en el HTML del perfil
            video_ids = re.findall(r'/video/(\d{15,25})', html)
            unique_ids = list(set(video_ids))[:5]  # Maximo 5 videos por cuenta por rastreo
            
            if not unique_ids:
                print(f"  [!] No se encontraron videos para @{account}")
                continue
                
            print(f"  [+] Encontrados {len(unique_ids)} videos")
            
            for vid_id in unique_ids:
                video_url = f"https://www.tiktok.com/@{account}/video/{vid_id}"
                
                # Verificar si ya existe en la DB
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM events WHERE embedUrl LIKE ?", (f"%{vid_id}%",))
                exists = c.fetchone()[0] > 0
                conn.close()
                
                if exists:
                    print(f"  [=] Video {vid_id[:10]}... ya procesado, saltando")
                    continue
                
                # Procesar video nuevo
                print(f"  [*] Nuevo video detectado: {vid_id[:10]}...")
                metadata = get_tiktok_metadata(video_url)
                
                if metadata['success']:
                    event = process_event(metadata, video_url)
                    if inject_to_database(event):
                        total_found += 1
                
                # Polite delay entre requests para no ser bloqueado
                time.sleep(2)
                
        except Exception as e:
            print(f"  [ERROR] Error rastreando @{account}: {e}")
        
        # Delay entre cuentas
        time.sleep(3)
    
    print(f"\n{'='*60}")
    print(f"  RASTREO COMPLETADO: {total_found} eventos nuevos descubiertos")
    print(f"  Proximo rastreo en {SCAN_INTERVAL // 3600} horas...")
    print(f"{'='*60}\n")
    
    return total_found


# ============================================================
# MAIN: Punto de entrada
# ============================================================
if __name__ == "__main__":
    print("\n" + "="*60)
    print("  URBAN DISCOVERY - AI EVENT BOT V2")
    print("  Powered by Google Gemini AI")
    print("="*60)
    
    # Verificar Gemini API Key
    if GEMINI_API_KEY:
        print(f"  [OK] Gemini API Key configurada: {GEMINI_API_KEY[:10]}...")
    else:
        print("  [!] Sin API Key de Gemini (usando analisis simulado)")
    
    print(f"  [OK] Base de datos: {DB_PATH}")
    print(f"  [OK] Cuentas rastreadas: {len(TRACKED_ACCOUNTS)}")
    print("="*60 + "\n")
    
    # Modo 1: URL manual
    if len(sys.argv) >= 2 and sys.argv[1] != '--auto':
        url = sys.argv[1]
        if "tiktok.com" not in url.lower():
            print("[!] Solo se soportan URLs de TikTok por ahora.")
            sys.exit(1)
        
        metadata = get_tiktok_metadata(url)
        if metadata['success']:
            event = process_event(metadata, url)
            inject_to_database(event)
            print("\n[*] Entra como admin en la web para aprobarlo!")
        else:
            print("[ERROR] No se pudo procesar la URL")
    
    # Modo 2: Automatico (bucle infinito cada 6 horas)
    elif len(sys.argv) >= 2 and sys.argv[1] == '--auto':
        print("[AUTO] Modo automatico activado!")
        print(f"[AUTO] Rastreando cada {SCAN_INTERVAL // 3600} horas")
        print("[AUTO] Presiona Ctrl+C para detener\n")
        
        try:
            while True:
                scan_tracked_accounts()
                print(f"[AUTO] Durmiendo {SCAN_INTERVAL // 3600} horas hasta el proximo rastreo...")
                time.sleep(SCAN_INTERVAL)
        except KeyboardInterrupt:
            print("\n[AUTO] Bot detenido por el usuario. Hasta luego!")
    
    # Sin argumentos: mostrar ayuda
    else:
        print("Modos de uso:\n")
        print("  1. MANUAL - Procesar un video especifico:")
        print('     python ai_event_bot.py "https://tiktok.com/@usuario/video/123"')
        print("")
        print("  2. AUTOMATICO - Rastrear cuentas cada 6 horas:")
        print("     python ai_event_bot.py --auto")
        print("")
        print("Cuentas configuradas para rastreo automatico:")
        for acc in TRACKED_ACCOUNTS:
            print(f"    - @{acc}")
