import datetime
import logging

import numpy as np
from django.utils import timezone

from articles.models import Rating

logger = logging.getLogger(__name__)


def calculate_suspicion(score, user, article):
    suspicion_factor = 0.0
    now = timezone.now()
    one_hour_ago_yesterday = now - datetime.timedelta(days=1, hours=1)
    one_hour_end_yesterday = now - datetime.timedelta(days=1)

    today_ratings_count = Rating.objects.filter(
        article=article, created_at__gte=one_hour_ago_yesterday
    ).count()

    past_ratings_count = Rating.objects.filter(
        article=article, created_at__gte=one_hour_ago_yesterday, created_at__lt=one_hour_end_yesterday
    ).count()

    if past_ratings_count > 0:
        ratings_diff = today_ratings_count - past_ratings_count
        percentage_diff = abs(ratings_diff / past_ratings_count) * 100

        if percentage_diff > 100:
            suspicion_factor += min(np.log(percentage_diff / 100) / 5, 0.5)

    user_recent_ratings = Rating.objects.filter(
        user=user
    ).order_by('-created_at')[:10]

    zero_five_count = sum([1 for rating in user_recent_ratings if rating.score == 0 or rating.score == 5])
    if zero_five_count > 0:
        suspicion_factor += min(zero_five_count * 0.05, 0.3)

    recent_ratings = Rating.objects.filter(
        article=article,
        created_at__gte=timezone.now() - datetime.timedelta(days=7)
    ).values('score')

    if len(recent_ratings) > 2:
        scores = [rating['score'] for rating in recent_ratings]
        mean_score = np.mean(scores)
        std_dev = np.std(scores)

        if abs(score - mean_score) > std_dev:
            suspicion_factor += min((abs(score - mean_score) / std_dev) * 0.1, 0.5)

    return min(suspicion_factor, 1.0)
