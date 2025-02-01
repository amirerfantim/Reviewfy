from rest_framework import generics

from utils.redis_utils import add_rating_to_redis, get_user_rating_from_redis, delete_user_rating_from_redis
from .serializers import ArticleSerializer
from rest_framework.permissions import IsAuthenticated
from .models import Rating, Article
from .serializers import RatingSerializer
from rest_framework.response import Response
from rest_framework import status
import redis


class ArticleListView(generics.ListAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]


class ArticleCreateView(generics.CreateAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]


class RatingCreateView(generics.CreateAPIView):
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        article_id = request.data.get('article')
        score = request.data.get('score')

        if not score.isdigit():
            return Response({"detail": "Score must be a valid integer."}, status=status.HTTP_400_BAD_REQUEST)
        score = int(score)

        if score < 0 or score > 5:
            return Response({"detail": "Score must be between 0 and 5."}, status=status.HTTP_400_BAD_REQUEST)

        add_rating_to_redis(article_id, user.id, score)

        return Response({"detail": "Rating added successfully."}, status=status.HTTP_201_CREATED)
