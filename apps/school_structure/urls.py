from django.urls import path
from . import views

app_name = "school_structure"

urlpatterns = [
    path('sessions/', views.academic_session_list, name='session_list'),
    path('terms/', views.term_list, name='term_list'),
    path('class-levels/', views.class_level_list, name='class_level_list'),
    path('class-arms/', views.class_arm_list, name='class_arm_list'),
    path('subjects/', views.subject_list, name='subject_list'),
    path('class-subjects/', views.class_subject_list, name='class_subject_list'),
    path('manage-class-subjects/', views.manage_class_subjects, name='manage_class_subjects'),
    path('manage-class-subjects/<int:class_arm_id>/', views.manage_class_subjects, name='manage_class_subjects'),
]
