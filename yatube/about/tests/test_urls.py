from http import HTTPStatus

from django.test import TestCase, Client


class StaticPagesTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_author_and_tech(self):
        """Тестируем статические страницы author и tech."""
        response = {
            'author': self.guest_client.get('/about/author/'),
            'tech': self.guest_client.get('/about/tech/'),
        }
        for page, url in response.items():
            with self.subTest(page=page):
                self.assertEqual(url.status_code, HTTPStatus.OK)
