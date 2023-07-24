# Test task: URL monitoring service

## Modules
### FastAPI app
File: `app.py`

Example: 
```
uvicorn app:app --host 0.0.0.0 --port 8000
```

It is used to run API endpoints. It's quite simple and lightweight. Only 
needed to create or remove monitors.

#### Possible ways to improve
- More methods for working with monitors (list, get, etc..)
- Detailed descriptions for fields in responses/requests

### Standalone worker
File: `worker.py`

Example:
```
python worker.py
```

Is used for grabbing data from websites and persisting all the data to the 
database. 

Each worker is a simple asyncio application that scans the database for
scheduled monitors and executes requests to websites. 

Can be run in multiple instances. Each instance uses database as a single 
source of truth and will execute only it's part of tasks. 
No duplicate scans are made due to Postgres lock mechanism.

#### Possible ways to improve
- Add a database pool instead of one connection and split batches into a
smaller ones.
- Add `asyncio.semaphore` support for limiting amount of requests, can provide
more flexibility
- For now if one request in a batch takes too long all other requests have 
to wait - can be solved by smaller batches and stricter timeouts. Also saving 
results and rescheduling on a per-monitor basis will solve the problem, but 
will affect performance.

### CLI
File: `manage.py`

Example:
```
python manage.py generate-monitors
```

For now only use cases are:
- Generate dummy URLs for monitor to work with
- Make migrations.

## Database structure
Has two tables:
- `monitors` - stores all monitors. Active and inactive. 
- `monitor_log` - **timescaledb** table, used for storing scan results data

## How to run
- Create a `prod.env` file with `DB_CONNECTION_STRING` (only one required
  parameter, only PostreSQL is supported)
- Run `docker-compose.yml` in order to start all services (API and worker)
- (optional) Run `python manage.py generate-monitors` in order to generate some URLs for
  scanning

Postgres should be run independently.

## What can be improved:
- More units (especially corner cases). Code coverage is more than 90% now, so
most of the code behaves properly.
- Implement duplicate checking on monitor creation (url/regexp pair)
- Proper migrations (for now it's only creation of tables)