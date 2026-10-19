from django.contrib import admin

from cloudy.notifications.models import Notice, NoticeSetting, NoticeType


@admin.register(NoticeType)
class NoticeTypeAdmin(admin.ModelAdmin):
    list_display = ("label", "display", "default")


@admin.register(NoticeSetting)
class NoticeSettingAdmin(admin.ModelAdmin):
    list_display = ("user", "notice_type", "medium", "send")


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("recipient", "notice_type", "unseen", "added")
    list_filter = ("unseen", "notice_type")
