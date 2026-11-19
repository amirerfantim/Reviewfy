# Reviewfy

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Django 4.2](https://img.shields.io/badge/django-4.2-0C4B33.svg)

Reviewfy is a Django REST API where users view articles and rate them from 0 to
5. It handles a large number of ratings, and it makes sure that short-term
rating spikes, such as a campaign of fake votes, do not move the average score
much.

**Contents:** [How it works](#how-it-works) · [Run it with Docker](#run-it-with-docker) ·
[Run it without Docker](#run-it-without-docker) · [Settings](#settings) · [API](#api) ·
[Tests](#tests) · [Project layout](#project-layout)

## Technologies

| | |
|---|---|
| Django 4.2, Django REST Framework | The web API |
| JWT (`djangorestframework-simplejwt`) | Sign-in and API access |
| Celery with Celery beat | Background processing of ratings |
| Redis | Queue for ratings, Celery broker, cache |
| PostgreSQL | Articles and ratings |
| Docker Compose | Running everything together |

## How it works

A rating is not written to the database when it arrives. It goes through Redis
and three periodic Celery tasks:

```
POST /api/articles/rate/
  -> Redis "unprocessed" ratings
  -> every 30 s: compute the suspicion factor of each rating
       below the threshold -> Redis "normal" ratings
       at or above it      -> Redis "suspicious" ratings
  -> every 60 s:  normal ratings are saved to PostgreSQL, the average is updated
  -> every 120 s: only the oldest 20% of the suspicious ratings are saved
                  (or one rating, when there are 5 or fewer)
```

A new rating therefore shows up in the article list after about a minute.

### Rating system

- When a user submits a rating for an article, it is first stored in **Redis**.
- A periodic task calculates the **suspicion factor** of the rating. This factor
  helps to identify and manage potentially manipulated ratings.
- A user has one rating per article. Rating again updates the earlier rating.

### Suspicious rating handling

- If the **suspicion factor** of a rating is at or above the defined **threshold**
  (`SUSPICION_THRESHOLD`), the rating is classified as suspicious and handled by
  a separate task.
- If the suspicion factor is below the threshold, the rating is processed normally.
- The system applies only 20% of the older suspicious ratings each time, so that
  a sudden surge in ratings (like a spam attack) does not change the average
  score drastically.

### Suspicion factor calculation

The **suspicion factor** of each rating is based on three things:

1. **Hourly rating fluctuation.**
   This factor checks how the number of ratings for an article has changed in
   the last hour compared to the same hour on the previous day. If there is a
   significant increase in ratings (over 100%), it may indicate that a large
   group of users suddenly started rating the article, which could be an attempt
   to manipulate the score. If this happens, the suspicion factor is raised.

   *Example:* if there were 10 ratings for an article between 2:00 PM and
   3:00 PM on the previous day, and there are 30 ratings between 2:00 PM and
   3:00 PM today, that is a **200% increase**. This raises the suspicion factor.

2. **The user's rating history.**
   If a user has been consistently giving extreme ratings (either 0 or 5) for
   different articles, it could indicate abnormal behavior. This raises the
   suspicion factor.

   *Example:* if the user has rated 10 articles recently, and 8 of them are rated
   either 0 or 5, the suspicion factor is higher.

3. **Recent ratings of the article.**
   This factor compares the current rating to the recent ratings of the article
   over the last week. If the score deviates significantly from the mean of
   recent ratings, it is considered suspicious.

   *Example:* if an article has been rated around 3.5 for the last week and a new
   rating is suddenly 5 or 0, it can be flagged as suspicious.

## Run it with Docker

The compose file is in `deployment/`. Run these commands from the repository
root:

```bash
cp .env.example .env
docker compose -f deployment/docker-compose.yml up --build
```

This starts the web app (with gunicorn), a Celery worker, Celery beat,
PostgreSQL 13 and Redis 6, and applies the database migrations. The API is at
<http://localhost:8000>. To create an admin user for `/admin/`:

```bash
docker compose -f deployment/docker-compose.yml exec web python manage.py createsuperuser
```

Stop everything and delete the database with
`docker compose -f deployment/docker-compose.yml down -v`.

## Run it without Docker

You need Python 3.9 or newer, PostgreSQL and Redis.

```bash
python3 -m venv venv
source venv/bin/activate            # on Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` so that the services are found on your machine: set `REDIS_HOST`,
`POSTGRES_HOST` and the host in the three Redis URLs (`REDIS_CACHE_LOCATION`,
`CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`) to `localhost`. Create the
PostgreSQL database named in `POSTGRES_DB`, then apply the migrations:

```bash
python manage.py migrate
```

Start three long-running processes, one per terminal:

```bash
python manage.py runserver
celery -A reviewfy worker --loglevel=info
celery -A reviewfy beat --loglevel=info
```

Without the worker and beat, ratings stay in Redis and never reach the list.

## Settings

All settings are environment variables, read from `.env`. [`.env.example`](.env.example)
lists them. These are the ones that matter most, with the value the code uses
when a variable is missing:

| Variable | Default | Meaning |
|---|---|---|
| `SUSPICION_THRESHOLD` | `0.5` | Ratings at or above this suspicion factor are handled as suspicious. |
| `SECRET_KEY` | `secret_key` | Django secret key, also used to sign JWTs. Set your own. |
| `DEBUG` | `True` | Only the exact text `True` turns debug mode on. |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated host names. |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | `reviewfy`, `postgres`, `postgres` | Database login. |
| `POSTGRES_HOST`, `POSTGRES_PORT` | `db`, `5432` | Database address. |
| `REDIS_HOST`, `REDIS_PORT` | `localhost`, `6379` | Redis address for the rating queue. |
| `CACHE_ENABLED` | `True` | Cache the article list. |
| `ARTICLES_LIST_CACHE_TIMEOUT` | `60` | Seconds the article list stays cached. |
| `JWT_ACCESS_TOKEN_LIFETIME` | `720` | Minutes an access token is valid. |
| `JWT_REFRESH_TOKEN_LIFETIME` | `7` | Days a refresh token is valid. |

## API

Every endpoint except register, login and refresh needs the header
`Authorization: Bearer <access token>`. The examples below were run against the
Docker setup above.

| Method and path | Purpose |
|---|---|
| `POST /api/auth/register/` | Create a user: `username`, `password` |
| `POST /api/auth/login/` | Get an `access` and a `refresh` token |
| `POST /api/auth/refresh/` | Exchange a `refresh` token for a new pair |
| `GET /api/articles/` | List articles with their ratings |
| `POST /api/articles/create/` | Create an article: `title`, `content` |
| `POST /api/articles/rate/` | Rate an article: `article` (id), `score` |

```bash
B=http://localhost:8000
curl -s -X POST $B/api/auth/register/ -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"s3cret-pass"}'
# {"username":"alice"}

curl -s -X POST $B/api/auth/login/ -H 'Content-Type: application/json' \
  -d '{"username":"alice","password":"s3cret-pass"}'
# {"access":"eyJ...","refresh":"eyJ..."}

curl -s -X POST $B/api/articles/create/ -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' -d '{"title":"Hello Reviewfy","content":"First article."}'
# {"id":1,"title":"Hello Reviewfy","content":"First article.","created_at":"...","updated_at":"...","ratings_count":0,"avg_rating":"0.00"}

curl -s -X POST $B/api/articles/rate/ -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' -d '{"article":1,"score":"5"}'
# {"detail":"Rating added successfully."}

curl -s $B/api/articles/ -H "Authorization: Bearer $ACCESS"
# after about a minute:
# [{"title":"Hello Reviewfy","ratings_count":1,"avg_rating":5.0,"user_rating":5}]
```

Things to know:

- `score` must be a **string** of a whole number from 0 to 5, such as `"5"`. A JSON
  number is rejected with `400 {"detail": "Score must be a valid integer."}`.
- The article list shows `title`, `ratings_count`, `avg_rating` and `user_rating`
  (`"No rating"` until you have rated). It does not include the article `id`.
  The `id` comes from the create response or from the admin site.
- Until the Celery tasks have processed a rating, the list still shows the old
  numbers.

## Tests

```bash
docker compose -f deployment/docker-compose.yml exec web python manage.py test
```

Without Docker, run `python manage.py test`. There are 13 tests, for
registration, login, token refresh, article creation and listing, and rating.

## Project layout

```
reviewfy/         Django settings, URLs and the Celery app
articles/         models, views, serializers and the Celery tasks
authentication/   registration, login and token refresh
utils/            suspicion calculation, Redis and cache helpers
deployment/       Dockerfile and docker-compose.yml
scripts/          wait-for-it.sh, used when the web container starts
```

## License

MIT. See [LICENSE](LICENSE).
