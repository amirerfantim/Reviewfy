from rest_framework import generics

from utils.redis_utils import add_rating_to_redis, get_user_rating_from_redis, delete_user_rating_from_redis
from .serializers import ArticleSerializer
from rest_framework.permissions import IsAuthenticated
from .models import Rating, Article
from .serializers import RatingSerializer
from rest_framework.response import Response
from rest_framework import status


class ArticleListView(generics.ListAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        articles = self.get_queryset()
        response_data = []

        for article in articles:
            ratings_count = article.ratings_count
            avg_rating = article.avg_rating

            try:
                user_rating_obj = Rating.objects.get(article=article, user=request.user)
                user_rating = user_rating_obj.score
            except Rating.DoesNotExist:
                user_rating = "No rating"

            article_data = {
                "title": article.title,
                "ratings_count": ratings_count,
                "avg_rating": float(avg_rating),
                "user_rating": user_rating
            }

            response_data.append(article_data)

        return Response(response_data, status=status.HTTP_200_OK)


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
