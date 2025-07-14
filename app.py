from flask import Flask, redirect, request, session, url_for, render_template_string
import spotipy
from spotipy.oauth2 import SpotifyOAuth
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

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Spotify Top Tracks</title>
        <style>
            body { font-family: Arial; text-align: center; padding: 40px; }
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
            }
            .button:hover { background-color: #1ed760; }
        </style>
    </head>
    <body>
        <h1>🎵 Ver tus artistas top de Spotify</h1>
        <p>Haz clic en el botón para iniciar sesión con tu cuenta de Spotify y ver tus artistas y canciones más escuchadas.</p>
        <a class="button" href="/login">Iniciar sesión con Spotify</a>
    </body>
    </html>
    '''

@app.route('/login')
def login():
    try:
        sp_oauth = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE,
            show_dialog=True  # Fuerza a mostrar el diálogo de autorización
        )
        auth_url = sp_oauth.get_authorize_url()
        print(f"Redirigiendo a: {auth_url}")  # Para debugging
        return redirect(auth_url)
    except Exception as e:
        return f"Error al iniciar sesión: {str(e)}"


@app.route('/callback')
def callback():
    try:
        sp_oauth = SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE
        )
        
        code = request.args.get('code')
        token_info = sp_oauth.get_access_token(code)
        session['token_info'] = token_info
        
        return redirect(url_for('get_top_tracks'))
    except Exception as e:
        return f"Error en callback: {str(e)}"

@app.route('/top-tracks')
def get_top_tracks():
    try:
        token_info = session.get('token_info', None)
        if not token_info:
            return redirect(url_for('login'))

        sp = spotipy.Spotify(auth=token_info['access_token'])
        
        # Get user info
        user_info = sp.current_user()
        
        # Get top artists and tracks
        top_artists = sp.current_user_top_artists(limit=10, time_range='short_term')
        top_tracks = sp.current_user_top_tracks(limit=10, time_range='short_term')
        
        # Create HTML with results
        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Spotify Top Tracks - {user_info['display_name']}</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    padding: 20px; 
                    max-width: 900px; 
                    margin: 0 auto; 
                    background: linear-gradient(135deg, #1DB954, #191414);
                    color: white;
                    min-height: 100vh;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                    background: rgba(0,0,0,0.3);
                    padding: 20px;
                    border-radius: 15px;
                }}
                h1 {{ color: #1DB954; margin: 0; }}
                h2 {{ color: #1DB954; border-bottom: 2px solid #1DB954; padding-bottom: 10px; }}
                .list {{ margin: 20px 0; }}
                .item {{ 
                    margin: 10px 0; 
                    padding: 15px; 
                    background: rgba(255,255,255,0.1); 
                    border-radius: 10px; 
                    border-left: 4px solid #1DB954;
                    backdrop-filter: blur(10px);
                }}
                .item:hover {{
                    background: rgba(255,255,255,0.2);
                    transform: translateX(5px);
                    transition: all 0.3s ease;
                }}
                .user-info {{
                    text-align: center;
                    margin-bottom: 30px;
                    font-size: 18px;
                }}
                .back-btn {{
                    background-color: #1DB954;
                    color: white;
                    padding: 10px 20px;
                    border: none;
                    border-radius: 25px;
                    text-decoration: none;
                    display: inline-block;
                    margin: 20px 0;
                }}
                .back-btn:hover {{ background-color: #1ed760; }}
                @media (max-width: 600px) {{
                    body {{ padding: 10px; }}
                    .item {{ padding: 10px; }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎵 Tus Top de Spotify</h1>
                <div class="user-info">¡Hola {user_info['display_name']}!</div>
                <a class="back-btn" href="/">← Volver al inicio</a>
            </div>
        '''
        
        for i, artist in enumerate(top_artists['items'], 1):
            html += f'<div class="item">{i}. {artist["name"]}</div>'
        
        html += '<h2>🎵 Tus canciones más escuchadas</h2><div class="list">'
        
        for i, track in enumerate(top_tracks['items'], 1):
            artists = ", ".join(artist["name"] for artist in track["artists"])
            html += f'<div class="item">{i}. <strong>{track["name"]}</strong> - {artists}</div>'
        
        html += '''
            </div>
        </body>
        </html>
        '''
        return html
        
    except Exception as e:
        return f"Error obteniendo tracks: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))