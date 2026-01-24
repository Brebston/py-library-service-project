from django.db import models

from books.models import Book
from users.models import User


class Borrowing(models.Model):
    borrow_date = models.DateField()
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="records")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="records")

    def __str__(self):
        return f"Book: {Book.objects.get().title}, Borrow date: {self.borrow_date}"
