from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Sum
from apps.school_structure.models import Term
from apps.students.models import Student
from apps.finance.models import FeeStructure, Invoice


class Command(BaseCommand):
    help = "Generates term invoices for students based on their current class level fee structure."

    def add_arguments(self, parser):
        parser.add_argument(
            "--term-id",
            type=int,
            help="ID of the Term to generate invoices for. If omitted, uses the current active term.",
        )

    def handle(self, *args, **options):
        term_id = options.get("term_id")

        if term_id:
            try:
                term = Term.objects.get(pk=term_id)
            except Term.DoesNotExist:
                raise CommandError(f"Term with ID {term_id} does not exist.")
        else:
            term = Term.objects.filter(is_current=True).first()
            if not term:
                raise CommandError("No current active Term found. Please specify --term-id.")

        self.stdout.write(self.style.NOTICE(f"Generating invoices for term: {term}"))

        students = Student.objects.select_related("current_class_level").all()
        created_count = 0
        skipped_count = 0

        with transaction.atomic():
            for student in students:
                # Idempotency check: Skip if an invoice already exists for this term
                if Invoice.objects.filter(student=student, term=term).exists():
                    skipped_count += 1
                    continue

                # Fetch all fee components for student's CURRENT class level
                fee_total = FeeStructure.objects.filter(
                    class_level=student.current_class_level,
                    term=term
                ).aggregate(total=Sum("amount"))["total"] or Decimal("0.00")

                Invoice.objects.create(
                    student=student,
                    term=term,
                    total_amount=fee_total,
                    amount_paid=Decimal("0.00"),
                    status="PENDING",
                )
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully generated {created_count} invoices. {skipped_count} skipped (already exists)."
            )
        )