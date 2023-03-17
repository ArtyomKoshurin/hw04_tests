from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост группы',
            group=cls.group
        )

    def test_correct_str(self):
        """Проверяем, что у моделей корректно работает __str__."""
        testing_vars = {
            str(self.group): self.group.title,
            str(self.post): self.post.text[:15],
        }
        for field, expected_value in testing_vars.items():
            with self.subTest(field=field):
                self.assertEqual(
                    expected_value, field
                )

    def test_help_text_post(self):
        """Проверяем, что у моделей корректно работает help_text."""
        post = PostModelTest.post
        testing_vars = {
            'text': 'Текст поста',
            'group': 'Выберите группу',
        }
        for field, expected_value in testing_vars.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value
                )

    def test_verbose_name_post(self):
        """Проверяем, что у моделей корректно работает verbose_name."""
        post = PostModelTest.post
        testing_vars = {
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in testing_vars.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value
                )
