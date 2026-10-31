from django.urls import path
from . import views

app_name = "finance"

urlpatterns = [
    path("invoices/", views.invoice_list, name="invoice_list"),
    path("invoices/<int:pk>/", views.invoice_detail, name="invoice_detail"),
    path("invoices/<int:pk>/pay/", views.record_payment, name="record_payment"),
    path("my-invoices/", views.student_invoice_list, name="student_invoice_list"),
    path("fee-structures/", views.fee_structure_list, name="fee_structure_list"),
]