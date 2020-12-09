import datetime

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.core.paginator import Paginator
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import User, Group, Post


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД
        cls.user = User.objects.create(
            username='testusername',
            email='testusername@testmail.com',
        )
        cls.group = Group.objects.create(
            title='Тестовое сообщество',
            slug='test-slug',
            description='test description'
        )
        cls.post = Post.objects.create(
            text='Заголовок тестовой записи',
            pub_date=datetime.date.today(),
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            'index.html': reverse('posts:index'),
            'new_post.html': reverse('posts:new_post'),
            'group.html': (
                reverse('posts:blogs', kwargs={'slug': 'test-slug'})
            ),
            'profile.html': (
                reverse('posts:profile', kwargs={'username': 'testusername'})
            ),
            'post.html': (
                reverse('posts:post', kwargs={'username': 'testusername',
                                              'post_id': 1})
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_post_edit_page_uses_correct_template(self):
        template = 'new_post.html'
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'username': 'testusername',
                                               'post_id': 1}))
        self.assertTemplateUsed(response, template)

    # Проверка словаря контекста страницы для создания поста
    # (в нём передаётся форма)
    def test_new_post_page_show_correct_context(self):
        """Шаблон new_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:new_post'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    # Проверяем, что словарь context главной страницы
    # содержит ожидаемые значения, и при создании поста
    # этот пост появляется на главной странице сайта
    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        post_text_0 = response.context.get('page')[0].text
        post_pub_date_0 = response.context.get('page')[0].pub_date
        post_author_0 = response.context.get('page')[0].author
        post_group_0 = response.context.get('page')[0].group
        self.assertEqual(post_text_0, 'Заголовок тестовой записи')
        self.assertEqual(post_pub_date_0.date(), datetime.date.today())
        self.assertEqual(post_author_0, PostPagesTests.user)
        self.assertEqual(post_group_0, PostPagesTests.group)

    # Проверяем, что словарь context страницы group/test-slug
    # содержит ожидаемые значения и при создании поста
    # этот пост появляется на странице выбранной группы
    def test_blogs_detail_pages_show_correct_context(self):
        """
        Шаблон blogs сформирован с правильным контекстом.
        Новый пост появляется на странице выбранной группы
        """
        response = self.authorized_client.get(
            reverse('posts:blogs', kwargs={'slug': 'test-slug'})
        )
        self.assertEqual(response.context.get('group').title,
                         'Тестовое сообщество')
        self.assertEqual(response.context.get('group').description,
                         'test description')
        self.assertEqual(response.context.get('group').slug, 'test-slug')

    # Проверяем, что словарь context страницы testusername/
    # содержит ожидаемые значения
    def test_profile_pages_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'testusername'})
        )
        self.assertEqual(response.context.get('profile_user'),
                         PostPagesTests.user)
        self.assertEqual(response.context.get('user_post_count'), 1)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создадим запись в БД
        cls.user = User.objects.create(
            username='testusername',
            email='testusername@testmail.com',
        )
        cls.group = Group.objects.create(
            title='Тестовое сообщество',
            slug='test-slug',
            description='test description'
        )
        cls.first_page_object_list = []
        for post_number in range(1, 14):
            post = Post.objects.create(
                text=f'{post_number}. Заголовок тестовой записи',
                pub_date=datetime.date.today(),
                author=cls.user,
                group=cls.group
            )
            if post_number > 3:
                cls.first_page_object_list.append(post)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PaginatorViewsTest.user)

    def test_first_page_containse_ten_records(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_containse_three_records(self):
        response = self.authorized_client.get(
            reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)

    def test_first_page_show_correct_context(self):
        """Содержимое постов на первой странице соответствует ожиданиям"""
        response = self.authorized_client.get(reverse('posts:index'))
        # переворачиваем список постов, по порядку добавления
        page_objects = response.context.get('page').object_list[::-1]
        self.assertEqual(page_objects,
                         PaginatorViewsTest.first_page_object_list)
