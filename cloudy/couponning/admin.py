from django.contrib import admin

from cloudy.couponning.models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ("code", "reduc_type", "discount_value", "validity_end", "used")
