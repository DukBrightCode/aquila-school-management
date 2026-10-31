from django.db import transaction
from django.db.models import F, Q, Sum
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone

from apps.school_structure.models import ClassArm
from apps.accounts.permissions import role_required
from apps.students.models import Student
from .models import Book, BookIssue
from .forms import BookForm

def check_librarian(user):
    return user.is_authenticated and user.is_librarian()


@role_required("ADMIN", "LIBRARIAN")
def book_list(request):
    query = request.GET.get("q", "").strip()
    books = Book.objects.all()

    # Calculate overall database stats
    total_titles = books.count()
    total_copies = books.aggregate(total=Sum("total_copies"))["total"] or 0
    total_available_copies = books.aggregate(total=Sum("available_copies"))["total"] or 0
    total_issued_copies = BookIssue.objects.filter(return_date__isnull=True).count()

    if query:
        books = books.filter(
            Q(title__icontains=query) |
            Q(author__icontains=query) |
            Q(isbn__icontains=query)
        )

    issues = BookIssue.objects.filter(return_date__isnull=True).select_related("book", "student__user")
    students = Student.objects.select_related(
        "user", 
        "current_class_level", 
        "current_class_arm"
    ).all()

    # Query all class arms from database
    class_arms = ClassArm.objects.all()

    return render(
        request,
        "library/book_list.html",
        {
            "books": books,
            "issues": issues,
            "students": students,
            "class_arms": class_arms,  # Pass class arms to template
            "search_query": query,
            "stats": {
                "total_titles": total_titles,
                "total_copies": total_copies,
                "total_available_copies": total_available_copies,
                "total_issued_copies": total_issued_copies,
            },
        },
    )
    
@role_required("ADMIN", "LIBRARIAN")
def issue_book(request, book_id):
    if request.method == "POST":
        student_id = request.POST.get("student_id") or request.POST.get("student")
        due_date = request.POST.get("due_date")

        with transaction.atomic():
            book = get_object_or_404(Book.objects.select_for_update(), pk=book_id)
            if book.available_copies <= 0:
                messages.error(request, "No available copies left to issue.")
                return redirect("library:book_list")

            student = get_object_or_404(Student, pk=student_id)
            
            BookIssue.objects.create(
                book=book,
                student=student,
                due_date=due_date,
            )
            
            book.available_copies = F("available_copies") - 1
            book.save()

        messages.success(request, f"Successfully issued '{book.title}' to {student}.")

    # Redirect GET requests back to book list so no missing template error occurs
    return redirect("library:book_list")


@role_required("ADMIN" , "LIBRARIAN")
def return_book(request, issue_id):
    if request.method == "POST":
        with transaction.atomic():
            issue = get_object_or_404(
                BookIssue.objects.select_related("book").select_for_update(), 
                pk=issue_id, 
                return_date__isnull=True
            )
            issue.return_date = timezone.now().date()
            issue.save()

            book = issue.book
            book.available_copies = F("available_copies") + 1
            book.save()

        messages.success(request, f"Successfully returned '{book.title}'.")
    return redirect("library:book_list")


@login_required
@user_passes_test(check_librarian)
def add_book(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            book = form.save(commit=False)
            book.available_copies = book.total_copies
            book.save()
            return redirect('library:book_list')
    else:
        form = BookForm()
    return render(request, 'library/add_book.html', {'form': form})


@login_required
@user_passes_test(check_librarian)
def delete_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        book.delete()
    return redirect('library:book_list')

@login_required
def update_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            updated_book = form.save(commit=False)
            # If total copies is reduced below available copies, adjust available copies safely
            if updated_book.available_copies > updated_book.total_copies:
                updated_book.available_copies = updated_book.total_copies
            updated_book.save()
            return redirect('library:book_list')
    else:
        form = BookForm(instance=book)
    
    return render(request, 'library/add_book.html', {'form': form, 'is_edit': True})