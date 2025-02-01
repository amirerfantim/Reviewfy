# articles/tasks.py
import logging
from decimal import Decimal
from celery import shared_task
from django.db import transaction
from .models import Article, Rating
from utils.redis_utils import get_all_ratings_from_redis, delete_user_rating_from_redis

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

        total_score_redis = 0
        total_ratings_redis = 0

        for user_id, score in new_ratings.items():
            logger.info(f"Processing rating for user {user_id}: {score}")

            previous_rating_db = Rating.objects.filter(user_id=user_id, article=article).first()

            if previous_rating_db:
                rating_diff = int(score) - previous_rating_db.score
                total_score_redis += rating_diff
                logger.info(f"User {user_id} previously rated {previous_rating_db.score}. Updated by {rating_diff}.")
                previous_rating_db.score = int(score)
                previous_rating_db.save()
            else:
                total_score_redis += int(score)
                total_ratings_redis += 1
                logger.info(f"User {user_id} added new rating {score}.")
                Rating.objects.create(user_id=user_id, article=article, score=int(score))

        total_score = total_score_db + total_score_redis
        total_ratings = total_ratings_db + total_ratings_redis

        avg_rating = Decimal(total_score) / Decimal(total_ratings) if total_ratings > 0 else Decimal('0.00')

        avg_rating = avg_rating.quantize(Decimal('0.00'))

        logger.info(f"Calculated new average rating for article {article.title}: {avg_rating}")

        with transaction.atomic():
            article.avg_rating = avg_rating
            article.ratings_count = total_ratings
            article.save()

        for user_id in new_ratings.keys():
            delete_user_rating_from_redis(article.pk, user_id)
            logger.info(f"Deleted rating for user {user_id} from Redis.")
