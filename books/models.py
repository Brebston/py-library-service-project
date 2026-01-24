from django.db import models


class Book(models.Model):
    class Cover(models.TextChoices):
        HARD = "HARD", "hard"
        SOFT = "SOFT", "soft"

    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover = models.CharField(max_length=4, choices=Cover.choices, default=Cover.HARD)
    inventory = models.PositiveIntegerField()
    daily_fee = models.DecimalField(decimal_places=2, max_digits=10)

    def __str__(self):
        return f"Book: {self.title}, author: {self.author}"
