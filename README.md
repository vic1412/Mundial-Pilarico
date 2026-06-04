# ⚽ Mundial Pilarico 2026

Quiniela privada del Mundial 2026 para tres amigos.

## Instalación rápida

```bash
cd Mundial2026
pip install -r requirements.txt
streamlit run app.py
```

## API de resultados en tiempo real

1. Regístrate gratis en https://dashboard.api-football.com/register
2. Copia tu API key
3. Pégala en `.streamlit/secrets.toml`:
   ```
   API_FOOTBALL_KEY = "tu_clave_aquí"
   ```
4. Reinicia la app

Sin API key la app funciona con el calendario de partidos precargado (sin resultados reales).

## Acceso desde el móvil (misma red WiFi)

1. Ejecuta `streamlit run app.py` en tu PC
2. Streamlit mostrará una URL tipo `http://192.168.x.x:8501`
3. Abre esa URL en el navegador del móvil

## Sistema de puntuación

| Resultado | Puntos |
|-----------|--------|
| Resultado exacto | 4 |
| Ganador correcto + diferencial de gol correcto | 3 |
| Ganador correcto | 2 |
| Empate (marcador distinto) | 2 |
| Incorrecto | 0 |
