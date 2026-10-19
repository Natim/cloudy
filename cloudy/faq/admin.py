from django.contrib import admin

from .models import Faq


class FaqAdmin(admin.ModelAdmin):
    search_fields = ("question", "answer")
    date_hierarchy = "post_date"
    list_display = ("question", "post_date")
    fields = ("question", "answer")


admin.site.register(Faq, FaqAdmin)
