import datetime
import logging
from decimal import Decimal

import numpy as np
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Article(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ratings_count = models.PositiveIntegerField(default=0)
    avg_rating = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return self.title

    def update_avg_rating(self, total_score, total_ratings):
        avg_rating = Decimal(total_score) / Decimal(total_ratings) if total_ratings > 0 else Decimal('0.00')
        avg_rating = avg_rating.quantize(Decimal('0.00'))
        self.avg_rating = avg_rating
        self.ratings_count = total_ratings
        self.save()


class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    article = models.ForeignKey(Article, on_delete=models.CASCADE)
    score = models.IntegerField(choices=[(i, i) for i in range(6)])
    suspicion_factor = models.FloatField(default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'article')

    def __str__(self):
        return f"{self.user.username} - {self.article.title} - {self.score}"

    @classmethod
    def update_or_create_rating(cls, user_id, article, score, suspicion_factor):
        previous_rating = cls.objects.filter(user_id=user_id, article=article).first()
        if previous_rating:
            rating_diff = int(score) - previous_rating.score
            previous_rating.score = int(score)
            previous_rating.suspicion_factor = suspicion_factor
            previous_rating.save(update_fields=['score', 'suspicion_factor'])
            return rating_diff, 0
        else:
            cls.objects.create(user_id=user_id, article=article, score=int(score), suspicion_factor=suspicion_factor)
            return int(score), 1
