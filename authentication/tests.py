from rest_framework.test import APITestCase
from rest_framework import status


class AuthTests(APITestCase):

    def setUp(self):
        self.register_data = {'username': 'testuser', 'password': 'testpassword'}
        self.client.post('/api/auth/register/', self.register_data, format='json')

    def test_register_user_success(self):
        data = {'username': 'newuser', 'password': 'newpassword'}
        response = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_register_user_missing_field(self):
        data = {'username': 'newuser'}
        response = self.client.post('/api/auth/register/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_login_user_success(self):
        login_data = {'username': 'testuser', 'password': 'testpassword'}
        response = self.client.post('/api/auth/login/', login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


    def test_refresh_token_missing(self):
        response = self.client.post('/api/auth/refresh/', {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Refresh token is required.")

    def test_refresh_token_invalid(self):
        response = self.client.post('/api/auth/refresh/', {'refresh': 'invalidtoken'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], "Invalid or expired refresh token.")
