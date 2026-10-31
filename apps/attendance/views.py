import json
from datetime import datetime
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.dateparse import parse_date
from django.views import View
from apps.accounts.permissions import TeacherRequiredMixin, role_required
from apps.school_structure.models import ClassArm
from apps.staff.models import Teacher
from apps.students.models import Student
from .models import AttendanceRecord, DailyAttendance


class MarkAttendanceView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        assigned_arms = ClassArm.objects.none()
        teacher = None

        if user.role == "TEACHER":
            try:
                teacher = user.teacher_profile
                assigned_arms = teacher.class_arms_assigned.all()
            except Teacher.DoesNotExist:
                assigned_arms = ClassArm.objects.none()
        elif user.role == "ADMIN" or user.is_superuser:
            assigned_arms = ClassArm.objects.all()

        selected_arm_id = request.GET.get("class_arm")
        selected_date_str = request.GET.get("date", datetime.now().strftime("%Y-%m-%d"))

        students = []
        existing_records = {}
        selected_arm = None

        if selected_arm_id:
            selected_arm = get_object_or_404(assigned_arms, pk=selected_arm_id)
            students = Student.objects.filter(current_class_arm=selected_arm).select_related("user")

            daily_att = DailyAttendance.objects.filter(class_arm=selected_arm, date=selected_date_str).first()
            if daily_att:
                existing_records = {
                    rec.student_id: rec.status
                    for rec in AttendanceRecord.objects.filter(daily_attendance=daily_att)
                }

        context = {
            "class_arms": assigned_arms,
            "selected_arm": selected_arm,
            "selected_arm_id": int(selected_arm_id) if selected_arm_id else "",
            "selected_date": selected_date_str,
            "students": students,
            "existing_records": existing_records,
        }
        return render(request, "attendance/mark_attendance.html", context)

    def post(self, request):
        if request.content_type != "application/json":
            return JsonResponse({"status": "error", "message": "Invalid Content-Type. Expected application/json."}, status=400)

        try:
            data = json.loads(request.body)
            class_arm_id = data.get("class_arm_id")
            date_str = data.get("date")
            records_data = data.get("records", [])

            if not class_arm_id or not date_str:
                return JsonResponse({"status": "error", "message": "Missing class_arm_id or date."}, status=400)

            parsed_date = parse_date(date_str)
            if not parsed_date:
                return JsonResponse({"status": "error", "message": "Invalid date format."}, status=400)

            user = request.user
            if user.role == "TEACHER":
                teacher = get_object_or_404(Teacher, user=user)
                if not teacher.class_arms_assigned.filter(pk=class_arm_id).exists():
                    return JsonResponse({"status": "error", "message": "You are not authorized to mark attendance for this class arm."}, status=403)
            elif user.role != "ADMIN" and not user.is_superuser:
                return JsonResponse({"status": "error", "message": "Permission denied."}, status=403)
            else:
                teacher = getattr(user, "teacher_profile", None)

            class_arm = get_object_or_404(ClassArm, pk=class_arm_id)

            with transaction.atomic():
                daily_att, created = DailyAttendance.objects.get_or_create(
                    class_arm=class_arm,
                    date=parsed_date,
                    defaults={"marked_by": teacher},
                )
                if not created and teacher:
                    daily_att.marked_by = teacher
                    daily_att.save()

                for item in records_data:
                    student_id = item.get("student_id")
                    status = item.get("status", "PRESENT")
                    AttendanceRecord.objects.update_or_create(
                        daily_attendance=daily_att,
                        student_id=student_id,
                        defaults={"status": status},
                    )

            return JsonResponse({"status": "success", "message": "Attendance successfully saved!"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


class AttendanceSummaryView(LoginRequiredMixin, View):
    def get(self, request):
        class_arm_id = request.GET.get("class_arm")
        student_id = request.GET.get("student_id")
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        class_arms = ClassArm.objects.all()
        summary_data = []
        selected_student = None

        # Handle individual student view
        if student_id:
            selected_student = get_object_or_404(Student, pk=student_id)
            class_arm_id = selected_student.current_class_arm.id if selected_student.current_class_arm else None

        if class_arm_id and start_date and end_date:
            # If student_id is provided, filter for that specific student only
            if student_id:
                students = Student.objects.filter(pk=student_id).select_related("user")
            else:
                students = Student.objects.filter(current_class_arm_id=class_arm_id).select_related("user")

            records = AttendanceRecord.objects.filter(
                daily_attendance__class_arm_id=class_arm_id,
                daily_attendance__date__range=[start_date, end_date],
            )

            for student in students:
                st_records = records.filter(student=student)
                total_days = st_records.count()
                present_days = st_records.filter(status="PRESENT").count()
                late_days = st_records.filter(status="LATE").count()
                absent_days = st_records.filter(status="ABSENT").count()

                percentage = round(((present_days + late_days) / total_days * 100), 2) if total_days > 0 else 0

                summary_data.append({
                    "student": student,
                    "total_days": total_days,
                    "present_days": present_days,
                    "late_days": late_days,
                    "absent_days": absent_days,
                    "percentage": percentage,
                })

        context = {
            "class_arms": class_arms,
            "selected_arm_id": int(class_arm_id) if class_arm_id else "",
            "selected_student": selected_student,
            "start_date": start_date or "",
            "end_date": end_date or "",
            "summary_data": summary_data,
        }
        return render(request, "attendance/summary.html", context)


@login_required
@role_required("ADMIN")
def attendance_records_list(request):
    """
    Admin view to manage attendance records directly.
    """
    from .models import AttendanceRecord
    records = AttendanceRecord.objects.select_related(
        "student__user", "daily_attendance__class_arm", "daily_attendance"
    ).all()

    context = {
        "records": records,
    }
    return render(request, "attendance/records_list.html", context)