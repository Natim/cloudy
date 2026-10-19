from django.contrib import admin

from .models import OrderInvoice, PaymentOrder


class PaymentOrderAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "user",
        "date",
        "state",
        "amount",
        "number_of_months",
        "sent",
        "invoice",
    )
    search_fields = (
        "uuid",
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
    )
    ordering = ("-date",)
    list_filter = (
        "state",
        "date",
    )

    @admin.display(description="Invoice sent", boolean=True)
    def sent(self, obj):
        if obj.invoice:
            return obj.invoice.sent
        return False


class OrderInvoiceAdmin(admin.ModelAdmin):
    list_display = ("uuid", "label", "created_date", "pdf", "sent")
    list_filter = ("created_date", "sent")


admin.site.register(PaymentOrder, PaymentOrderAdmin)
admin.site.register(OrderInvoice, OrderInvoiceAdmin)
