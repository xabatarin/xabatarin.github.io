from flask import Flask, redirect, request, session, url_for, render_template_string
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import MemoryCacheHandler
import secrets
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(16))

# Configuración para producción
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET') 
REDIRECT_URI = os.getenv('REDIRECT_URI')
SCOPE = 'user-top-read playlist-modify-public'

# Verificar que las credenciales estén configuradas
if not all([CLIENT_ID, CLIENT_SECRET, REDIRECT_URI]):
    raise ValueError("Faltan las credenciales de Spotify. Configura las variables de entorno.")

def get_spotify_oauth():
    # Crear un cache único por usuario usando MemoryCacheHandler
    cache_handler = MemoryCacheHandler()
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_handler=cache_handler,
        show_dialog=True  # Forzar que siempre muestre el diálogo de login
    )

def get_token():
    token_info = session.get('token_info', None)
    if not token_info:
        return None
    
    sp_oauth = get_spotify_oauth()
    
    # Verificar si el token necesita renovación
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = token_info
    
    return token_info

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Emo2Music - Spotify Top Tracks</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                text-align: center; 
                padding: 20px; 
                background: linear-gradient(135deg, #1DB954, #191414);
                color: white;
                min-height: 100vh;
                margin: 0;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                background: rgba(0,0,0,0.3);
                padding: 50px;
                border-radius: 20px;
                max-width: 600px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            }
            .button {
                background-color: #1DB954;
                color: white;
                padding: 18px 40px;
                border: none;
                border-radius: 30px;
                font-size: 18px;
                font-weight: bold;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin-top: 30px;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(29, 185, 84, 0.3);
            }
            .button:hover { 
                background-color: #1ed760; 
                transform: translateY(-3px);
                box-shadow: 0 6px 20px rgba(29, 185, 84, 0.4);
            }
            h1 {
                font-size: 2.5em;
                margin-bottom: 20px;
                color: #1DB954;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
            }
            p {
                font-size: 1.2em;
                line-height: 1.6;
                opacity: 0.9;
                margin-bottom: 20px;
            }
            .features {
                display: flex;
                justify-content: space-around;
                margin: 30px 0;
                flex-wrap: wrap;
            }
            .feature {
                background: rgba(255,255,255,0.1);
                padding: 20px;
                border-radius: 10px;
                margin: 10px;
                flex: 1;
                min-width: 150px;
            }
            .feature h3 {
                color: #1DB954;
                margin-bottom: 10px;
            }
            @media (max-width: 768px) {
                .container {
                    padding: 30px 20px;
                    margin: 20px;
                }
                h1 {
                    font-size: 2em;
                }
                .features {
                    flex-direction: column;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎵 Emo2Music</h1>
            <p>Descubre tus artistas y canciones más escuchadas de Spotify</p>
            
            <div class="features">
                <div class="feature">
                    <h3>🎤 Artistas Top</h3>
                    <p>Ve tus artistas favoritos</p>
                </div>
                <div class="feature">
                    <h3>🎵 Canciones Top</h3>
                    <p>Descubre tus hits personales</p>
                </div>
                <div class="feature">
                    <h3>📊 Estadísticas</h3>
                    <p>Datos detallados de tu música</p>
                </div>
            </div>
            
            <p>Conecta tu cuenta de Spotify y explora tu música como nunca antes.</p>
            <a class="button" href="/login">🚀 Iniciar sesión con Spotify</a>
            
            <div style="margin-top: 40px; font-size: 0.9em; opacity: 0.7;">
                <p>✨ Cada usuario ve sus propios datos ✨</p>
                <p>📝 Aplicación en modo desarrollo - Solo usuarios autorizados</p>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/login')
def login():
    try:
        # Limpiar cualquier sesión anterior
        session.clear()
        
        sp_oauth = get_spotify_oauth()
        auth_url = sp_oauth.get_authorize_url()
        print(f"Redirigiendo a: {auth_url}")  # Para debugging
        return redirect(auth_url)
    except Exception as e:
        return f"Error al iniciar sesión: {str(e)}"


@app.route('/callback')
def callback():
    try:
        sp_oauth = get_spotify_oauth()
        session.clear()  # Limpiar sesión anterior
        
        code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            if error == 'access_denied':
                return '''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Acceso denegado</title>
                    <meta charset="UTF-8">
                    <style>
                        body { 
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                            text-align: center; 
                            padding: 40px; 
                            background: linear-gradient(135deg, #1DB954, #191414);
                            color: white;
                            min-height: 100vh;
                            margin: 0;
                        }
                        .container {
                            background: rgba(0,0,0,0.3);
                            padding: 40px;
                            border-radius: 15px;
                            max-width: 600px;
                            margin: 0 auto;
                            backdrop-filter: blur(10px);
                        }
                        .button {
                            background-color: #1DB954;
                            color: white;
                            padding: 15px 30px;
                            border: none;
                            border-radius: 25px;
                            font-size: 16px;
                            cursor: pointer;
                            text-decoration: none;
                            display: inline-block;
                            margin-top: 20px;
                            transition: all 0.3s ease;
                        }
                        .button:hover { 
                            background-color: #1ed760; 
                        }
                        h1 {
                            color: #e22134;
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🚫 Acceso no autorizado</h1>
                        <p><strong>Esta aplicación está en modo desarrollo.</strong></p>
                        <p>Solo usuarios autorizados pueden acceder actualmente.</p>
                        <p>Si quieres probar la aplicación, contacta al desarrollador para ser agregado a la lista de usuarios permitidos.</p>
                        <a class="button" href="/">← Volver al inicio</a>
                    </div>
                </body>
                </html>
                '''
        
        if not code:
            return "Error: No se recibió código de autorización"
            
        token_info = sp_oauth.get_access_token(code)
        if not token_info:
            return "Error: No se pudo obtener el token de acceso"
            
        # Guardar token en la sesión del usuario específico
        session['token_info'] = token_info
        session['user_authenticated'] = True
        
        return redirect(url_for('dashboard'))
    except Exception as e:
        error_msg = str(e)
        if "invalid_client" in error_msg.lower() or "unauthorized" in error_msg.lower():
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Usuario no autorizado</title>
                <meta charset="UTF-8">
                <style>
                    body { 
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                        text-align: center; 
                        padding: 40px; 
                        background: linear-gradient(135deg, #1DB954, #191414);
                        color: white;
                        min-height: 100vh;
                        margin: 0;
                    }
                    .container {
                        background: rgba(0,0,0,0.3);
                        padding: 40px;
                        border-radius: 15px;
                        max-width: 600px;
                        margin: 0 auto;
                        backdrop-filter: blur(10px);
                    }
                    .button {
                        background-color: #1DB954;
                        color: white;
                        padding: 15px 30px;
                        border: none;
                        border-radius: 25px;
                        text-decoration: none;
                        display: inline-block;
                        margin-top: 20px;
                    }
                    .button:hover { background-color: #1ed760; }
                    h1 { color: #e22134; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🚫 Aplicación en modo desarrollo</h1>
                    <p>Esta aplicación de Spotify está actualmente en modo desarrollo.</p>
                    <p>Solo usuarios específicamente autorizados pueden acceder.</p>
                    <p><strong>¿Quieres probar la app?</strong><br>
                    Contacta al desarrollador para ser agregado a la lista de usuarios permitidos.</p>
                    <a class="button" href="/">← Volver al inicio</a>
                </div>
            </body>
            </html>
            '''
        return f"Error en callback: {str(e)}"

@app.route('/dashboard')
def dashboard():
    try:
        token_info = get_token()
        if not token_info:
            return redirect(url_for('login'))
        
        sp = spotipy.Spotify(auth=token_info['access_token'])
        user_info = sp.current_user()
        
        # Debug: Mostrar qué usuario está logueado
        print(f"Usuario logueado: {user_info['display_name']} (ID: {user_info['id']})")
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dashboard - {user_info['display_name']}</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    text-align: center; 
                    padding: 20px; 
                    background: linear-gradient(135deg, #1DB954, #191414);
                    color: white;
                    min-height: 100vh;
                    margin: 0;
                }}
                .container {{
                    background: rgba(0,0,0,0.3);
                    padding: 40px;
                    border-radius: 15px;
                    max-width: 800px;
                    margin: 0 auto;
                    backdrop-filter: blur(10px);
                }}
                .user-info {{
                    background: rgba(255,255,255,0.1);
                    padding: 20px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                }}
                .button {{
                    background-color: #1DB954;
                    color: white;
                    padding: 15px 30px;
                    border: none;
                    border-radius: 25px;
                    font-size: 16px;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                    margin: 10px;
                    transition: all 0.3s ease;
                }}
                .button:hover {{ 
                    background-color: #1ed760; 
                    transform: translateY(-2px);
                }}
                .logout {{ 
                    background-color: #e22134; 
                }}
                .logout:hover {{ 
                    background-color: #ff4757; 
                }}
                h1 {{ 
                    color: #1DB954; 
                    margin-bottom: 20px;
                }}
                h2 {{
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="user-info">
                    <h2>¡Hola, {user_info['display_name']}! 👋</h2>
                    <p><strong>ID de usuario:</strong> {user_info['id']}</p>
                    <p><strong>Seguidores:</strong> {user_info['followers']['total']}</p>
                </div>
                
                <h1>🎵 Tu Dashboard de Spotify</h1>
                <p>Elige qué quieres ver de tu cuenta:</p>
                
                <a class="button" href="/top-artists">🎤 Mis Artistas Top</a>
                <a class="button" href="/top-tracks">🎵 Mis Canciones Top</a>
                <a class="button" href="/crear-playlist">🪄 Crear Playlist por Estado de Ánimo</a>
                <br>
                <a class="button logout" href="/logout">🚪 Cerrar sesión</a>
            </div>
        </body>
        </html>
        '''
        return html
        
    except Exception as e:
        session.clear()  # Limpiar sesión en caso de error
        return f"Error: {str(e)} - <a href='/'>Volver al inicio</a>"

@app.route('/logout')
def logout():
    session.clear()  # Limpiar toda la sesión
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sesión cerrada</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                text-align: center; 
                padding: 40px; 
                background: linear-gradient(135deg, #1DB954, #191414);
                color: white;
                min-height: 100vh;
                margin: 0;
            }
            .container {
                background: rgba(0,0,0,0.3);
                padding: 40px;
                border-radius: 15px;
                max-width: 500px;
                margin: 0 auto;
                backdrop-filter: blur(10px);
            }
            .button {
                background-color: #1DB954;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 25px;
                font-size: 16px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin-top: 20px;
                transition: all 0.3s ease;
            }
            .button:hover { 
                background-color: #1ed760; 
                transform: translateY(-2px);
            }
            h1 {
                color: #1DB954;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>✅ Sesión cerrada exitosamente</h1>
            <p>Has cerrado sesión de Spotify correctamente.</p>
            <p>Ahora otros usuarios pueden iniciar sesión con sus propias cuentas.</p>
            <a class="button" href="/">🎵 Volver al inicio</a>
        </div>
    </body>
    </html>
    '''

@app.route('/top-artists')
def get_top_artists():
    try:
        token_info = get_token()
        if not token_info:
            return redirect(url_for('login'))
        
        sp = spotipy.Spotify(auth=token_info['access_token'])
        user_info = sp.current_user()
        
        # Debug: Verificar usuario
        print(f"Obteniendo artistas para: {user_info['display_name']} (ID: {user_info['id']})")
        
        top_artists = sp.current_user_top_artists(limit=20, time_range='short_term')
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Top Artistas - {user_info['display_name']}</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    padding: 20px; 
                    background: linear-gradient(135deg, #1DB954, #191414);
                    color: white;
                    min-height: 100vh;
                    margin: 0;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: rgba(0,0,0,0.3);
                    padding: 30px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }}
                .user-header {{
                    text-align: center;
                    margin-bottom: 30px;
                    background: rgba(255,255,255,0.1);
                    padding: 15px;
                    border-radius: 10px;
                }}
                .artist {{
                    background: rgba(255,255,255,0.1);
                    margin: 10px 0;
                    padding: 15px;
                    border-radius: 10px;
                    display: flex;
                    align-items: center;
                    transition: all 0.3s ease;
                }}
                .artist:hover {{
                    background: rgba(255,255,255,0.2);
                    transform: translateX(5px);
                }}
                .rank {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-right: 20px;
                    color: #1DB954;
                    min-width: 40px;
                }}
                .artist-info h3 {{
                    margin: 0 0 5px 0;
                    color: white;
                }}
                .artist-info p {{
                    margin: 0;
                    opacity: 0.8;
                    font-size: 14px;
                }}
                .button {{
                    background-color: #1DB954;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 20px;
                    text-decoration: none;
                    display: inline-block;
                    margin: 5px;
                    transition: all 0.3s ease;
                }}
                .button:hover {{ 
                    background-color: #1ed760; 
                    transform: translateY(-2px);
                }}
                .button-nav {{
                    text-align: center; 
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="user-header">
                    <h2>🎤 Top Artistas de {user_info['display_name']}</h2>
                    <p><strong>ID:</strong> {user_info['id']}</p>
                    <p>Basado en tus últimas 4 semanas de escucha</p>
                </div>
        '''
        
        for i, artist in enumerate(top_artists['items'], 1):
            genres = ', '.join(artist['genres'][:3]) if artist['genres'] else 'Sin género'
            html += f'''
                <div class="artist">
                    <div class="rank">#{i}</div>
                    <div class="artist-info">
                        <h3>{artist['name']}</h3>
                        <p><strong>Géneros:</strong> {genres}</p>
                        <p><strong>Popularidad:</strong> {artist['popularity']}/100</p>
                    </div>
                </div>
            '''
        
        html += '''
                <div class="button-nav">
                    <a class="button" href="/dashboard">🏠 Dashboard</a>
                    <a class="button" href="/top-tracks">🎵 Ver Canciones Top</a>
                    <a class="button" href="/logout">🚪 Cerrar sesión</a>
                </div>
            </div>
        </body>
        </html>
        '''
        return html
        
    except Exception as e:
        return f"Error obteniendo artistas: {str(e)} - <a href='/dashboard'>Volver</a>"

@app.route('/top-tracks')
def get_top_tracks():
    try:
        token_info = get_token()
        if not token_info:
            return redirect(url_for('login'))
        
        sp = spotipy.Spotify(auth=token_info['access_token'])
        user_info = sp.current_user()
        
        # Debug: Verificar usuario
        print(f"Obteniendo tracks para: {user_info['display_name']} (ID: {user_info['id']})")
        
        top_tracks = sp.current_user_top_tracks(limit=20, time_range='short_term')
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Top Canciones - {user_info['display_name']}</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    padding: 20px; 
                    background: linear-gradient(135deg, #1DB954, #191414);
                    color: white;
                    min-height: 100vh;
                    margin: 0;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    background: rgba(0,0,0,0.3);
                    padding: 30px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }}
                .user-header {{
                    text-align: center;
                    margin-bottom: 30px;
                    background: rgba(255,255,255,0.1);
                    padding: 15px;
                    border-radius: 10px;
                }}
                .track {{
                    background: rgba(255,255,255,0.1);
                    margin: 10px 0;
                    padding: 15px;
                    border-radius: 10px;
                    display: flex;
                    align-items: center;
                    transition: all 0.3s ease;
                }}
                .track:hover {{
                    background: rgba(255,255,255,0.2);
                    transform: translateX(5px);
                }}
                .rank {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-right: 20px;
                    color: #1DB954;
                    min-width: 40px;
                }}
                .track-info h3 {{
                    margin: 0 0 5px 0;
                    color: white;
                }}
                .track-info p {{
                    margin: 0;
                    opacity: 0.8;
                    font-size: 14px;
                }}
                .button {{
                    background-color: #1DB954;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 20px;
                    text-decoration: none;
                    display: inline-block;
                    margin: 5px;
                    transition: all 0.3s ease;
                }}
                .button:hover {{ 
                    background-color: #1ed760; 
                    transform: translateY(-2px);
                }}
                .button-nav {{
                    text-align: center; 
                    margin-top: 30px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="user-header">
                    <h2>🎵 Top Canciones de {user_info['display_name']}</h2>
                    <p><strong>ID:</strong> {user_info['id']}</p>
                    <p>Basado en tus últimas 4 semanas de escucha</p>
                </div>
        '''
        
        for i, track in enumerate(top_tracks['items'], 1):
            artists = ', '.join([artist['name'] for artist in track['artists']])
            duration_ms = track['duration_ms']
            duration_min = duration_ms // 60000
            duration_sec = (duration_ms % 60000) // 1000
            
            html += f'''
                <div class="track">
                    <div class="rank">#{i}</div>
                    <div class="track-info">
                        <h3>{track['name']}</h3>
                        <p><strong>Artista:</strong> {artists}</p>
                        <p><strong>Álbum:</strong> {track['album']['name']}</p>
                        <p><strong>Duración:</strong> {duration_min}:{duration_sec:02d} | <strong>Popularidad:</strong> {track['popularity']}/100</p>
                    </div>
                </div>
            '''
        
        html += '''
                <div class="button-nav">
                    <a class="button" href="/dashboard">🏠 Dashboard</a>
                    <a class="button" href="/top-artists">🎤 Ver Artistas Top</a>
                    <a class="button" href="/logout">🚪 Cerrar sesión</a>
                </div>
            </div>
        </body>
        </html>
        '''
        return html
        
    except Exception as e:
        return f"Error obteniendo tracks: {str(e)} - <a href='/dashboard'>Volver</a>"

@app.route('/crear-playlist', methods=['GET', 'POST'])
def crear_playlist():
    try:
        token_info = get_token()
        if not token_info:
            return redirect(url_for('login'))
        sp = spotipy.Spotify(auth=token_info['access_token'])
        user_info = sp.current_user()

        if request.method == 'POST':
            mood = request.form.get('mood')
            if mood not in ['feliz', 'triste', 'enfadado']:
                return 'Estado de ánimo no válido', 400

            # Obtener top artistas y top tracks
            top_artists = sp.current_user_top_artists(limit=5, time_range='short_term')
            top_tracks = sp.current_user_top_tracks(limit=10, time_range='short_term')

            artist_ids = [artist['id'] for artist in top_artists['items']]
            # Buscar canciones populares de los artistas favoritos
            artist_tracks = []
            for artist_id in artist_ids:
                tracks = sp.artist_top_tracks(artist_id, country='ES')['tracks']
                artist_tracks.extend(tracks[:2])  # 2 canciones por artista

            # Filtrar canciones según el estado de ánimo
            def filtrar_por_mood(tracks, mood):
                if mood == 'feliz':
                    return [t for t in tracks if t['energy'] > 0.6 and t['valence'] > 0.6]
                elif mood == 'triste':
                    return [t for t in tracks if t['valence'] < 0.4 and t['energy'] < 0.6]
                elif mood == 'enfadado':
                    return [t for t in tracks if t['energy'] < 0.5 and t['valence'] > 0.5]
                return tracks

            # Obtener audio features para filtrar
            all_tracks = artist_tracks + top_tracks['items']
            all_tracks = [t for t in all_tracks if t.get('id')]  # Solo tracks con id válido
            all_tracks = all_tracks[:30]  # Limitar para no exceder peticiones
            track_ids = [t['id'] for t in all_tracks]
            features = sp.audio_features(track_ids)
            tracks_with_features = []
            for t, f in zip(all_tracks, features):
                if f and f['energy'] is not None and f['valence'] is not None:
                    t['energy'] = f['energy']
                    t['valence'] = f['valence']
                    tracks_with_features.append(t)
            # Filtrar por mood
            filtered_tracks = filtrar_por_mood(tracks_with_features, mood)
            # Añadir canciones favoritas si no hay suficientes
            if len(filtered_tracks) < 18:
                extra = [t for t in tracks_with_features if t not in filtered_tracks]
                filtered_tracks += extra
            # Limitar a 18 canciones
            filtered_tracks = filtered_tracks[:18]
            uris = [t['uri'] for t in filtered_tracks]

            # Crear la playlist
            nombre = f"Playlist {'Feliz' if mood=='feliz' else 'Triste' if mood=='triste' else 'Relajada'} - Emo2Music"
            descripcion = f"Playlist generada automáticamente según tu estado de ánimo: {mood}"
            playlist = sp.user_playlist_create(user_info['id'], nombre, public=True, description=descripcion)
            sp.playlist_add_items(playlist['id'], uris)

            return f"<h2>✅ Playlist '{nombre}' creada con éxito!</h2><a href='{playlist['external_urls']['spotify']}' target='_blank'>Ver en Spotify</a><br><a href='/dashboard'>Volver al dashboard</a>"

        # GET: mostrar formulario
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Crear Playlist por Estado de Ánimo</title>
            <meta charset="UTF-8">
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #1DB954, #191414); color: white; min-height: 100vh; text-align: center; }
                .container { background: rgba(0,0,0,0.3); padding: 40px; border-radius: 15px; max-width: 500px; margin: 40px auto; }
                select, button { padding: 12px 20px; border-radius: 20px; border: none; font-size: 1.1em; margin: 10px; }
                button { background: #1DB954; color: white; font-weight: bold; cursor: pointer; transition: all 0.3s; }
                button:hover { background: #1ed760; }
                h2 { color: #1DB954; }
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Crear Playlist según tu estado de ánimo</h2>
                <form method="post">
                    <label for="mood">Selecciona tu estado de ánimo:</label><br><br>
                    <select name="mood" id="mood" required>
                        <option value="feliz">😊 Feliz</option>
                        <option value="triste">😢 Triste</option>
                        <option value="enfadado">😡 Enfadado</option>
                    </select><br><br>
                    <button type="submit">Crear Playlist</button>
                </form>
                <br><a href="/dashboard" style="color:#1DB954;">← Volver al dashboard</a>
            </div>
        </body>
        </html>
        '''
    except Exception as e:
        return f"Error al crear la playlist: {str(e)} <br><a href='/dashboard'>Volver</a>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))