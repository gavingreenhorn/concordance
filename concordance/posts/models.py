from django.db import models
from django.db.models import F, Q
from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from core.models import CreatedModel


User = get_user_model()


class Post(CreatedModel):
    text = models.TextField(
        'Post text',
        help_text='Text content of the post'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Author',
    )
    group = models.ForeignKey(
        'Group',
        on_delete=models.SET_NULL,
        related_name='posts',
        null=True,
        blank=True,
        verbose_name='Group',
        help_text='Associated group',
    )
    image = models.ImageField(
        'Image',
        upload_to='posts/',
        blank=True,
        help_text='Image file'
    )

    class Meta:
        ordering = ['-pub_date']

    def __str__(self):
        snippet = self.text if len(self.text) <= 50 else self.text[:47] + '...'
        timestamp = self.pub_date.strftime('%d/%m/%Y %H:%M')
        return (f'{self.author} ({timestamp}): "{snippet}"')

    def get_absolute_url(self):
        return reverse('posts:post_detail', args=(self.id,))


class Comment(CreatedModel):
    post = models.ForeignKey(
        Post,
        related_name='comments',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        related_name='comments',
        on_delete=models.CASCADE
    )
    text = models.TextField(
        'Comment text',
        help_text='Text content of the comment',
        default=None
    )


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=30, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('posts:group_list', args=(self.slug,))


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "author"], name="unique_follow"
            ),
            models.CheckConstraint(
                check=~Q(user=F('author')), name="don't follow yourself"
            )
        ]
