from django.urls import path
from .views import ArticleListView, RatingCreateView, ArticleCreateView

urlpatterns = [
    path('', ArticleListView.as_view(), name='article-list'),
    path('rate/', RatingCreateView.as_view(), name='article-rate'),
    path('create/', ArticleCreateView.as_view(), name='article-create'),
]
