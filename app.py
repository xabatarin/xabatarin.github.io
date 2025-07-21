from flask import Flask, redirect, request, session, url_for, render_template_string
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import secrets
import os  
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Actualiza las credenciales para usar variables de entorno
CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID', '24e44232fd75456d92df0cc79125f0a7')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET', '91ebf78ab4264252b6f562079ca0b9b9')
REDIRECT_URI = os.getenv('REDIRECT_URI', 'http://127.0.0.1:5000/callback')
SCOPE = 'user-top-read playlist-modify-public'

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
        
        # Get top artists and tracks
        top_artists = sp.current_user_top_artists(limit=10, time_range='medium_term')
        top_tracks = sp.current_user_top_tracks(limit=10, time_range='medium_term')
        
        # Create HTML with results
        html = '''
            <style>
                body { font-family: Arial; padding: 40px; max-width: 800px; margin: 0 auto; }
                h2 { color: #1DB954; }
                .list { margin: 20px 0; }
                .item { margin: 10px 0; padding: 10px; background: #f5f5f5; border-radius: 5px; }
            </style>
            <h2>🎤 Tus artistas más escuchados</h2>
            <div class="list">
        '''
        
        for i, artist in enumerate(top_artists['items'], 1):
            html += f'<div class="item">{i}. {artist["name"]}</div>'
        
        html += '<h2>🎵 Tus canciones más escuchadas</h2><div class="list">'
        
        for i, track in enumerate(top_tracks['items'], 1):
            artists = ", ".join(artist["name"] for artist in track["artists"])
            html += f'<div class="item">{i}. {track["name"]} - {artists}</div>'
        
        html += '</div>'
        return html
        
    except Exception as e:
        return f"Error obteniendo tracks: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))