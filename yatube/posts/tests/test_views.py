from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from django.conf import settings

from ..models import Post, Group

User = get_user_model()

POSTS_ON_2ND_PAGE = 3
POST_CREATE = settings.POSTS_ON_PAGE + POSTS_ON_2ND_PAGE


class TestViewPosts(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.second_group = Group.objects.create(
            title='Вторая группа',
            slug='second_group',
            description='Описание второй группы',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост группы',
            group=cls.group,
        )

    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def test_templates_users(self):
        """Тестируем соответствие шаблонов, вызываемых view-функциями
        (используется учетная запись автора поста)."""
        templates_used = {
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:main_page'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'any_slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.user}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.id}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_used.items():
            with self.subTest(template=template):
                response = self.post_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        """Шаблоны страниц сформированы с правильынм контекстом."""
        response_home = self.authorized_client.get(reverse(
            'posts:main_page')).context['page_obj'][0]
        response_group = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'any_slug': self.group.slug})
        ).context['page_obj'][0]
        response_profile = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.author})
        ).context['page_obj'][0]
        response_post = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id})
        ).context['post'].author.posts.all()[0]
        show_info = {
            self.post.id: response_home.id,
            self.group.title: response_home.group.title,
            self.post.text: response_home.text,
            self.post.author: response_home.author,
            self.group.slug: response_home.group.slug,
            self.post.id: response_group.id,
            self.group.title: response_group.group.title,
            self.group.description: response_group.group.description,
            self.post.text: response_group.text,
            self.post.author: response_group.author,
            self.group.slug: response_group.group.slug,
            self.post.id: response_profile.id,
            self.group.slug: response_profile.group.slug,
            self.post.text: response_profile.text,
            self.post.author: response_profile.author,
            self.post.id: response_post.id,
            self.group.title: response_post.group.title,
            self.group.slug: response_post.group.slug,
            self.post.text: response_post.text,
            self.post.author: response_post.author,
        }
        for info, context in show_info.items():
            with self.subTest(info=info):
                self.assertEqual(info, context)

    def test_post_create_show_correct_context(self):
        """Функция post_create передает правильный контекст в шаблон."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Функция post_edit передает правильный контекст в шаблон."""
        response = self.post_author.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_with_group_is_on_pages(self):
        """Тестируем наличие поста с группой на страницах"""
        response = self.authorized_client.get(
            f'/group/{self.second_group.slug}/')
        self.assertNotIn(self.post,
                         response.context['page_obj'])


class TestPaginator(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.author = User.objects.create_user(username='auth')
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        Post.objects.bulk_create(
            [Post(
                author=self.author,
                text=f'Тестовый текст №{i}',
                group=self.group,
            ) for i in range(POST_CREATE)]
        )

    def test_paginator_pages(self):
        """Тестируем работу паджинатора у главной страницы,
        страницы группы и страницы поста."""

        response_values = {
            self.guest_client.get(
                reverse('posts:main_page')): settings.POSTS_ON_PAGE,
            self.guest_client.get(
                reverse('posts:main_page') + '?page=2'
            ): POSTS_ON_2ND_PAGE,
            self.guest_client.get(
                reverse(
                    'posts:group_list',
                    kwargs={'any_slug': self.group.slug})
            ): settings.POSTS_ON_PAGE,
            self.guest_client.get(
                reverse('posts:group_list',
                        kwargs={
                            'any_slug': self.group.slug}) + '?page=2'
            ): POSTS_ON_2ND_PAGE,
            self.guest_client.get(
                reverse('posts:profile', kwargs={'username': self.author})
            ): settings.POSTS_ON_PAGE,
            self.guest_client.get(
                reverse('posts:profile',
                        kwargs={'username': self.author}) + '?page=2'
            ): POSTS_ON_2ND_PAGE,
        }
        for response, value in response_values.items():
            with self.subTest(response=response):
                self.assertEqual(len(response.context['page_obj']), value)
