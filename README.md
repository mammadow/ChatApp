# ChatApp

ChatApp is a small Django + Channels project for a shared realtime chat room. This version adds a cleaner interface, persists recent messages, protects the socket behind authentication, and includes a deploy path that serves WebSockets correctly.

## Features

- Django authentication for login/logout
- Shared room chat over Django Channels
- Recent message persistence in SQLite
- Responsive chat interface with connection status
- Basic automated tests for page access and socket behavior
- ASGI deployment via Daphne for WebSocket support

## Stack

- Python
- Django
- Django Channels
- Daphne
- SQLite

## Local Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt
```

3. Apply migrations:

```powershell
python manage.py migrate
```

4. Create a user:

```powershell
python manage.py createsuperuser
```

5. Run the development server:

```powershell
python manage.py runserver
```

6. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) and sign in.

## Tests

Run the test suite with:

```powershell
python manage.py test
```

## Deployment Notes

- The app entrypoint is ASGI, not WSGI, because chat uses WebSockets.
- `Procfile` and `railway.json` now start Daphne instead of Gunicorn.
- `requirements.txt` is reduced to the primary runtime dependencies.

## Project Structure

- `ChatApp/` contains project settings and ASGI/WSGI entrypoints.
- `chat/` contains the chat app, templates, static assets, consumer, and tests.
- `db.sqlite3` is the local development database.

## License

This project is available under the MIT License. See [LICENSE](LICENSE).
