# Spotify Top Tracks App

Una aplicación web que muestra tus artistas y canciones más escuchadas de Spotify.

## Configuración para uso público

### 1. Configurar la aplicación de Spotify

1. Ve a [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Crea una nueva aplicación
3. En la configuración de la app, agrega estas URLs de redirección:
   - Para desarrollo local: `http://localhost:5000/callback`
   - Para producción: `https://tu-dominio.com/callback`

### 2. Configurar variables de entorno

Crea un archivo `.env` con:
```
SPOTIFY_CLIENT_ID=tu_client_id
SPOTIFY_CLIENT_SECRET=tu_client_secret
REDIRECT_URI=https://tu-dominio.com/callback
SECRET_KEY=tu_clave_secreta_aleatoria
```

### 3. Desplegar en Heroku

1. Instala Heroku CLI
2. Ejecuta estos comandos:

```bash
heroku create tu-app-name
heroku config:set SPOTIFY_CLIENT_ID=tu_client_id
heroku config:set SPOTIFY_CLIENT_SECRET=tu_client_secret
heroku config:set REDIRECT_URI=https://tu-app-name.herokuapp.com/callback
heroku config:set SECRET_KEY=tu_clave_secreta
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

### 4. Alternativas de despliegue

- **Railway**: Fácil despliegue conectando tu repositorio de GitHub
- **Render**: Gratis con algunas limitaciones
- **PythonAnywhere**: Buena opción para principiantes
- **DigitalOcean App Platform**: Más control y escalabilidad

## Instalación local

```bash
pip install -r requirements.txt
python app.py
```

## Uso

1. Ve a la URL de tu aplicación
2. Haz clic en "Iniciar sesión con Spotify"
3. Autoriza la aplicación
4. ¡Disfruta viendo tus tops!
