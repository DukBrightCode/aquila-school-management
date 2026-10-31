from decimal import Decimal
from django.db import models


class FeeStructure(models.Model):
    class_level = models.ForeignKey(
        "school_structure.ClassLevel",
        on_delete=models.CASCADE,
        related_name="fee_structures",
    )
    term = models.ForeignKey(
        "school_structure.Term",
        on_delete=models.CASCADE,
        related_name="fee_structures",
    )
    fee_type = models.CharField(max_length=100, help_text="e.g. Tuition, Books, Uniform")
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["class_level", "term", "fee_type"]
        unique_together = ["class_level", "term", "fee_type"]

    def __str__(self):
        return f"{self.class_level} - {self.term} - {self.fee_type}: ₦{self.amount}"


class Invoice(models.Model):
    STATUS_CHOICES = (
        ("PENDING", "Pending"),
        ("PARTIAL", "Partial"),
        ("PAID", "Paid"),
    )

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    term = models.ForeignKey(
        "school_structure.Term",
        on_delete=models.CASCADE,
        related_name="invoices",
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PENDING")
    generated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-generated_at"]
        unique_together = ["student", "term"]

    def __str__(self):
        return f"Invoice #{self.id} - {self.student} ({self.term})"

    @property
    def balance_due(self):
        return max(Decimal("0.00"), self.total_amount - self.amount_paid)

    def update_status(self):
        """Recalculates amount_paid and updates status accordingly."""
        total_payments = self.payments.aggregate(
            total=models.Sum("amount")
        )["total"] or Decimal("0.00")
        
        self.amount_paid = total_payments
        if self.amount_paid == Decimal("0.00"):
            self.status = "PENDING"
        elif self.amount_paid < self.total_amount:
            self.status = "PARTIAL"
        else:
            self.status = "PAID"
        self.save()


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ("CASH", "Cash"),
        ("BANK_TRANSFER", "Bank Transfer"),
        ("POS", "POS / Card"),
        ("CHEQUE", "Cheque"),
        ("OTHER", "Other"),
    )

    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="BANK_TRANSFER",
    )
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Transaction reference number or receipt ID",
    )

    class Meta:
        ordering = ["-payment_date", "-id"]

    def __str__(self):
        return f"Payment ₦{self.amount} for Invoice #{self.invoice_id}"