import logging
from celery import shared_task
from django.db import transaction

from utils.rating_utils import process_redis_ratings, remove_ratings_from_redis
from .models import Article, Rating
from utils.redis_utils import get_all_ratings_from_redis

logger = logging.getLogger(__name__)


@shared_task
def process_new_ratings():
    articles = Article.objects.all()

    for article in articles:
        logger.info(f"Processing article {article.title} (ID: {article.pk})")

        existing_ratings = Rating.objects.filter(article=article)
        total_score_db = sum([rating.score for rating in existing_ratings])
        total_ratings_db = article.ratings_count
        logger.info(f"Total score from DB: {total_score_db}, Total ratings count: {total_ratings_db}")

        new_ratings = get_all_ratings_from_redis(article.pk)
        if not new_ratings:
            continue

        total_score_redis, total_ratings_redis = process_redis_ratings(article, new_ratings)

        total_score = total_score_db + total_score_redis
        total_ratings = total_ratings_db + total_ratings_redis

        logger.info(f"Calculated new total score: {total_score}, total ratings: {total_ratings}")

        with transaction.atomic():
            article.update_avg_rating(total_score, total_ratings)

        remove_ratings_from_redis(article, new_ratings)
