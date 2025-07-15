from flask import Flask, redirect, request, session, url_for, render_template_string
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import MemoryCacheHandler
import secrets
import os
from dotenv import load_dotenv
import random

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

# --- Plantillas HTML y CSS ---

def get_base_css():
    """Devuelve el CSS base para todas las páginas para un diseño consistente."""
    return '''
        <style>
            body { 
                font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; 
                background-color: #121212;
                color: #FFFFFF;
                margin: 0;
                padding: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: calc(100vh - 40px);
            }
            .container {
                max-width: 800px;
                width: 100%;
                margin: 20px auto;
                background-color: #181818;
                padding: 30px 40px;
                border-radius: 10px;
                box-shadow: 0 4px_20px rgba(0,0,0,0.2);
                text-align: center;
            }
            h1 {
                color: #1DB954;
                font-size: 2.2em;
                margin-bottom: 10px;
                font-weight: 700;
            }
            h2 {
                color: #FFFFFF;
                margin-bottom: 20px;
                font-weight: 600;
            }
            p {
                font-size: 1.1em;
                line-height: 1.6;
                color: #B3B3B3;
            }
            .button {
                background-color: #1DB954;
                color: #FFFFFF;
                padding: 15px 35px;
                border: none;
                border-radius: 50px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 10px 5px;
                transition: background-color 0.3s ease, transform 0.2s ease;
            }
            .button:hover { 
                background-color: #1ed760; 
                transform: scale(1.05);
            }
            .button.logout { 
                background-color: #535353; 
            }
            .button.logout:hover { 
                background-color: #737373; 
            }
            a {
                color: #1DB954;
                text-decoration: none;
            }
            a:hover {
                text-decoration: underline;
            }
            .list-item {
                background-color: #282828;
                margin: 15px 0;
                padding: 15px 20px;
                border-radius: 8px;
                display: flex;
                align-items: center;
                text-align: left;
                transition: background-color 0.3s ease;
            }
            .list-item:hover {
                background-color: #383838;
            }
            .list-item .rank {
                font-size: 20px;
                font-weight: bold;
                margin-right: 20px;
                color: #B3B3B3;
                min-width: 30px;
            }
            .list-item .info h3 {
                margin: 0 0 5px 0;
                color: #FFFFFF;
                font-size: 1.1em;
            }
            .list-item .info p {
                margin: 0;
                color: #B3B3B3;
                font-size: 0.9em;
            }
            .user-header {
                text-align: center;
                margin-bottom: 30px;
                background: #282828;
                padding: 20px;
                border-radius: 10px;
            }
            .form-container {
                margin-top: 20px;
            }
            .form-container label {
                font-size: 1.1em;
                margin-bottom: 15px;
                display: block;
            }
            .form-container select {
                background-color: #282828;
                color: white;
                padding: 12px 20px;
                border-radius: 5px;
                border: 1px solid #535353;
                font-size: 1em;
                margin: 10px;
            }
            .footer-nav {
                text-align: center; 
                margin-top: 30px;
            }
            @media (max-width: 768px) {
                body {
                    align-items: flex-start;
                }
                .container {
                    padding: 20px;
                    margin-top: 20px;
                }
                h1 {
                    font-size: 1.8em;
                }
            }
        </style>
    '''

@app.route('/')
def index():
    return f'''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <title>Emo2Music - Analiza tu Música</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {get_base_css()}
    </head>
    <body>
        <div class="container">
            <h1>Emo2Music</h1>
            <p>Conecta tu cuenta de Spotify para descubrir tus artistas y canciones más escuchadas, y crea playlists basadas en tu estado de ánimo.</p>
            <a class="button" href="/login">Iniciar Sesión con Spotify</a>
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
                return f'''
                <!DOCTYPE html>
                <html lang="es">
                <head>
                    <title>Acceso Denegado</title>
                    <meta charset="UTF-8">
                    {get_base_css()}
                </head>
                <body>
                    <div class="container">
                        <h1>Acceso Denegado</h1>
                        <p><strong>La aplicación está en modo de desarrollo.</strong></p>
                        <p>Para utilizarla, el propietario de la aplicación debe añadir tu cuenta de Spotify a la lista de usuarios autorizados.</p>
                        <a class="button" href="/">Volver al Inicio</a>
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
            return f'''
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <title>Usuario No Autorizado</title>
                <meta charset="UTF-8">
                {get_base_css()}
            </head>
            <body>
                <div class="container">
                    <h1>Aplicación en Modo Desarrollo</h1>
                    <p>Esta aplicación de Spotify se encuentra actualmente en modo de desarrollo y solo los usuarios autorizados pueden acceder.</p>
                    <p>Si deseas probar la aplicación, por favor, contacta al desarrollador.</p>
                    <a class="button" href="/">Volver al Inicio</a>
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
        <html lang="es">
        <head>
            <title>Panel de Control - {user_info['display_name']}</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {get_base_css()}
        </head>
        <body>
            <div class="container">
                <div class="user-header">
                    <h2>Bienvenido, {user_info['display_name']}</h2>
                    <p><strong>ID de Usuario:</strong> {user_info['id']} | <strong>Seguidores:</strong> {user_info['followers']['total']}</p>
                </div>
                
                <h1>Panel de Control</h1>
                <p>Selecciona una opción para explorar tu música.</p>
                
                <a class="button" href="/top-artists">Artistas Principales</a>
                <a class="button" href="/top-tracks">Canciones Principales</a>
                <a class="button" href="/crear-playlist">Crear Playlist por Ánimo</a>
                <br>
                <a class="button logout" href="/logout">Cerrar Sesión</a>
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
    return f'''
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <title>Sesión Cerrada</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {get_base_css()}
    </head>
    <body>
        <div class="container">
            <h1>Sesión Cerrada</h1>
            <p>Has cerrado sesión de tu cuenta de Spotify correctamente.</p>
            <a class="button" href="/">Volver a la página de inicio</a>
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
        <html lang="es">
        <head>
            <title>Artistas Principales - {user_info['display_name']}</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {get_base_css()}
        </head>
        <body>
            <div class="container">
                <div class="user-header">
                    <h2>Artistas Principales de {user_info['display_name']}</h2>
                    <p>Basado en tu actividad de las últimas 4 semanas.</p>
                </div>
        '''
        
        if not top_artists['items']:
            html += "<p>No se encontraron artistas principales. ¡Escucha más música!</p>"
        else:
            for i, artist in enumerate(top_artists['items'], 1):
                genres = ', '.join(artist['genres'][:3]) if artist['genres'] else 'No especificado'
                html += f'''
                    <div class="list-item">
                        <div class="rank">#{i}</div>
                        <div class="info">
                            <h3>{artist['name']}</h3>
                            <p><strong>Géneros:</strong> {genres}</p>
                            <p><strong>Popularidad:</strong> {artist['popularity']}/100</p>
                        </div>
                    </div>
                '''
        
        html += f'''
                <div class="footer-nav">
                    <a class="button" href="/dashboard">Panel de Control</a>
                    <a class="button" href="/top-tracks">Ver Canciones Principales</a>
                    <a class="button logout" href="/logout">Cerrar Sesión</a>
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
        <html lang="es">
        <head>
            <title>Canciones Principales - {user_info['display_name']}</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {get_base_css()}
        </head>
        <body>
            <div class="container">
                <div class="user-header">
                    <h2>Canciones Principales de {user_info['display_name']}</h2>
                    <p>Basado en tu actividad de las últimas 4 semanas.</p>
                </div>
        '''
        
        if not top_tracks['items']:
            html += "<p>No se encontraron canciones principales. ¡Escucha más música!</p>"
        else:
            for i, track in enumerate(top_tracks['items'], 1):
                artists = ', '.join([artist['name'] for artist in track['artists']])
                duration_ms = track['duration_ms']
                duration_min = duration_ms // 60000
                duration_sec = (duration_ms % 60000) // 1000
                
                html += f'''
                    <div class="list-item">
                        <div class="rank">#{i}</div>
                        <div class="info">
                            <h3>{track['name']}</h3>
                            <p><strong>Artista:</strong> {artists}</p>
                            <p><strong>Álbum:</strong> {track['album']['name']}</p>
                            <p><strong>Duración:</strong> {duration_min}:{duration_sec:02d} | <strong>Popularidad:</strong> {track['popularity']}/100</p>
                        </div>
                    </div>
                '''
        
        html += f'''
                <div class="footer-nav">
                    <a class="button" href="/dashboard">Panel de Control</a>
                    <a class="button" href="/top-artists">Ver Artistas Principales</a>
                    <a class="button logout" href="/logout">Cerrar Sesión</a>
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

            # Si está enfadado, redirigir a una playlist tranquila
            if mood == 'enfadado':
                # URL de una playlist de Spotify con música tranquila
                calm_playlist_url = 'https://open.spotify.com/playlist/37i9dQZF1DX8NTLI25q_x0'
                return f'''
                <!DOCTYPE html>
                <html lang="es">
                <head>
                    <title>Redirigiendo...</title>
                    <meta charset="UTF-8">
                    {get_base_css()}
                    <meta http-equiv="refresh" content="4;url={calm_playlist_url}" />
                </head>
                <body>
                    <div class="container">
                        <h1>Redirigiendo a una Playlist Tranquila</h1>
                        <p>Para ayudarte a relajar, te estamos llevando a una playlist de música tranquila en Spotify.</p>
                        <p>Si no eres redirigido, <a href="{calm_playlist_url}" target="_blank">haz clic aquí</a>.</p>
                    </div>
                </body>
                </html>
                '''

            # --- Lógica para Feliz y Triste ---
            
            # 1. Obtener canciones base
            top_artists = sp.current_user_top_artists(limit=10, time_range='long_term')
            top_tracks = sp.current_user_top_tracks(limit=30, time_range='short_term')

            # Diccionario para evitar duplicados usando el ID de la canción como clave
            all_tracks = {}

            # Añadir las 30 canciones más escuchadas del usuario
            for track in top_tracks['items']:
                if track and track.get('id'):
                    all_tracks[track['id']] = track
            
            # Añadir hasta 5 canciones de los 10 artistas favoritos
            for artist in top_artists['items']:
                try:
                    # Usamos 'ES' como mercado para obtener resultados relevantes
                    artist_tracks = sp.artist_top_tracks(artist['id'], country='ES')['tracks']
                    for track in artist_tracks[:5]:
                        if track and track.get('id') and track['id'] not in all_tracks:
                            all_tracks[track['id']] = track
                except Exception:
                    continue # Si un artista no tiene canciones o falla, continuamos

            # Convertir el diccionario de canciones únicas a una lista
            track_pool = list(all_tracks.values())
            
            if len(track_pool) < 18:
                 return "<h2>No tienes suficientes canciones para crear una playlist. ¡Escucha más música!</h2><a href='/dashboard'>Volver</a>"

            uris = []
            nombre = ""
            
            if mood == 'triste':
                nombre = "Playlist para un día triste - Emo2Music"
                # Elegir 18 canciones aleatorias de la lista de favoritas
                final_tracks = random.sample(track_pool, 18)
                uris = [t['uri'] for t in final_tracks]

            elif mood == 'feliz':
                nombre = "Playlist para un día feliz - Emo2Music"
                # Elegir 10 canciones aleatorias de la lista de favoritas
                base_tracks = random.sample(track_pool, 10)
                uris = [t['uri'] for t in base_tracks]
                
                # Obtener 8 recomendaciones basadas en las canciones elegidas
                seed_track_ids = [t['id'] for t in base_tracks[:5]] # Usar 5 como semilla
                try:
                    recommendations = sp.recommendations(seed_tracks=seed_track_ids, limit=8)
                    uris.extend([t['uri'] for t in recommendations['tracks']])
                except Exception as e:
                    print(f"Error obteniendo recomendaciones: {e}")
                    # Si falla la recomendación, rellenar con más canciones aleatorias de la lista
                    remaining_needed = 18 - len(uris)
                    if remaining_needed > 0:
                        # Asegurarse de no añadir canciones que ya están
                        extra_pool = [t for t in track_pool if t['uri'] not in uris]
                        uris.extend([t['uri'] for t in random.sample(extra_pool, min(remaining_needed, len(extra_pool)))])
            
            # Crear la playlist en Spotify
            descripcion = f"Playlist generada automáticamente por Emo2Music para un día {mood}."
            playlist = sp.user_playlist_create(user_info['id'], nombre, public=True, description=descripcion)
            
            # Añadir las canciones a la playlist
            sp.playlist_add_items(playlist['id'], uris)

            return f'''
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <title>Playlist Creada</title>
                <meta charset="UTF-8">
                {get_base_css()}
            </head>
            <body>
                <div class="container">
                    <h1>Playlist Creada con Éxito</h1>
                    <p>Tu playlist "{nombre}" está lista.</p>
                    <a class="button" href="{playlist['external_urls']['spotify']}" target="_blank">Abrir en Spotify</a>
                    <a class="button" href="/dashboard">Volver al Panel de Control</a>
                </div>
            </body>
            </html>
            '''

        # GET: si no es POST, mostrar el formulario
        return f'''
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <title>Crear Playlist por Estado de Ánimo</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {get_base_css()}
        </head>
        <body>
            <div class="container">
                <h2>Crear Playlist por Estado de Ánimo</h2>
                <form method="post" class="form-container">
                    <label for="mood">Selecciona tu estado de ánimo actual:</label>
                    <select name="mood" id="mood" required>
                        <option value="feliz">Feliz</option>
                        <option value="triste">Triste</option>
                        <option value="enfadado">Enfadado</option>
                    </select>
                    <br><br>
                    <button class="button" type="submit">Crear Playlist</button>
                </form>
                <div class="footer-nav">
                    <a href="/dashboard">Volver al Panel de Control</a>
                </div>
            </div>
        </body>
        </html>
        '''
    except Exception as e:
        return f"Error al crear la playlist: {str(e)} <br><a href='/dashboard'>Volver</a>"

if __name__ == '__main__':
    app.run(debug=True)