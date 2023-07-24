# Test task: URL monitoring service

## How to run
 - Create a `prod.env` file with `DB_CONNECTION_STRING` (only one required 
parameter)
 - Run `docker-compose.yml` in order to start all services (API and worker)
 - Run `python manage.py generate-monitors` in order to generate some URLs for
scanning

## Modules
### FastAPI app
File: `app.py`

Example: 
```
uvicorn app:app --host 0.0.0.0 --port 8000
```

It is used to run API endpoints. It's quite simple and is only needed to create
or remove monitors.

### Standalone worker
File: `worker.py`

Example:
```
python worker.py
```

Is used for grabbing data from websites and persisting all the data to the 
database. Each worker is an asyncio application that scans the database for
scheduled monitors and executes requests to websites. Can be run in multiple
instances. Each instance uses database as a single source of truth and will
execute only it's part of tasks. No duplicate scans are made due to Postgres
lock mechanism.

### CLI
File: `manage.py`

Example:
```
python manage.py generate-monitors
```

For now only use case is to generate dummy URLs for monitor to work with.

### What can be improved:
- More units (especially corner cases)
- Implement duplicate checking on monitor creation (url/regexp pair)
- Proper migrations

### How-to start
- Using `docker-compose.yml` (Postgres should be started independently)