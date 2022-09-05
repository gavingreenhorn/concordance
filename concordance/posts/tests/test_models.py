from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from freezegun import freeze_time

from posts.models import Post, Group


User = get_user_model()


class PostModelTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.freezer = freeze_time(timezone.now())
        cls.freezer.start()
        cls.group = Group.objects.create(
            title='Test group',
            slug='Test_slug',
            description='Test description',
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=User.objects.create_user(username='wacko wacko'),
            group=cls.group,
        )
        field_names = ['text', 'pub_date', 'author', 'group', 'image']
        verbose_names = [
            'Post text', 'Object creation date',
            'Author', 'Group', 'Image'
        ]
        cls.EXPECTED_LABELS = dict(zip(field_names, verbose_names))
        cls.EXPECTED_HELP_TEXTS = {
            'text': 'Text content of the post',
            'group': 'Associated group',
            'image': 'Image file',
        }

    @classmethod
    def tearDownClass(cls):
        cls.freezer.stop()
        cache.clear()
        super().tearDownClass()

    @classmethod
    def get_actual_state(cls):
        """helper method to iterate over test object's fields"""
        for field in cls.post._meta.fields:
            if not field.primary_key:
                yield field.name, field.verbose_name, field.help_text

    def test_fields_meta(self):
        """test fields verbose names and help texts"""
        for field, name, text in self.get_actual_state():
            self.subtest_labels(field, name)
            if text:
                self.subtest_help_texts(field, text)

    def subtest_labels(self, field, name):
        """fields' verbose_name == expected"""
        with self.subTest(field=field):
            self.assertEqual(
                name, self.EXPECTED_LABELS[field]
            )

    def subtest_help_texts(self, field, text):
        """fields' help_text == expected."""
        with self.subTest(field=field):
            self.assertEqual(
                text, self.EXPECTED_HELP_TEXTS[field]
            )

    def test_object_names(self):
        """objects name == expected."""
        time = timezone.now().strftime('%d/%m/%Y %H:%M')
        expected_names = {
            self.post: f'wacko wacko ({time}): "Test text"',
            self.group: 'Test group',
        }
        for model_object, name in expected_names.items():
            with self.subTest(object=(str(model_object))):
                self.assertEqual(str(model_object), name)

    def test_abs_urls(self):
        """test objects' absolute url"""
        expected_abs_urls = {
            self.post: f'/posts/{self.post.id}/',
            self.group: f'/group/{self.group.slug}/',
        }
        for model_object, url in expected_abs_urls.items():
            with self.subTest(object=(str(model_object))):
                self.assertEqual(model_object.get_absolute_url(), url)
