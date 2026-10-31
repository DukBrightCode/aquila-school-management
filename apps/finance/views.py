from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from apps.accounts.permissions import role_required
from apps.school_structure.models import Term
from apps.students.models import Student
from .models import Invoice, Payment, FeeStructure
from .forms import PaymentForm


@role_required("ADMIN")
def invoice_list(request):
    term_id = request.GET.get("term")
    status = request.GET.get("status")

    invoices = Invoice.objects.select_related("student__user", "student__current_class_level", "term").all()

    if term_id:
        invoices = invoices.filter(term_id=term_id)
    if status:
        invoices = invoices.filter(status=status)

    terms = Term.objects.select_related("session").all()

    context = {
        "invoices": invoices,
        "terms": terms,
        "selected_term": term_id,
        "selected_status": status,
        "status_choices": Invoice.STATUS_CHOICES,
    }
    return render(request, "finance/invoice_list.html", context)


@role_required("ADMIN")
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            "student__user", "student__current_class_level", "student__current_class_arm", "term"
        ),
        pk=pk,
    )
    payments = invoice.payments.all().order_by("-payment_date", "-id")
    form = PaymentForm()

    context = {
        "invoice": invoice,
        "payments": payments,
        "form": form,
    }
    return render(request, "finance/invoice_detail.html", context)


@role_required("ADMIN")
def record_payment(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.invoice = invoice
            payment.save()

            # Recalculate amount_paid and update invoice status
            invoice.update_status()

            messages.success(request, f"Payment of ₦{payment.amount} recorded successfully.")
            return redirect("finance:invoice_detail", pk=invoice.pk)
        else:
            messages.error(request, "Failed to record payment. Please check form errors.")
            payments = invoice.payments.all().order_by("-payment_date", "-id")
            return render(request, "finance/invoice_detail.html", {
                "invoice": invoice,
                "payments": payments,
                "form": form,
            })

    return redirect("finance:invoice_detail", pk=invoice.pk)


@role_required("STUDENT")
def student_invoice_list(request):
    """
    Student view to see only their own invoices.
    """
    student = get_object_or_404(Student, user=request.user)
    term_id = request.GET.get("term")
    status = request.GET.get("status")

    invoices = Invoice.objects.filter(
        student=student
    ).select_related("student__user", "student__current_class_level", "term")

    if term_id:
        invoices = invoices.filter(term_id=term_id)
    if status:
        invoices = invoices.filter(status=status)

    terms = Term.objects.select_related("session").all()

    context = {
        "invoices": invoices,
        "terms": terms,
        "selected_term": term_id,
        "selected_status": status,
        "status_choices": Invoice.STATUS_CHOICES,
        "student": student,
    }
    return render(request, "finance/student_invoice_list.html", context)


@role_required("ADMIN")
def fee_structure_list(request):
    """
    Admin view to manage fee structures.
    """
    fee_structures = FeeStructure.objects.select_related("class_level", "term").all()

    context = {
        "fee_structures": fee_structures,
    }
    return render(request, "finance/fee_structure_list.html", context)