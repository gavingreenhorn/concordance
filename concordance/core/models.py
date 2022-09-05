from django.db import models


class CreatedModel(models.Model):
    pub_date = models.DateTimeField(
        'Object creation date',
        auto_now_add=True,
        db_index=True
    )

    class Meta:
        abstract = True
