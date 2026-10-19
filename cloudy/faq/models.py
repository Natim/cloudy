from django.db import models
from django.urls import reverse


class Faq(models.Model):
    """Stores FAQS"""

    question = models.CharField(max_length=400)
    answer = models.TextField()
    post_date = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        return self.question

    def get_absolute_url(self):
        return reverse("faq:details", args=[self.pk])
