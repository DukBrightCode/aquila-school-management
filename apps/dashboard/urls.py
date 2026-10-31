from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path('', views.dashboard_redirect, name='redirect'),
    path('admin/', views.admin_dashboard, name='admin'),
    path('teacher/', views.teacher_dashboard, name='teacher'),
    path('student/', views.student_dashboard, name='student'),
    # Assessment Type Management Routes
    path(
        'academics/assessment-types/',
        views.assessment_type_list,
        name='assessment_type_list',
    ),
    path(
        'academics/assessment-types/add/',
        views.assessment_type_create,
        name='assessment_type_create',
    ),
    path(
        'academics/assessment-types/<int:pk>/edit/',
        views.assessment_type_update,
        name='assessment_type_update',
    ),
    path(
        'academics/assessment-types/<int:pk>/delete/',
        views.assessment_type_delete,
        name='assessment_type_delete',
    ),


    # Grading Scale Management Routes
    path('academics/grading-scales/', views.grading_scale_list, name='grading_scale_list'),
    path('academics/grading-scales/add/', views.grading_scale_create, name='grading_scale_create'),
    path('academics/grading-scales/<int:pk>/edit/', views.grading_scale_update, name='grading_scale_update'),
    path('academics/grading-scales/<int:pk>/delete/', views.grading_scale_delete, name='grading_scale_delete'),

    # Predefined Remark Management Routes
    path('academics/remarks/', views.predefined_remark_list, name='predefined_remark_list'),
    path('academics/remarks/add/', views.predefined_remark_create, name='predefined_remark_create'),
    path('academics/remarks/<int:pk>/edit/', views.predefined_remark_update, name='predefined_remark_update'),
    path('academics/remarks/<int:pk>/delete/', views.predefined_remark_delete, name='predefined_remark_delete'),
    path('api/academics/remarks/', views.api_get_predefined_remarks, name='api_get_predefined_remarks'),

    # Teacher Student Management Routes
    path('teacher/students/', views.teacher_student_list, name='teacher_student_list'),
    path('teacher/students/add/', views.teacher_student_add, name='teacher_student_add'),
    path('teacher/students/<int:pk>/edit/', views.teacher_student_edit, name='teacher_student_edit'),
    path('teacher/class/<int:arm_id>/subjects/', views.teacher_class_subjects, name='teacher_class_subjects'),
]