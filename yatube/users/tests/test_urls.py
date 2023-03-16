from http import HTTPStatus

from django.test import TestCase, Client
from django.contrib.auth import get_user_model

User = get_user_model()


class UsersPagesTest(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages(self):
        """Тестируем страницы для пользоавтелей."""
        response = {
            'signup': self.guest_client.get('/auth/signup/'),
            'login': self.authorized_client.get('/auth/login/'),
            'logout': self.authorized_client.get('/auth/logout/'),
            'password_change': self.authorized_client.get(
                '/auth/password_change/', follow=True),
            'password_change_done': self.authorized_client.get(
                '/auth/password_change/done/', follow=True),
            'password_reset': self.authorized_client.get(
                '/auth/password_reset/'),
            'password_reset_done': self.authorized_client.get(
                '/auth/password_reset/done/'),
            'reset_done': self.authorized_client.get('/auth/reset/done/'),
        }
        for page, url in response.items():
            with self.subTest(page=page):
                self.assertEqual(url.status_code, HTTPStatus.OK)
