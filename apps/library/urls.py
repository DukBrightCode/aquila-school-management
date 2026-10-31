from django.urls import path
from . import views

app_name = "library"

urlpatterns = [
    path("", views.book_list, name="book_list"),
    path("add/", views.add_book, name="add_book"),
    path("edit/<int:book_id>/", views.update_book, name="update_book"),  # <-- Edit route
    path("delete/<int:book_id>/", views.delete_book, name="delete_book"),
    path("issue/<int:book_id>/", views.issue_book, name="issue_book"),
    path("return/<int:issue_id>/", views.return_book, name="return_book"),
]