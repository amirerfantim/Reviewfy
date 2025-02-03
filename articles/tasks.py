import logging
from celery import shared_task
from django.contrib.auth.models import User

from reviewfy import settings
from utils.rating_utils import calculate_suspicion
from .models import Article, Rating
from utils.redis_utils import get_ratings_from_redis, add_rating_to_redis, delete_user_rating_from_redis

logger = logging.getLogger(__name__)


@shared_task
def process_unprocessed_ratings():
    articles = Article.objects.all()

    for article in articles:
        logger.info(f"Processing unprocessed ratings for article {article.title} (ID: {article.pk})")

        unprocessed_ratings = get_ratings_from_redis(article.pk, rating_type='unprocessed')
        if not unprocessed_ratings:
            continue

        for user_id, rating_data in unprocessed_ratings.items():
            score = rating_data['score']
            user = User.objects.get(id=user_id)

            suspicion_factor = calculate_suspicion(score, user, article)

            if suspicion_factor >= settings.SUSPICION_THRESHOLD:
                add_rating_to_redis(article.pk, user_id, score, rating_type='suspicious',
                                    suspicion_factor=suspicion_factor)
            else:
                add_rating_to_redis(article.pk, user_id, score, rating_type='normal', suspicion_factor=suspicion_factor)

            delete_user_rating_from_redis(article.pk, user_id, rating_type='unprocessed')


@shared_task
def process_suspicious_ratings():
    articles = Article.objects.all()

    for article in articles:
        logger.info(f"Processing suspicious ratings for article {article.title} (ID: {article.pk})")

        suspicious_ratings = get_ratings_from_redis(article.pk, rating_type='suspicious')
        if not suspicious_ratings:
            continue

        sorted_ratings = sorted(suspicious_ratings.items(), key=lambda x: x[1]['timestamp'])

        total_ratings_count = len(sorted_ratings)
        ratings_to_process_count = int(total_ratings_count * 0.2) if total_ratings_count > 5 else 1

        ratings_to_process = sorted_ratings[:ratings_to_process_count]

        total_score_suspicious = 0
        total_ratings_suspicious = 0

        existing_ratings = Rating.objects.filter(article=article)
        total_score_db = sum([rating.score for rating in existing_ratings])
        total_ratings_db = article.ratings_count

        for user_id, rating_data in ratings_to_process:
            score = rating_data['score']
            suspicion_factor = rating_data['suspicion_factor']

            rating_diff, is_new = Rating.update_or_create_rating(user_id, article, score, suspicion_factor)

            if is_new:
                total_ratings_suspicious += 1

            total_score_suspicious += rating_diff
            delete_user_rating_from_redis(article.pk, user_id, rating_type='suspicious')

        total_score = total_score_db + total_score_suspicious
        total_ratings = total_ratings_db + total_ratings_suspicious

        article.update_avg_rating(total_score, total_ratings)

        logger.info(f"Processed {ratings_to_process_count} suspicious ratings for article {article.title}.")


@shared_task
def process_normal_ratings():
    articles = Article.objects.all()

    for article in articles:
        logger.info(f"Processing normal ratings for article {article.title} (ID: {article.pk})")

        normal_ratings = get_ratings_from_redis(article.pk, rating_type='normal')
        if not normal_ratings:
            continue

        sorted_ratings = sorted(normal_ratings.items(), key=lambda x: x[1]['timestamp'])

        total_score_normal = 0
        total_ratings_normal = 0

        existing_ratings = Rating.objects.filter(article=article)
        total_score_db = sum([rating.score for rating in existing_ratings])
        total_ratings_db = article.ratings_count

        for user_id, rating_data in sorted_ratings:
            score = rating_data['score']
            suspicion_factor = rating_data['suspicion_factor']

            rating_diff, is_new = Rating.update_or_create_rating(user_id, article, score, suspicion_factor)

            if is_new:
                total_ratings_normal += 1

            total_score_normal += rating_diff
            delete_user_rating_from_redis(article.pk, user_id, rating_type='normal')

        total_score = total_score_db + total_score_normal
        total_ratings = total_ratings_db + total_ratings_normal

        article.update_avg_rating(total_score, total_ratings)

        logger.info(f"Processed {len(sorted_ratings)} normal ratings for article {article.title}.")
