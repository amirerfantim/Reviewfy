import redis
from django.conf import settings

redis_client = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)


def add_rating_to_redis(article_id, user_id, score):
    redis_client.hset(f"ratings:{article_id}", user_id, score)


def get_user_rating_from_redis(article_id, user_id):
    rating = redis_client.hget(f"ratings:{article_id}", user_id)
    if rating:
        return int(rating)
    return None


def delete_user_rating_from_redis(article_id, user_id):
    redis_client.hdel(f"ratings:{article_id}", user_id)


def get_all_ratings_from_redis(article_id):
    return redis_client.hgetall(f"ratings:{article_id}")
