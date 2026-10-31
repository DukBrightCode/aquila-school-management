from django.contrib import admin
from .models import FeeStructure, Invoice, Payment


@admin.register(FeeStructure)
class FeeStructureAdmin(admin.ModelAdmin):
    list_display = ("class_level", "term", "fee_type", "amount")
    list_filter = ("class_level", "term")
    search_fields = ("fee_type", "class_level__name")


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ("payment_date",)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "student", "term", "total_amount", "amount_paid", "status", "generated_at")
    list_filter = ("status", "term")
    search_fields = ("student__admission_number", "student__user__first_name", "student__user__last_name")
    inlines = [PaymentInline]
    readonly_fields = ("generated_at",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "invoice", "amount", "payment_date", "payment_method", "reference_number")
    list_filter = ("payment_method", "payment_date")
    search_fields = ("reference_number", "invoice__student__admission_number")