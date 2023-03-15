from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from ..models import Post, Group

User = get_user_model()


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
            id='50'
        )

    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Post.author
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def test_templates_users(self):
        """Тестируем соответствие шаблонов, вызываемых view-функциями
        (используется учетная запись автора поста)."""
        templates_used = {
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:main_page'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'any_slug': 'test_slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': 'test_user'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': '50'}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': '50'}
            ): 'posts/create_post.html',
        }
        for reverse_name, template in templates_used.items():
            with self.subTest(template=template):
                response = self.post_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_homepage_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:main_page'))
        first_object = response.context['page_obj'][0]
        show_info = {
            'Тестовая группа': first_object.group.title,
            'Тестовый пост группы': first_object.text,
            TestViewPosts.author.username: first_object.author.username,
            'test_slug': first_object.group.slug,
        }
        for info, context in show_info.items():
            with self.subTest(info=info):
                self.assertEqual(info, context)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'any_slug': 'test_slug'})
        )
        first_object = response.context['page_obj'][0]
        show_info = {
            'Тестовая группа': first_object.group.title,
            'Тестовое описание': first_object.group.description,
            'Тестовый пост группы': first_object.text,
            TestViewPosts.author.username: first_object.author.username,
        }
        for info, context in show_info.items():
            with self.subTest(info=info):
                self.assertEqual(info, context)

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': 'auth'})
        )
        first_object = response.context['page_obj'][0]
        show_info = {
            'test_slug': first_object.group.slug,
            'Тестовый пост группы': first_object.text,
            TestViewPosts.author.username: first_object.author.username,
        }
        for info, context in show_info.items():
            with self.subTest(info=info):
                self.assertEqual(info, context)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': '50'})
        )
        first_object = response.context['posts'][0]
        show_info = {
            'Тестовая группа': first_object.group.title,
            'test_slug': first_object.group.slug,
            'Тестовый пост группы': first_object.text,
            TestViewPosts.author.username: first_object.author.username,
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
            'posts:post_edit', kwargs={'post_id': '50'})
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
        response_index = self.authorized_client.get('/')
        response_group = self.authorized_client.get('/group/test_slug/')
        response_profile = self.authorized_client.get('/profile/auth/')
        response_false_group = self.authorized_client.get(
            '/group/second_group/')
        self.assertIn('Тестовый пост группы', response_index.content.decode())
        self.assertIn('Тестовый пост группы', response_group.content.decode())
        self.assertIn('Тестовый пост группы',
                      response_profile.content.decode())
        self.assertNotIn('Тестовый пост группы',
                         response_false_group.content.decode())


class TestPaginator(TestCase):

    def setUp(self):
        self.guest_client = Client()
        self.author = User.objects.create_user(username='auth')
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        # Пытался придумать другой вариант создания нескольких
        # объектов, но не получилось
        Post.objects.create(author=self.author, text='А', group=self.group)
        Post.objects.create(author=self.author, text='Б', group=self.group)
        Post.objects.create(author=self.author, text='В', group=self.group)
        Post.objects.create(author=self.author, text='Г', group=self.group)
        Post.objects.create(author=self.author, text='Д', group=self.group)
        Post.objects.create(author=self.author, text='Е', group=self.group)
        Post.objects.create(author=self.author, text='Ж', group=self.group)
        Post.objects.create(author=self.author, text='З', group=self.group)
        Post.objects.create(author=self.author, text='И', group=self.group)
        Post.objects.create(author=self.author, text='К', group=self.group)
        Post.objects.create(author=self.author, text='Л', group=self.group)

    def test_paginator_pages(self):
        """Тестируем работу паджинатора у главной страницы,
        страницы группы и страницы поста."""
        POSTS_ON_1_PAGE = 10
        POSTS_ON_2_PAGE = 1
        response_values = {
            self.guest_client.get(
                reverse('posts:main_page')): POSTS_ON_1_PAGE,
            self.guest_client.get(
                reverse('posts:main_page') + '?page=2'): POSTS_ON_2_PAGE,
            self.authorized_client.get(
                reverse(
                    'posts:group_list',
                    kwargs={'any_slug': 'test_slug'})): POSTS_ON_1_PAGE,
            self.authorized_client.get(
                reverse('posts:group_list',
                        kwargs={
                            'any_slug': 'test_slug'}) + '?page=2'
            ): POSTS_ON_2_PAGE,
            self.authorized_client.get(
                reverse('posts:profile', kwargs={'username': 'auth'})
            ): POSTS_ON_1_PAGE,
            self.authorized_client.get(
                reverse('posts:profile',
                        kwargs={'username': 'auth'}) + '?page=2'
            ): POSTS_ON_2_PAGE,
        }
        for response, value in response_values.items():
            with self.subTest(response=response):
                self.assertEqual(len(response.context['page_obj']), value)
