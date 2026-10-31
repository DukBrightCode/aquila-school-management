from django.contrib import admin
from .models import Book, BookIssue


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "isbn", "total_copies", "available_copies")
    search_fields = ("title", "author", "isbn")


@admin.register(BookIssue)
class BookIssueAdmin(admin.ModelAdmin):
    list_display = ("book", "student", "issue_date", "due_date", "return_date")
    list_filter = ("issue_date", "due_date", "return_date")
    search_fields = ("book__title", "student__admission_number")