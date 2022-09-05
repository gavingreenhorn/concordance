import shutil
import tempfile
import io
from math import ceil
from http import HTTPStatus

from django.conf import settings
from django.shortcuts import reverse
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from PIL import Image

from posts.models import Post, Group, Comment, Follow
from posts.forms import PostForm


User = get_user_model()
# temporary location for media files to be stored at
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
# custom paginator page size effective during test runtime
TEST_POSTS_PER_PAGE = 7


class ViewTests:
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        """create required test objects"""
        # create one user that is not assigned as an author to any post
        cls.user_random = User.objects.create_user(username='homie')


@override_settings(
    MEDIA_ROOT=TEMP_MEDIA_ROOT,
    POSTS_PER_PAGE=TEST_POSTS_PER_PAGE)
class PostsViewTests(ViewTests, TestCase):
    @classmethod
    def setUpClass(cls):
        """generate required test objects and set up shared constants"""
        super().setUpClass()
        # define range and display count for test posts set
        cls.POST_COUNT = 25
        cls.TEST_RANGE = range(1, cls.POST_COUNT + 1)
        cls.COMMENTS_PER_POST = 5
        # create test images as byte strings
        cls.TEST_IMAGES = {
            1: cls.get_test_img('red'),
            2: cls.get_test_img('blue'),
        }
        # create test base
        cls.create_test_objects()
        Post.objects.bulk_create(cls.generate_dummy_posts())
        # assign test comments to posts
        for post in Post.objects.all():
            Comment.objects.bulk_create(cls.generate_dummy_comments(post))
        # resolve urls to constants
        cls.INDEX = reverse('posts:index')
        cls.CREATE = reverse('posts:post_create')
        cls.FOLLOW_INDEX = reverse('posts:follow_index')
        # separate pages for both test groups
        cls.GROUP_1 = reverse('posts:group_list', args=('test-group-1',))
        cls.GROUP_2 = reverse('posts:group_list', args=('test-group-2',))
        # separate pages for both test users
        cls.PROFILE_1 = reverse('posts:profile', args=('vato',))
        cls.PROFILE_2 = reverse('posts:profile', args=('loco',))
        # follow pages for test users
        cls.FOLLOW_1 = reverse('posts:profile_follow', args=('vato',))
        cls.FOLLOW_2 = reverse('posts:profile_follow', args=('loco',))
        # unfollow pages for test users
        cls.UNFOLLOW_1 = reverse('posts:profile_unfollow', args=('vato',))
        cls.UNFOLLOW_2 = reverse('posts:profile_unfollow', args=('loco',))
        # create ranges for posts expected to be found on different pages
        cls.POSTS_ENUMERATION = {
            cls.INDEX: cls.TEST_RANGE,
            cls.GROUP_1: range(0, cls.POST_COUNT, 2),
            cls.GROUP_2: range(1, cls.POST_COUNT + 1, 2),
            cls.PROFILE_1: range(0, cls.POST_COUNT, 2),
            cls.PROFILE_2: range(1, cls.POST_COUNT + 1, 2),
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

    @classmethod
    def generate_dummy_posts(cls) -> Post:
        for number in cls.TEST_RANGE:
            group, author = cls.fetch_object(number)
            # every other post gets assigned to one of two groups
            yield Post(
                text=f'test text {number}',
                group=group,
                author=author,
                image=cls.TEST_IMAGES[number % 2 + 1],
            )

    @classmethod
    def generate_dummy_comments(cls, post: Post) -> Comment:
        for number in range(1, cls.COMMENTS_PER_POST + 1):
            yield Comment(
                post=post,
                text=f'test comment {number}',
                author=cls.user_random,
            )

    @classmethod
    def fetch_expected_posts(cls) -> dict:
        expected_posts = {}
        for url in cls.POSTS_ENUMERATION:
            expected_posts.update(cls.fetch_expected_entries(url))
        return expected_posts

    @classmethod
    def fetch_expected_entries(cls, url) -> dict:
        posts_range = cls.POSTS_ENUMERATION[url]
        posts = Post.objects.filter(id__in=posts_range)
        first_page = posts[:settings.POSTS_PER_PAGE]
        count = posts.count()
        if count > settings.POSTS_PER_PAGE:
            last_page_num = ceil(count / settings.POSTS_PER_PAGE)
            last_page_count = count % settings.POSTS_PER_PAGE
            last_page_url = url + '?page=%s' % last_page_num
            last_page = posts[count - last_page_count:]
            return {
                url: first_page,
                last_page_url: last_page,
            }
        return {url: first_page}

    @staticmethod
    def create_test_objects() -> None:
        Group.objects.bulk_create([
            Group(
                title='test group 1',
                description='test description 1',
                slug='test-group-1',
            ),
            Group(
                title='test group 2',
                description='test description 2',
                slug='test-group-2',
            )
        ])
        User.objects.bulk_create([
            User(username='vato'),
            User(username='loco')
        ])

    @staticmethod
    def fetch_object(number, p=None) -> tuple:
        group = Group.objects.get(id=(number % 2 + 1))
        author = User.objects.get(id=(number % 2 + 2))
        if p:
            post = Post.objects.get(id=number)
            return post, group, author
        return group, author

    def setUp(self):
        """set up incoming data to test against"""

        self.auth_client = Client()
        self.auth_client.force_login(self.user_random)
        self.author_client = Client()

        self.urls = {
            self.INDEX: 'posts/index.html',
            self.GROUP_1: 'posts/group_list.html',
            self.GROUP_2: 'posts/group_list.html',
            self.CREATE: 'posts/post_form.html',
            self.PROFILE_1: 'posts/profile.html',
            self.PROFILE_2: 'posts/profile.html',
        }

        self.access_test_packets = [
            (self.INDEX, self.client, HTTPStatus.OK),
            (self.GROUP_1, self.client, HTTPStatus.OK),
            (self.GROUP_2, self.client, HTTPStatus.OK),
            (self.CREATE, self.client, HTTPStatus.FOUND),
            (self.CREATE, self.auth_client, HTTPStatus.OK),
            (self.PROFILE_1, self.client, HTTPStatus.OK),
            (self.PROFILE_2, self.client, HTTPStatus.OK)
        ]

        self.templates_test_packets = [
            (self.INDEX, self.client, 'posts/index.html'),
            (self.GROUP_1, self.client, 'posts/group_list.html'),
            (self.GROUP_2, self.client, 'posts/group_list.html'),
            (self.CREATE, self.client, 'users/login.html'),
            (self.CREATE, self.auth_client, 'posts/post_form.html'),
            (self.PROFILE_1, self.client, 'posts/profile.html'),
            (self.PROFILE_2, self.client, 'posts/profile.html')
        ]

        # set data for pagination test
        self.expected_posts = PostsViewTests.fetch_expected_posts()

    def follow(self, username) -> None:
        url = reverse('posts:profile_follow', args=(username,))
        self.auth_client.get(url)

    def unfollow(self, username) -> None:
        url = reverse('posts:profile_unfollow', args=(username,))
        self.auth_client.get(url)

    def tearDown(self) -> None:
        cache.clear()
        return super().tearDown()

    # test url resolution and templates rendering

    def test_urls_access(self):
        """test if different users has access to the pages"""
        for url, client, code in self.access_test_packets:
            with self.subTest(client=client, address=url):
                response = client.get(url)
                self.assertEqual(response.status_code, code)

    def test_urls_templates(self):
        """test if different users has access to the pages"""
        for url, client, template in self.templates_test_packets:
            with self.subTest(client=client, address=url):
                response = client.get(url, follow=True)
                self.assertTemplateUsed(response, template)

    def test_post_detail_tempalates(self):
        """test if detail pages for all dummy posts are present"""
        for number in self.TEST_RANGE:
            detail = reverse(
                'posts:post_detail',
                kwargs={'post_id': number},
            )
            with self.subTest(address=detail):
                response = self.client.get(detail)
                self.assertTemplateUsed(response, 'posts/post_detail.html')

    def test_post_edit_templates(self):
        """test if edit pages for all dummy posts are present"""
        for number in self.TEST_RANGE:
            _, author = PostsViewTests.fetch_object(number)
            self.author_client.force_login(author)
            edit = reverse(
                'posts:post_edit',
                kwargs={'pk': number},
            )
            with self.subTest(address=edit):
                response = self.author_client.get(edit)
                self.assertTemplateUsed(response, 'posts/post_form.html')

    # testing context, pagination and cache

    def test_context_and_pagination(self):
        """testing page contents and posts per-page spread"""
        for address, values in self.expected_posts.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                qs = response.context['page_obj'].object_list
                self.assertQuerysetEqual(qs, values, transform=lambda x: x)

    def test_post_details_context(self):
        """test if correct post is rendered"""
        for number in self.TEST_RANGE:
            post, *_ = PostsViewTests.fetch_object(number, p=1)
            comments = post.comments.all()
            url = reverse(
                'posts:post_detail',
                kwargs={'post_id': post.id},
            )
            response = self.client.get(url)
            context_post = response.context['post']
            context_comments = response.context['comments']
            self.assertEqual(context_post, post)
            self.assertQuerysetEqual(
                context_comments, comments,
                transform=lambda x: x, ordered=False)

    def test_post_edit_context(self):
        """test type of fields in rendered form"""
        for i in self.TEST_RANGE:
            post, _, author = PostsViewTests.fetch_object(i, p=1)
            self.author_client.force_login(author)
            url = reverse(
                'posts:post_edit',
                kwargs={'pk': post.pk},
            )
            color = 'red' if post.id % 2 == 1 else 'blue'
            # create a form to test against
            expected_form = PostForm(initial={
                'text': post.text,
                'group': post.group,
                'file': f'concordance/{color}.jpeg'
            })
            response = self.author_client.get(url)
            context_form = response.context['form']
            # iterate over tested form's fields and compare with expected types
            for field in context_form.fields:
                self.assertEqual(
                    context_form.instance._meta.get_field(field),
                    expected_form.instance._meta.get_field(field)
                )

    def test_index_cached(self):
        """test if index page content is cached"""
        response = self.client.get(self.INDEX)
        test_post = response.context['page_obj'].object_list[-1]
        test_post_as_bytes = test_post.text.encode('utf-8')
        Post.objects.get(id=test_post.id).delete()
        # test if deleted post remains on the page
        response = self.client.get(self.INDEX)
        self.assertIn(test_post_as_bytes, response.content)
        # test if a post is removed from the page after cache flush
        cache.clear()
        response = self.client.get(self.INDEX)
        self.assertNotIn(test_post_as_bytes, response.content)

    # testing post presence

    def test_new_post_presence(self):
        """test different views for newly created post's presence"""
        new_group = Group.objects.create(
            title='new-group',
            slug='new-group',
            description='something descriptive')
        new_author = User.objects.create(username='danger-pwrs')
        new_post = Post.objects.create(
            text='Owls are not what they seem',
            group=new_group,
            author=new_author
        )
        self.author_client.force_login(new_author)
        group_url = reverse(
            'posts:group_list',
            kwargs={'slug': 'new-group'},
        )
        profile_url = reverse(
            'posts:profile',
            kwargs={'username': 'danger-pwrs'},
        )
        for url in (self.INDEX, group_url, profile_url):
            with self.subTest(address=url):
                response = self.author_client.get(url)
                qs = response.context['page_obj'].object_list
                self.assertTrue(new_post in qs)

    # testing follows

    def test_follow(self):
        """test that authorised user can follow"""
        self.follow('vato')
        self.assertTrue(
            Follow.objects.filter(user=self.user_random).exists()
        )

    def test_unfollow(self):
        """test that unfollowing removes db object"""
        author = User.objects.get(username='vato')
        Follow.objects.create(user=self.user_random, author=author)
        self.unfollow(author.username)
        self.assertFalse(
            Follow.objects.filter(user=self.user_random).exists()
        )

    def test_follow_count(self):
        """test that Follow objects are incremented"""
        self.follow('vato')
        self.follow('loco')
        followings = self.user_random.follower.all().count()
        self.assertEqual(followings, 2)

    def test_follows_rendered(self):
        """test if only followed author's posts are displayed"""
        for username in ('vato', 'loco'):
            with self.subTest(author=username):
                self.follow(username)
                response = self.auth_client.get(self.FOLLOW_INDEX)
                page = response.context['page_obj']
                received_posts = page.paginator.object_list
                expected_posts = Post.objects.filter(
                    author=User.objects.get(username=username)
                )
                self.assertQuerysetEqual(
                    received_posts,
                    expected_posts,
                    transform=lambda x: x
                )
                self.unfollow(username)

    def test_follows_posts_increments(self):
        """test if only followed author's posts are displayed"""
        self.follow('vato')
        response = self.auth_client.get(self.FOLLOW_INDEX)
        page = response.context['page_obj']
        posts_count = len(page.paginator.object_list)
        # followed author leaves a new post
        self.author_client.force_login(User.objects.get(username='vato'))
        self.author_client.post(self.CREATE, data={'text': 'new post'})
        # check if a new post is added to follows page
        response = self.auth_client.get(self.FOLLOW_INDEX)
        page = response.context['page_obj']
        self.assertEqual(len(page.paginator.object_list), posts_count + 1)
