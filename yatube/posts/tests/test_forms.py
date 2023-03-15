from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group
User = get_user_model()


class TestViewPosts(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.second_group = Group.objects.create(
            title='Вторая группа',
            slug='second_slug',
            description='Второе описание',
        )
        self.author = User.objects.create_user(username='auth')
        self.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        self.post = Post.objects.create(
            author=self.author,
            text='Тестовый пост группы',
            group=self.group,
            id='50',
        )
        self.post_author = Post.author
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def test_create_new_post(self):
        """Валидная форма создает новую запись в БД."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст нового поста',
            'group': self.second_group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            ('/profile/test_user/'),
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Текст нового поста',
            ).exists()
        )

    def test_edited_post_exists(self):
        """Тестируем, что отредактированый пост изменяет данные."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст отредактированного поста',
            'group': self.second_group.id,
        }
        self.post_author.post(
            reverse('posts:post_edit', kwargs={'post_id': '50'}),
            data=form_data,
            follow=True
        )
        edited_post = Post.objects.get(id='50')
        self.assertEqual(edited_post.text, form_data['text'])
        self.assertEqual(edited_post.group.id, form_data['group'])
        self.assertEqual(Post.objects.count(), posts_count)
