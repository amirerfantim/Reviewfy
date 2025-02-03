import ast
import time
import redis
from django.conf import settings

redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)

RATING_TYPES = {
    "unprocessed": "unprocessed_ratings",
    "suspicious": "suspicious_ratings",
    "normal": "normal_ratings"
}


def add_rating_to_redis(article_id, user_id, score, rating_type='unprocessed', suspicion_factor=0.0):
    timestamp = int(time.time())
    key = f"{RATING_TYPES.get(rating_type)}:{article_id}"
    value = f"{score},{suspicion_factor},{timestamp}"
    redis_client.hset(key, user_id, value)


def get_user_rating_from_redis(article_id, user_id, rating_type='unprocessed'):
    key = f"{RATING_TYPES.get(rating_type)}:{article_id}"
    rating = redis_client.hget(key, user_id)
    return int(rating) if rating else None


def delete_user_rating_from_redis(article_id, user_id, rating_type='unprocessed'):
    key = f"{RATING_TYPES.get(rating_type)}:{article_id}"
    redis_client.hdel(key, user_id)


def get_ratings_from_redis(article_id, rating_type='unprocessed'):
    key = f"{RATING_TYPES.get(rating_type)}:{article_id}"
    ratings_data = redis_client.hgetall(key)

    ratings = {}
    for user_id, data in ratings_data.items():
        data = data.decode('utf-8')
        score, suspicion_factor, timestamp = data.split(',')

        ratings[user_id] = {
            'score': int(ast.literal_eval(score)),
            'suspicion_factor': float(suspicion_factor),
            'timestamp': int(timestamp)
        }

    return ratings
