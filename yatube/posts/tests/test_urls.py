from http import HTTPStatus

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse

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
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Authorized')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def test_allusers_page(self):
        """Тестируем общедоступные страницы в соответствии с правами
        пользователей и их статусом входа."""
        response = {
            self.guest_client.get(
                reverse('posts:main_page')
            ): HTTPStatus.OK,
            self.guest_client.get(
                reverse(
                    'posts:group_list',
                    kwargs={'any_slug': self.group.slug})
            ): HTTPStatus.OK,
            self.guest_client.get(
                reverse(
                    'posts:profile',
                    kwargs={'username': self.author})
            ): HTTPStatus.OK,
            self.guest_client.get(
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': self.post.id})
            ): HTTPStatus.OK,
            self.authorized_client.get('/create/'): HTTPStatus.OK,
            self.post_author.get(
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': self.post.id})
            ): HTTPStatus.OK,
            self.authorized_client.get(
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': self.post.id})
            ): HTTPStatus.FOUND,
            self.guest_client.get(
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': self.post.id})
            ): HTTPStatus.FOUND,
            self.guest_client.get('/create/'): HTTPStatus.FOUND,
        }
        for url, response_status in response.items():
            with self.subTest(url=url):
                self.assertEqual(url.status_code, response_status)

    def test_redirect_user_from_create(self):
        """Страница create перенаправит неавторизованного пользователя
        на страницу логина."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, ('/auth/login/?next=/create/'))

    def test_redirect_user_from_edit(self):
        """Страница edit перенаправит пользователя,
        не являющимся автором - на страницу поста."""
        response = self.guest_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_unexisting_page(self):
        """Проверка 404 при переходе на несуществующую страницу."""
        response = self.guest_client.get('/random_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_templates_posts(self):
        """Тестируем шаблоны."""
        templates_urls = {
            '/': 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'any_slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.author}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for url, template in templates_urls.items():
            with self.subTest(url=url):
                response = self.post_author.get(url)
                self.assertTemplateUsed(response, template)
