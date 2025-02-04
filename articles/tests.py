from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from .models import Article, Rating
from rest_framework_simplejwt.tokens import RefreshToken


class ArticleTests(APITestCase):

    def setUp(self):
        self.register_data = {'username': 'testuser', 'password': 'testpassword'}
        self.client.post('/api/auth/register/', self.register_data, format='json')
        login_data = {'username': 'testuser', 'password': 'testpassword'}
        response = self.client.post('/api/auth/login/', login_data, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

        self.article = Article.objects.create(title="Test Article", content="This is a test article.")

    def test_article_list_view(self):
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_article_create_view(self):
        data = {'title': 'New Article', 'content': 'Content for the new article.'}
        response = self.client.post('/api/articles/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Article.objects.count(), 2)

    def test_article_create_view_invalid_data(self):
        data = {'title': '', 'content': 'Missing title'}
        response = self.client.post('/api/articles/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_article_create_view_no_title(self):
        data = {'content': 'Missing title'}
        response = self.client.post('/api/articles/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RatingTests(APITestCase):

    def setUp(self):
        self.register_data = {'username': 'testuser', 'password': 'testpassword'}
        self.client.post('/api/auth/register/', self.register_data, format='json')
        login_data = {'username': 'testuser', 'password': 'testpassword'}
        response = self.client.post('/api/auth/login/', login_data, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

        self.article = Article.objects.create(title="Test Article", content="This is a test article.")
        self.user = User.objects.get(username='testuser')


    def test_rating_create_view_invalid_score(self):
        data = {'article': self.article.pk, 'score': "6"}
        response = self.client.post('/api/articles/rate/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Score must be between 0 and 5.")

    def test_rating_create_view_no_score(self):
        data = {'article': self.article.pk}
        response = self.client.post('/api/articles/rate/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Article and score are required.")

    def test_rating_create_view_invalid_article(self):
        data = {'article': 9999, 'score': "3"}
        response = self.client.post('/api/articles/rate/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ArticleRatingTests(APITestCase):

    def setUp(self):
        self.register_data = {'username': 'testuser', 'password': 'testpassword'}
        self.client.post('/api/auth/register/', self.register_data, format='json')
        login_data = {'username': 'testuser', 'password': 'testpassword'}
        response = self.client.post('/api/auth/login/', login_data, format='json')
        self.token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)

        self.article = Article.objects.create(title="Test Article", content="This is a test article.")
        self.user = User.objects.get(username='testuser')

    def test_user_rating_for_article(self):
        rating = Rating.objects.create(user=self.user, article=self.article, score=3)
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['user_rating'], rating.score)



