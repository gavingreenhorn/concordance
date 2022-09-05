import io
import shutil
import tempfile
from http import HTTPStatus
from urllib.parse import urljoin, unquote

from django import forms
from django.conf import settings
from django.test import TestCase, Client, override_settings
from django.shortcuts import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils.http import urlencode
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from posts.models import Post, Group, Comment
from posts.forms import PostForm
from .utils import write_log


User = get_user_model()
# temporary location for media files to be stored at
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class NamedClient(Client):
    def __init__(self, name):
        super().__init__()
        self.name = name


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.new_group = Group.objects.create(
            title='new group',
            slug='new-group',
            description='something descriptive'
        )
        cls.new_group_2 = Group.objects.create(
            title='new group 2',
            slug='new-group-2',
            description='something even more descriptive'
        )
        cls.user_random = User.objects.create(username='wacko wacko')
        cls.user_author = User.objects.create(username='danger-pwrs')
        cls.CREATE = reverse('posts:post_create')
        cls.PROFILE = reverse(
            'posts:profile',
            kwargs={'username': cls.user_author.username}
        )
        cls.EXPECTED_FIELD_TYPES = {
            'text': forms.CharField,
            'group': forms.ModelChoiceField,
            'image': forms.ImageField,
        }
        cls.EXPECTED_HTML_TAGS = {
            'text': (
                '<textarea name="text" cols="40" '
                'rows="10" required id="id_text">'
            ),
            'group': '<option value="" selected> Выберите группу </option>',
            'image': (
                '<input type="file" name="image" '
                'accept="image/*" id="id_image">'
            )
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cache.clear()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    @staticmethod
    def get_test_img(color: str) -> SimpleUploadedFile:
        image = Image.new('RGB', (10, 10), color)
        byte_arr = io.BytesIO()
        image.save(byte_arr, format='jpeg')
        file = SimpleUploadedFile(
            name=f'{color}.jpeg',
            content=byte_arr.getvalue(),
            content_type='image/jpeg'
        )
        return file

    def get_post_data(self, action):
        post_data = {
            'create': {
                'text': 'Test post 1',
                'group': self.new_group.pk,
                'image': self.get_test_img('red'),
            },
            'update': {
                'text': 'Test post 2',
                'group': self.new_group_2.pk,
                'image': self.get_test_img('blue')
            }
        }
        return post_data[action]

    def create_post(self, test_client):
        data = self.get_post_data('create')
        response = PostsFormsTest.post_to(
            test_client, PostsFormsTest.CREATE, data
        )
        return response

    def update_post(self, test_client, post_id):
        edit_url = reverse('posts:post_edit', args=(post_id,))
        data = self.get_post_data('update')
        response = PostsFormsTest.post_to(
            test_client, edit_url, data
        )
        return response

    def post_to(test_client, to, data):
        response = test_client.post(
            to,
            data,
            follow=True,
            multipart=True,
        )
        write_log(test_client, to, data, TEMP_MEDIA_ROOT, response)
        return response

    def setUp(self):
        self.form = PostForm()
        self.guest_client = NamedClient('Guest client')
        self.auth_client = NamedClient('Authorised client')
        self.auth_client.force_login(self.user_random)
        self.author_client = NamedClient('Author client')
        self.author_client.force_login(self.user_author)

    def test_expected_fields(self):
        """test if the fields are present"""
        for field in ('text', 'group'):
            with self.subTest(field_name=field):
                self.assertIn(field, self.form.fields)

    def test_create_form_is_rendered(self):
        """test if the fields are rendered correctly"""
        for field, html in self.EXPECTED_HTML_TAGS.items():
            with self.subTest(field_name=field):
                self.assertInHTML(html, str(self.form))

    def test_field_types(self):
        """test if the fields are of correct types"""
        for field_name, field_type in self.EXPECTED_FIELD_TYPES.items():
            with self.subTest(field_name=field_name):
                field = self.form.fields.get(field_name)
                self.assertIsInstance(field, field_type)

    def test_count_increment(self):
        """test if post objects count is incremented"""
        post_count = Post.objects.count()
        expected_increment = {
            self.guest_client: post_count,
            self.auth_client: post_count + 1,
        }
        for client, new_count in expected_increment.items():
            with self.subTest(client=client.name):
                self.create_post(client)
                self.assertEqual(
                    Post.objects.count(), new_count,
                )

    def test_create_redirects(self):
        """test if user is redirected to profile page"""
        response = self.create_post(self.author_client)
        self.assertRedirects(response, self.PROFILE)

    def test_edit_form_initial_state(self):
        """test if edit form's fields are correctly pre-populated"""
        self.create_post(self.author_client)
        test_post = Post.objects.latest('pub_date')
        edit_url = reverse(
            'posts:post_edit',
            kwargs={'pk': test_post.id}
        )
        r = self.author_client.get(edit_url)
        form = r.context['form']
        for field, value in form.initial.items():
            with self.subTest(field=field):
                field_name = 'group_id' if field == 'group' else field
                self.assertEqual(test_post.__dict__[field_name], value)

    def test_edit_form_change(self):
        """test if initial post is modified"""
        expected_asserts = {
            self.guest_client: self.assertEqual,
            self.auth_client: self.assertEqual,
            self.author_client: self.assertNotEqual
        }
        for client, func in expected_asserts.items():
            self.create_post(self.author_client)
            test_post = Post.objects.latest('pub_date')
            self.update_post(client, test_post.id)
            edited_post = Post.objects.get(id=test_post.id)
            for field in ('text', 'group', 'image'):
                with self.subTest(client=client.name, field=field):
                    func(
                        getattr(test_post, field), getattr(edited_post, field)
                    )

    def test_edit_redirects(self):
        """test if user is redirected to details page"""
        self.create_post(self.author_client)
        test_post = Post.objects.latest('pub_date')
        response = self.update_post(
            self.author_client, test_post.id
        )
        details_url = reverse('posts:post_detail', args=(test_post.id,))
        self.assertRedirects(response, details_url)

    def test_comment_redirects(self):
        """test if unauthorised user is redirected to login page"""
        self.create_post(self.author_client)
        test_post = Post.objects.latest('pub_date')
        add_comment_url = reverse(
            'posts:add_comment',
            kwargs={'post_id': test_post.id}
        )
        query_string = '?' + unquote(urlencode({'next': add_comment_url}))
        response = self.client.post(
            path=add_comment_url,
            data={'text': 'Hello there'},
            follow=True
        )
        self.assertRedirects(
            response=response,
            expected_url=urljoin(
                reverse(settings.LOGIN_URL),
                query_string
            ),
            status_code=HTTPStatus.FOUND,
            target_status_code=HTTPStatus.OK
        )

    def test_comment_created(self):
        """test if a comment left by an authorised user is created and shown"""
        self.create_post(self.author_client)
        test_post = Post.objects.latest('pub_date')
        test_text = 'Hello there'
        self.auth_client.post(
            path=reverse('posts:add_comment', args=(test_post.id,)),
            data={'text': test_text},
            follow=True
        )
        expected_comment = Comment.objects.latest('pub_date')
        expected_context = self.client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': test_post.id}
            )
        ).context
        self.assertTrue(expected_comment in test_post.comments.all())
        self.assertTrue(expected_comment in expected_context['comments'])
        self.assertEqual(expected_comment.text, test_text)
