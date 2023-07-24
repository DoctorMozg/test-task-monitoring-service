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

#### How it works
It has two REST API methods:
- `POST /monitors` - creates a new monitor and returns its ID. Monitor is
scheduled for scan immediately after creation.
- `DELETE /monitors/{id}/` - deactivates monitor but leaves all scans intact.

Uses connection pool for optimal performance. Strict type checking is done
using **pydantic** in order to ensure everything is valid and also this makes
future improvement of such service will be easier and less error-prone.

As i don't want to overcomplicate this service i've decided to move scanning
functionality to the separate process 
(see [standalone worker](#standalone-worker)). This will allow to scale things
independently and save some resources.

By utilizing load balancers this service will be pretty easy to scale. 

#### Possible ways to improve
- More methods for working with monitors (list, get, etc..)
- Detailed descriptions for fields in responses/requests
- Implement duplicate checking on monitor creation (url/regexp pair), 
also reactivate disabled monitors in these cases instead of creating a new ones.

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

You can run tens of such workers. They'll be working fine in
parallel, as long as Postgres performance allows it. So it's pretty easy to
scale it.

#### How it works
1. Upon starting, this app enters infinite loop which only stops on exit.
2. It grabs all pending monitor scans from the DB and locks them so only this
service will perform scans.
3. It tries to execute as close to `POLL_INTERVAL` as possible. In case requests
are taking longer than `POLL_INTERVAL` it will execute next loop immediately
after finishing the previous one.
4. It runs all scans in a batch using `asyncio.gather` method.
5. The next scan is scheduled right after the current scan is complete.

In this alg. I've assumed that a deviation in scan schedule for much less 
than second doesn't matter. In a very rare cases it can be big, but this won't
affect a lot of monitors.

#### Possible ways to improve
- Add a database pool instead of one connection and split batches into a
smaller ones.
- Add `asyncio.semaphore` support for limiting amount of requests, can provide
more flexibility
- For now if one request in a batch takes too long all other requests have 
to wait - can be solved by smaller batches and stricter timeouts. Also saving 
results and rescheduling on a per-monitor basis will solve the problem, but 
will affect performance.
- Upon rescheduling we can also use monitor's `next_sync` field instead of just
`CURRENT_TIMESTAMP`. This method will be more accurate but can lead to problems
if workers will be lagging behind the schedule.

### CLI
File: `manage.py`

Example:
```
python manage.py generate-monitors
```

For now only use cases are:
- Generate dummy URLs for monitor to work with
- Create database schema for services

#### Possible ways to improve
- Use dedicated library for migrations (for now it's only creation of tables)

## Database structure
Has two tables:
- `monitors` - stores all monitors and their settings. Active and inactive. 
- `monitor_log` - **timescaledb** table, used for storing scan results data.

## Checks
Multiple linters like **ruff** or **mypy** are ensuring that code is clean, 
readable and correct in terms of types. This will greatly speed up future
development.

## Testing
Tests are run using **pytest**. It reads its configuration from `pyproject.toml`
file. Also, sensitive configuration parameters like DCS are being read from
`test.env` file.

## How to run
- Build an image from `Dockerfile` (is also done by GitHub CI), and it should be
named `url-monitor-server:latest`
- Create a `prod.env` file with `DB_CONNECTION_STRING` (only one required
  parameter, only PostreSQL is supported)
- Run `docker-compose.yml` in order to start all services (API and worker)
- (optional) Run `python manage.py generate-monitors` in order to generate some URLs for
  scanning

Postgres should be run independently.

## Production
The main idea is to build new **Docker image** and push them to a registry 
like **Docker Hub**.
During the deployment stage, these images are downloaded onto the server,
and **docker-compose** is used to run the production stack.

## What can be globally improved:
- More units (especially corner cases). Code coverage is more than 90% now, so
most of the code is tested.
- Add health-checking to the **Docker** image