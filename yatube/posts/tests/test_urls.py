from django.test import TestCase, Client
from django.contrib.auth import get_user_model

from http import HTTPStatus

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост группы',
            group=cls.group,
            id='50'
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Authorized')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Post.author
        self.author = PostsURLTests.author
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def test_allusers_page(self):
        """Тестируем общедоступные страницы."""
        response = {
            'main': self.guest_client.get('/'),
            'group': self.guest_client.get('/group/test_slug/'),
            'profile': self.guest_client.get('/profile/auth/'),
            'posts': self.guest_client.get('/posts/50/'),
        }
        for page, url in response.items():
            with self.subTest(page=page):
                self.assertEqual(url.status_code, HTTPStatus.OK)

    def test_create_page(self):
        """Тестируем страницу создания поста для авторизованного
        пользователя."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_user_from_create(self):
        """Страница create перенаправит неавторизованного пользователя
        на страницу логина."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, ('/auth/login/?next=/create/'))

    def test_editing_author_post(self):
        """Тестрируем страницу для редактирования поста автором."""
        response = self.post_author.get('/posts/50/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_user_from_edit(self):
        """Страница edit перенаправит пользователя,
        не являющимся автором - на страницу поста."""
        response = self.guest_client.get('/posts/50/edit/')
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unexisting_page(self):
        """Проверка 404 при переъоде на несуществующую страницу."""
        response = self.guest_client.get('/random_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_templates_posts(self):
        """Тестируем шаблоны."""
        templates_urls = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            '/posts/50/': 'posts/post_detail.html',
            '/posts/50/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_urls.items():
            with self.subTest(url=url):
                response = self.post_author.get(url)
                self.assertTemplateUsed(response, template)
