from django.contrib import admin
from .models import Article, Rating


class ArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'created_at', 'updated_at', 'ratings_count', 'avg_rating')
    search_fields = ('title', 'content')
    list_filter = ('created_at',)


class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'article', 'score', 'suspicion_factor', 'created_at')
    search_fields = ('user__username', 'article__title')
    list_filter = ('score', 'created_at')


admin.site.register(Article, ArticleAdmin)
admin.site.register(Rating, RatingAdmin)
