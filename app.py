from flask import Flask, redirect, request, session, url_for, render_template_string
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import MemoryCacheHandler
import secrets
import os
from dotenv import load_dotenv
import random
import joblib
import re
import pandas as pd
import nltk
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from collections import Counter

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

# --- Funciones del Modelo de Clasificación ---

def limpiar_tweet(texto):
    """Limpia el texto de entrada para que coincida con el preprocesamiento del modelo."""
    texto = re.sub(r"http\S+|www\.\S+", "", texto)
    texto = re.sub(r"@\w+", "", texto)
    texto = re.sub(r"#\w+", "", texto)
    texto = re.sub(r"[^\w\sáéíóúüñÁÉÍÓÚÜÑ]", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto.lower()
    
def top_words_by_label(df, label_col, text_col, top_n):
    vocab = set()
    for label in df[label_col].unique():
        textos = df[df[label_col] == label][text_col]
        palabras = ' '.join(textos).split()
        top = [w for w, _ in Counter(palabras).most_common(top_n)]
        vocab.update(top)
    return list(vocab)

def train_sentiment_model():
    """
    Carga los datos, los preprocesa y entrena el modelo de clasificación de sentimientos.
    """
    nltk.download('stopwords')
    from nltk.corpus import stopwords
    spanish_stopwords = set(stopwords.words('spanish'))

    # Construir la ruta al archivo de datos
    data_path = os.path.join(os.path.dirname(__file__), 'train.tsv')
    if not os.path.exists(data_path):
        print(f"ADVERTENCIA: El archivo de datos '{data_path}' no se encontró.")
        return None, None, None

    print("Entrenando el modelo de clasificación de sentimientos...")
    # Cargar datos
    df = pd.read_csv(data_path, sep='\t')
    df.columns = [col.strip() for col in df.columns]
    df = df[df['label'].isin(['joy ', 'sadness ', 'anger '])].copy()
    # Indizea berrabiarazi
    df.reset_index(drop=True, inplace=True)
    # 'id' zutabea kendu
    df = df.drop(columns=['id'])
    # 'HASHTAG' ordezkatu '#' karaktereagatik, aldaketa betirako gordez
    df['tweet'] = df['tweet'].str.replace('HASHTAG', '#')
    # Limpieza y preprocesamiento
    df['tweet'] = df['tweet'].apply(limpiar_tweet)
    

    # Codificar etiquetas y vectorizar texto
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df['label'])
    


    # Vocabulario personalizado (top-N por label)
    custom_vocab = top_words_by_label(df, 'label', 'tweet', top_n=1250)

    # Eliminar stopwords del vocabulario personalizado
    custom_vocab_no_stop = [w for w in custom_vocab if w.lower() not in spanish_stopwords]

    # Vectorizador con vocabulario personalizado sin stopwords
    vectorizer = TfidfVectorizer(vocabulary=custom_vocab_no_stop)
    X = vectorizer.fit_transform(df['tweet'])

    tfidf_df = pd.DataFrame(X.toarray(), columns=vectorizer.get_feature_names_out())
    tfidf_df['tweet'] = df['tweet'].values
    tfidf_df['label'] = df['label'].values

    cols = ['tweet'] + [col for col in tfidf_df.columns if col not in ['tweet', 'label']] + ['label']
    tfidf_df = tfidf_df[cols]

    # Entrenar el clasificador MLP
    mlp = MLPClassifier(
            hidden_layer_sizes=(256,128,32),
            activation='tanh',
            solver='adam',
            alpha=0.1,
            learning_rate_init=0.001,
            max_iter=200,
            random_state=42,
            early_stopping=True,
            n_iter_no_change=25,
            tol=1e-4,
            verbose=False
        )
    mlp.fit(X,y )

    
    print("Modelo entrenado y listo.")
    return vectorizer, mlp, label_encoder

# Entrenar los modelos una sola vez al iniciar la app
vectorizer, mlp, label_encoder = train_sentiment_model()

def predecir_sentimiento(texto):
    """Predice el sentimiento de un texto usando el modelo MLP cargado."""
    if not all([vectorizer, mlp, label_encoder]):
        raise RuntimeError("Los modelos de clasificación no están cargados. Verifica que 'train.tsv' exista.")
    
    texto_limpio = limpiar_tweet(texto)
    vector_texto = vectorizer.transform([texto_limpio])
    prediccion_numerica = mlp.predict(vector_texto)
    prediccion_etiqueta = label_encoder.inverse_transform(prediccion_numerica)
    
    # Mapear la etiqueta a un 'mood' simple
    etiqueta = prediccion_etiqueta[0].strip()
    if etiqueta == 'joy':
        return 'feliz'
    elif etiqueta == 'sadness':
        return 'triste'
    elif etiqueta == 'anger':
        return 'enfadado'
    return 'desconocido'



@app.route('/crear-playlist', methods=['GET', 'POST'])
def crear_playlist():
    try:
        token_info = get_token()
        if not token_info:
            return redirect(url_for('login'))
        sp = spotipy.Spotify(auth=token_info['access_token'])
        user_info = sp.current_user()

        if request.method == 'POST':
            user_text = request.form.get('user_text')
            if not user_text:
                return 'Por favor, introduce un texto.', 400

            # Predecir el estado de ánimo a partir del texto
            try:
                mood = predecir_sentimiento(user_text)
            except RuntimeError as e:
                return f"Error del modelo: {e}", 500
            except Exception as e:
                return f"Error al predecir el sentimiento: {e}", 500

            if mood == 'desconocido':
                return "No se pudo determinar un sentimiento claro del texto. Inténtalo de nuevo.", 400
            
            # Si está enfadado, redirigir a una playlist tranquila
            if mood == 'enfadado':
                # URL de una playlist de Spotify con música tranquila (Peaceful Piano)
                calm_playlist_url = 'https://open.spotify.com/playlist/37i9dQZF1DX4sWSpwq3LiO'
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
            
            # 1. Obtener las 20 canciones más escuchadas del último mes.
            top_tracks_results = sp.current_user_top_tracks(limit=20, time_range='short_term')
            
            # 2. Obtener los 10 artistas más escuchados del último mes.
            top_artists_results = sp.current_user_top_artists(limit=10, time_range='short_term')

            # Usar un diccionario para evitar duplicados por ID de canción.
            track_pool = {track['id']: track for track in top_tracks_results['items'] if track and track.get('id')}

            # 3. Añadir hasta 10 canciones populares de cada uno de los 10 artistas principales.
            artist_ids = [artist['id'] for artist in top_artists_results['items'] if artist and artist.get('id')]
            for artist_id in artist_ids:
                try:
                    # Pedimos las 10 canciones más populares del artista.
                    artist_top_tracks = sp.artist_top_tracks(artist_id, country='ES')['tracks']
                    for track in artist_top_tracks: # Iteramos sobre las 10 canciones
                        # Añadir solo si no está ya en la lista
                        if track and track.get('id') and track['id'] not in track_pool:
                            track_pool[track['id']] = track
                except Exception as e:
                    print(f"No se pudieron obtener canciones para el artista {artist_id}: {e}")
                    continue

            # Convertir el diccionario de canciones únicas a una lista
            final_track_list = list(track_pool.values())
            
            # Verificar si hay suficientes canciones para crear una playlist
            if len(final_track_list) < 18:
                 return f"<h2>No tienes suficientes canciones en tu historial para crear una playlist ({len(final_track_list)} encontradas). ¡Escucha más música!</h2><a href='/dashboard'>Volver</a>"

            uris = []
            nombre = ""
            
            if mood == 'triste':
                nombre = "huts egiten ez dutenak"
                # Elegir 18 canciones aleatorias de la lista combinada
                selected_tracks = random.sample(final_track_list, 18)
                uris = [t['uri'] for t in selected_tracks]

            elif mood == 'feliz':
                nombre = "Playlist para un día feliz - Emo2Music"
                # Elegir 10 canciones aleatorias de la lista combinada
                base_tracks = random.sample(final_track_list, 10)
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
                        extra_pool = [t for t in final_track_list if t['uri'] not in uris]
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
            <title>Crear Playlist por Sentimiento</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            {get_base_css()}
            <style>
                textarea {{
                    width: 95%;
                    padding: 15px;
                    border-radius: 5px;
                    border: 1px solid #535353;
                    background-color: #282828;
                    color: white;
                    font-size: 1em;
                    min-height: 80px;
                    resize: vertical;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Crear Playlist Basada en un Sentimiento</h2>
                <form method="post" class="form-container">
                    <label for="user_text">Escribe una frase (máx. 240 caracteres) que describa cómo te sientes:</label>
                    <textarea name="user_text" id="user_text" maxlength="240" required></textarea>
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