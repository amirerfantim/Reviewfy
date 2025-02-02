from articles.models import Rating
from articles.tasks import logger
from utils.redis_utils import delete_user_rating_from_redis


def process_redis_ratings(article, new_ratings):
    total_score_redis = 0
    total_ratings_redis = 0

    for user_id, score in new_ratings.items():
        logger.info(f"Processing rating for user {user_id}: {score}")

        rating_diff, is_new = Rating.update_or_create_rating(user_id, article, score)

        if is_new:
            total_ratings_redis += 1

        total_score_redis += rating_diff

    return total_score_redis, total_ratings_redis


def remove_ratings_from_redis(article, new_ratings):
    for user_id in new_ratings.keys():
        delete_user_rating_from_redis(article.pk, user_id)
        logger.info(f"Deleted rating for user {user_id} from Redis.")
