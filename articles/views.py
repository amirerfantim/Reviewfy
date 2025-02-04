from django.conf import settings
from rest_framework import generics
from utils.cache_utils import get_or_set_cache
from utils.redis_utils import add_rating_to_redis
from rest_framework.permissions import IsAuthenticated
from .serializers import RatingSerializer
from rest_framework.response import Response
from rest_framework import status
from .models import Article, Rating
from .serializers import ArticleSerializer
from django.core.exceptions import ObjectDoesNotExist


class ArticleListView(generics.ListAPIView):
    queryset = Article.objects.all()
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        try:
            articles = get_or_set_cache('articles_list', self.get_queryset(),
                                        timeout=settings.ARTICLES_LIST_CACHE_TIMEOUT)
        except Exception as e:
            return Response({"detail": f"Error fetching articles: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        response_data = []

        for article in articles:
            ratings_count = article.ratings_count
            avg_rating = article.avg_rating

            try:
                user_rating_obj = Rating.objects.get(article=article, user=request.user)
                user_rating = user_rating_obj.score
            except Rating.DoesNotExist:
                user_rating = "No rating"
            except Exception as e:
                return Response({"detail": f"Error fetching user rating: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

        if not article_id or not score:
            return Response({"detail": "Article and score are required."}, status=status.HTTP_400_BAD_REQUEST)

        if not isinstance(score, str) or not score.isdigit():
            return Response({"detail": "Score must be a valid integer."}, status=status.HTTP_400_BAD_REQUEST)

        score = int(score)

        if score < 0 or score > 5:
            return Response({"detail": "Score must be between 0 and 5."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            Article.objects.get(pk=article_id)
        except ObjectDoesNotExist:
            return Response({"detail": f"Article {article_id} not found."}, status=status.HTTP_404_NOT_FOUND)

        add_rating_to_redis(article_id, user.id, score, rating_type='unprocessed')

        return Response({"detail": "Rating added successfully."}, status=status.HTTP_201_CREATED)
