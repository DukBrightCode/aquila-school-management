from django.urls import path
from . import views

app_name = "academics"

urlpatterns = [
    path("score-entry/", views.score_entry, name="score_entry"),
    path("score-entry/subjects/", views.get_class_subjects, name="get_class_subjects"),
    path("score-entry/data/", views.score_entry_data, name="score_entry_data"),
    path("score-entry/save/", views.score_entry_save, name="score_entry_save"),
    # Report card URLs - more specific patterns first
    path("report-card/<int:student_id>/<int:term_id>/<str:exam_type>/<str:report_type>/", views.report_card, name="report_card"),
    path("report-card/<int:student_id>/<int:term_id>/<str:exam_type>/", views.report_card, name="report_card_with_exam"),
    path("report-card/<int:student_id>/<int:term_id>/", views.report_card, name="report_card_legacy"),
    path("report-card/<int:student_id>/<int:term_id>/<str:exam_type>/<str:report_type>/pdf/", views.generate_report_card_pdf, name="generate_report_card_pdf"),
    path("report-card/<int:student_id>/<int:term_id>/<str:exam_type>/pdf/", views.generate_report_card_pdf, name="generate_report_card_pdf_with_exam"),
    path("report-card/<int:student_id>/<int:term_id>/pdf/", views.generate_report_card_pdf, name="generate_report_card_pdf_legacy"),
    path("report-card/<int:student_id>/<int:term_id>/email/", views.send_single_result_email, name="send_single_result_email"),
    path("report-cards/", views.report_card_list, name="report_card_list"),
    path("class-results/<int:class_arm_id>/<int:term_id>/", views.class_results_summary, name="class_results_summary"),
    path("class-results/<int:class_arm_id>/<int:term_id>/email-all/", views.send_class_result_emails, name="send_class_result_emails"),
    path(
        'report-card/<int:student_id>/<int:term_id>/email/',
        views.send_single_result_email,
        name='send_result_email'
    ),
    path("skills/rate/", views.rate_skills, name="rate_skills"),
    
    path("class-results/<int:class_arm_id>/<int:term_id>/<str:exam_type>/pdf/",
         views.class_report_cards_pdf, name="class_report_cards_pdf"),
    path("release/<int:class_arm_id>/<int:term_id>/<str:exam_type>/",
         views.toggle_result_release, name="toggle_result_release"),
    path("skills/class/", views.class_skill_ratings, name="class_skill_ratings"),
    path("remarks/class/", views.class_remarks, name="class_remarks"),
    path("streams/class/", views.class_streams, name="class_streams"),
    path("position/<int:class_arm_id>/toggle/", views.toggle_class_position, name="toggle_class_position"),
]
    
