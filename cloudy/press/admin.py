from django.contrib import admin

from cloudy.press.models import Article


class ArticleAdmin(admin.ModelAdmin):
    search_fields = ("title", "reference")
    date_hierarchy = "date"
    list_display = ("title", "date")
    fields = ("date", "title", "reference", "link")


admin.site.register(Article, ArticleAdmin)
