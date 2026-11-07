
from datetime import datetime
from django.shortcuts import get_object_or_404, redirect, render
from django.http import Http404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, Count, Q, DecimalField, F
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from .forms import AssessmentTypeForm
from .forms import GradingScaleForm
from .forms import PredefinedRemarkForm
from django.contrib import messages

from apps.accounts.permissions import role_required
from apps.school_structure.models import Term, ClassLevel, ClassArm, Subject
from apps.students.models import Student
from apps.students.teacher_forms import TeacherStudentForm
from apps.staff.models import Teacher
from apps.attendance.models import AttendanceRecord, DailyAttendance
from apps.academics.models import Score, AssessmentType, PredefinedRemark
from apps.finance.models import Invoice
from apps.timetable.models import TimetableSlot
from apps.communication.models import Announcement
from apps.academics.models import GradingScale, ClassSubjectTeacher


def get_greeting(user):
    """Returns a time-aware personalized greeting and display name."""
    now_hour = datetime.now().hour
    if now_hour < 12:
        time_greeting = "Good morning"
    elif now_hour < 17:
        time_greeting = "Good afternoon"
    else:
        time_greeting = "Good evening"
    
    display_name = user.get_full_name() or user.username
    return f"{time_greeting}, {display_name}"


@login_required
def dashboard_redirect(request):
    """
    Redirects authenticated users to their respective role-based dashboard 
    with explicit route validation.
    """
    role = getattr(request.user, 'role', None)
    
    if role == 'ADMIN':
        return redirect('dashboard:admin')
    elif role == 'TEACHER':
        return redirect('dashboard:teacher')
    elif role == 'STUDENT':
        return redirect('dashboard:student')
    elif role == 'LIBRARIAN':
        return redirect('library:book_list')  # Routes to your library dashboard
        
    # Fallback for users with unassigned or unknown roles
    return redirect('core:home')


@role_required("ADMIN")
def admin_dashboard(request):
    today = datetime.now().date()
    current_term = Term.objects.filter(is_current=True).first()

    # Core Counts
    total_students = Student.objects.count()
    total_staff = Teacher.objects.count()

    # Today's Attendance Rate Across All Class Arms
    today_records = AttendanceRecord.objects.filter(daily_attendance__date=today)
    total_marked = today_records.count()
    present_count = today_records.filter(status='PRESENT').count()
    attendance_rate = round((present_count / total_marked * 100), 1) if total_marked > 0 else 0.0

    # Outstanding Fees Total (non-PAID invoices)
    zero_dec = DecimalField(max_digits=12, decimal_places=2)
    unpaid_invoices = Invoice.objects.exclude(status='PAID')
    outstanding_fees_total = unpaid_invoices.aggregate(
        total=Coalesce(Sum(F('total_amount') - F('amount_paid'), output_field=zero_dec), 0, output_field=zero_dec)
    )['total']

    # Top 10 Students with Outstanding Balances > 0
    debtors_raw = Invoice.objects.exclude(status='PAID').annotate(
        balance=F('total_amount') - F('amount_paid')
    ).filter(balance__gt=0).order_by('-balance')[:10]
    
    top_debtors = []
    for inv in debtors_raw:
        top_debtors.append({
            'student_name': inv.student.full_name,
            'admission_number': inv.student.admission_number,
            'class_name': str(inv.student.current_class_level),
            'arm_name': inv.student.current_class_arm.name if inv.student.current_class_arm else '',
            'balance': inv.balance,
            'invoice_id': inv.id
        })

    # Enrollment Breakdown by Section (Primary, JSS, SSS)
    primary_count = Student.objects.filter(current_class_level__category='PRIMARY').count()
    jss_count = Student.objects.filter(current_class_level__category='JSS').count()
    sss_count = Student.objects.filter(current_class_level__category='SSS').count()

    # At-risk Class Arms (Class arms with zero Score records for current term)
    class_arms = ClassArm.objects.select_related('class_level').all()
    at_risk_count = 0
    if current_term:
        for arm in class_arms:
            has_scores = Score.objects.filter(term=current_term, class_arm=arm).exists()
            if not has_scores:
                at_risk_count += 1

    # Recent Announcements
    announcements = Announcement.objects.filter(Q(target_role='ALL') | Q(target_role='STUDENTS') | Q(target_role='TEACHERS')).order_by('-created_at')[:5]

    # Student Search functionality (GET query)
    search_query = request.GET.get('q', '').strip()
    search_results = []
    if search_query:
        search_results = Student.objects.filter(
            Q(admission_number__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        ).select_related('current_class_level', 'current_class_arm')[:10]

    # Chart Data: Student count per class arm (covering all arms)
    chart_labels = []
    chart_counts = []
    for arm in class_arms:
        label = f"{arm.class_level.name} {arm.name}"
        count = Student.objects.filter(current_class_arm=arm).count()
        chart_labels.append(label)
        chart_counts.append(count)

    context = {
        'greeting': get_greeting(request.user),
        'total_students': total_students,
        'total_staff': total_staff,
        'attendance_rate': attendance_rate,
        'outstanding_fees_total': outstanding_fees_total,
        'top_debtors': top_debtors,
        'primary_count': primary_count,
        'jss_count': jss_count,
        'sss_count': sss_count,
        'at_risk_count': at_risk_count,
        'announcements': announcements,
        'search_query': search_query,
        'search_results': search_results,
        'chart_labels': chart_labels,
        'chart_counts': chart_counts,
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@role_required("TEACHER")
def teacher_dashboard(request):
    teacher = Teacher.objects.filter(user=request.user).first()
    current_term = Term.objects.filter(is_current=True).first()
    today_day_name = datetime.now().strftime('%A').upper()  # e.g., MONDAY

    from apps.academics.permissions import scoreable_arms, offered_subjects, scoreable_subjects

    led_arms = scoreable_arms(teacher) if teacher else ClassArm.objects.none()

    # Rough count of pending score entries (classes where teacher is class teacher)
    pending_scores_count = 0
    if current_term and teacher:
        for arm in led_arms:
            offered = offered_subjects(arm)
            for subj in offered:
                has_score = Score.objects.filter(term=current_term, class_arm=arm, subject=subj).exists()
                if not has_score:
                    pending_scores_count += 1

    # Today's Timetable slots for teacher's led class arms
    timetable_slots = TimetableSlot.objects.filter(
        class_arm__in=led_arms,
        day_of_week=today_day_name
    ).select_related('period', 'class_arm__class_level', 'subject', 'teacher').order_by('period__start_time')

    # Recent announcements visible to teachers
    announcements = Announcement.objects.filter(Q(target_role='ALL') | Q(target_role='TEACHERS')).order_by('-created_at')[:5]

    # Chart Data: Student count per led class arm
    chart_labels = []
    chart_counts = []
    for arm in led_arms:
        label = f"{arm.class_level.name} {arm.name}"
        count = Student.objects.filter(current_class_arm=arm).count()
        chart_labels.append(label)
        chart_counts.append(count)

    context = {
        'greeting': get_greeting(request.user),
        'teacher': teacher,
        'current_term': current_term,
        'assigned_arms': led_arms,  # Use led_arms for compatibility with template
        'pending_scores_count': pending_scores_count,
        'timetable_slots': timetable_slots,
        'announcements': announcements,
        'chart_labels': chart_labels,
        'chart_counts': chart_counts,
    }
    return render(request, 'dashboard/teacher_dashboard.html', context)


@role_required("STUDENT")
def student_dashboard(request):
    student = Student.objects.filter(user=request.user).select_related('current_class_level', 'current_class_arm').first()
    current_term = Term.objects.filter(is_current=True).first()
    today_day_name = datetime.now().strftime('%A').upper()

    # Student's own attendance rate
    attendance_rate = 0.0
    if student:
        total_student_records = AttendanceRecord.objects.filter(student=student).count()
        present_student_records = AttendanceRecord.objects.filter(student=student, status='PRESENT').count()
        if total_student_records > 0:
            attendance_rate = round((present_student_records / total_student_records * 100), 1)

    # Latest scores for current term
    latest_scores = []
    if student and current_term:
        latest_scores = Score.objects.filter(student=student, term=current_term).select_related('subject', 'assessment_type')[:10]

    # Outstanding fee balance for this student
    outstanding_balance = 0.00
    if student:
        zero_dec = DecimalField(max_digits=12, decimal_places=2)
        student_invoices = Invoice.objects.filter(student=student).exclude(status='PAID')
        balance_res = student_invoices.aggregate(
            total=Coalesce(Sum(F('total_amount') - F('amount_paid'), output_field=zero_dec), 0, output_field=zero_dec)
        )
        outstanding_balance = balance_res['total']

    # Today's timetable for student's current class arm
    timetable_slots = []
    if student and student.current_class_arm:
        timetable_slots = TimetableSlot.objects.filter(
            class_arm=student.current_class_arm,
            day_of_week=today_day_name
        ).select_related('period', 'subject', 'teacher').order_by('period__start_time')

    # Announcements visible to students
    announcements = Announcement.objects.filter(Q(target_role='ALL') | Q(target_role='STUDENTS')).order_by('-created_at')[:5]

    context = {
        'greeting': get_greeting(request.user),
        'student': student,
        'current_term': current_term,
        'attendance_rate': attendance_rate,
        'latest_scores': latest_scores,
        'outstanding_balance': outstanding_balance,
        'timetable_slots': timetable_slots,
        'announcements': announcements,
    }
    return render(request, 'dashboard/student_dashboard.html', context)



#AssessmentT Functions
@staff_member_required
def assessment_type_list(request):
  assessment_types = AssessmentType.objects.select_related('term', 'term__session').order_by('-term', 'name')
  return render(
      request,
      'dashboard/academics/assessment_type_list.html',
      {'assessment_types': assessment_types},
  )


@staff_member_required
def assessment_type_create(request):
  if request.method == 'POST':
    form = AssessmentTypeForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(request, 'Assessment type created successfully.')
      return redirect('dashboard:assessment_type_list')
  else:
    form = AssessmentTypeForm()
  return render(
      request,
      'dashboard/academics/assessment_type_form.html',
      {'form': form, 'title': 'Add Assessment Type'},
  )


@staff_member_required
def assessment_type_update(request, pk):
  assessment_type = get_object_or_404(AssessmentType, pk=pk)
  if request.method == 'POST':
    form = AssessmentTypeForm(request.POST, instance=assessment_type)
    if form.is_valid():
      form.save()
      messages.success(request, 'Assessment type updated successfully.')
      return redirect('dashboard:assessment_type_list')
  else:
    form = AssessmentTypeForm(instance=assessment_type)
  return render(
      request,
      'dashboard/academics/assessment_type_form.html',
      {'form': form, 'title': 'Edit Assessment Type'},
  )


@staff_member_required
def assessment_type_delete(request, pk):
  assessment_type = get_object_or_404(AssessmentType, pk=pk)
  if request.method == 'POST':
    assessment_type.delete()
    messages.success(request, 'Assessment type deleted successfully.')
    return redirect('dashboard:assessment_type_list')
  return render(
      request,
      'dashboard/academics/assessment_type_confirm_delete.html',
      {'assessment_type': assessment_type},
  )

#Grading Scale Functions
@staff_member_required
def grading_scale_list(request):
  grading_scales = GradingScale.objects.all().order_by('min_score')
  return render(
      request,
      'dashboard/academics/grading_scale_list.html',
      {'grading_scales': grading_scales},
  )


@staff_member_required
def grading_scale_create(request):
  if request.method == 'POST':
    form = GradingScaleForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(request, 'Grading scale created successfully.')
      return redirect('dashboard:grading_scale_list')
  else:
    form = GradingScaleForm()
  return render(
      request,
      'dashboard/academics/grading_scale_form.html',
      {'form': form, 'title': 'Add Grading Scale'},
  )


@staff_member_required
def grading_scale_update(request, pk):
  grading_scale = get_object_or_404(GradingScale, pk=pk)
  if request.method == 'POST':
    form = GradingScaleForm(request.POST, instance=grading_scale)
    if form.is_valid():
      form.save()
      messages.success(request, 'Grading scale updated successfully.')
      return redirect('dashboard:grading_scale_list')
  else:
    form = GradingScaleForm(instance=grading_scale)
  return render(
      request,
      'dashboard/academics/grading_scale_form.html',
      {'form': form, 'title': 'Edit Grading Scale'},
  )


@staff_member_required
def grading_scale_delete(request, pk):
  grading_scale = get_object_or_404(GradingScale, pk=pk)
  if request.method == 'POST':
    grading_scale.delete()
    messages.success(request, 'Grading scale deleted successfully.')
    return redirect('dashboard:grading_scale_list')
  return render(
      request,
      'dashboard/academics/grading_scale_confirm_delete.html',
      {'grading_scale': grading_scale},
  )
  
#Remarks views
@staff_member_required
def predefined_remark_list(request):
  # Updated to sort by 'type' and 'text' instead of non-existent fields
  remarks = PredefinedRemark.objects.all().order_by('type', 'text')
  return render(
      request,
      'dashboard/academics/predefined_remark_list.html',
      {'remarks': remarks},
  )


@staff_member_required
def predefined_remark_create(request):
  if request.method == 'POST':
    form = PredefinedRemarkForm(request.POST)
    if form.is_valid():
      form.save()
      messages.success(request, 'Predefined remark created successfully.')
      return redirect('dashboard:predefined_remark_list')
  else:
    form = PredefinedRemarkForm()
  return render(
      request,
      'dashboard/academics/predefined_remark_form.html',
      {'form': form, 'title': 'Add Predefined Remark'},
  )


@staff_member_required
def predefined_remark_update(request, pk):
  remark = get_object_or_404(PredefinedRemark, pk=pk)
  if request.method == 'POST':
    form = PredefinedRemarkForm(request.POST, instance=remark)
    if form.is_valid():
      form.save()
      messages.success(request, 'Predefined remark updated successfully.')
      return redirect('dashboard:predefined_remark_list')
  else:
    form = PredefinedRemarkForm(instance=remark)
  return render(
      request,
      'dashboard/academics/predefined_remark_form.html',
      {'form': form, 'title': 'Edit Predefined Remark'},
  )


@staff_member_required
def predefined_remark_delete(request, pk):
  remark = get_object_or_404(PredefinedRemark, pk=pk)
  if request.method == 'POST':
    remark.delete()
    messages.success(request, 'Predefined remark deleted successfully.')
    return redirect('dashboard:predefined_remark_list')
  return render(
      request,
      'dashboard/academics/predefined_remark_confirm_delete.html',
      {'remark': remark},
  )


# API endpoint for teachers/admins to fetch remarks dynamically
def api_get_predefined_remarks(request):
  remarks = list(PredefinedRemark.objects.values('id', 'type', 'text'))
  return JsonResponse({'remarks': remarks})


# ----------------------------------------------------------------------
# TEACHER STUDENT MANAGEMENT VIEWS
# ----------------------------------------------------------------------

@role_required("TEACHER")
def teacher_student_list(request):
    # Use the helper function for consistency
    led_arms = _class_teacher_arms(request.user)
    
    if not led_arms.exists():
        messages.error(request, "You are not assigned as a class teacher to any class arm.")
        return redirect("dashboard:teacher")

    students = Student.objects.filter(current_class_arm__in=led_arms).select_related(
        "current_class_level", "current_class_arm"
    ).order_by("last_name", "first_name")

    context = {
        "greeting": get_greeting(request.user),
        "students": students,
        "led_arms": led_arms,
    }
    return render(request, "dashboard/teacher/student_list.html", context)


@role_required("TEACHER")
def teacher_student_add(request):
    led_arms = _class_teacher_arms(request.user)
    
    if not led_arms.exists():
        messages.error(request, "You are not assigned as a class teacher to any class arm.")
        return redirect("dashboard:teacher")

    if request.method == "POST":
        form = TeacherStudentForm(request.POST, arms=led_arms)
        if form.is_valid():
            form.save()
            messages.success(request, "Student added successfully.")
            return redirect("dashboard:teacher_student_list")
    else:
        form = TeacherStudentForm(arms=led_arms)

    context = {
        "greeting": get_greeting(request.user),
        "form": form,
    }
    return render(request, "dashboard/teacher/student_form.html", context)


@role_required("TEACHER")
def teacher_student_edit(request, pk):
    led_arms = _class_teacher_arms(request.user)
    
    if not led_arms.exists():
        messages.error(request, "You are not assigned as a class teacher to any class arm.")
        return redirect("dashboard:teacher")

    student = get_object_or_404(Student, pk=pk, current_class_arm__in=led_arms)

    if request.method == "POST":
        form = TeacherStudentForm(request.POST, instance=student, arms=led_arms)
        if form.is_valid():
            form.save()
            messages.success(request, "Student updated successfully.")
            return redirect("dashboard:teacher_student_list")
    else:
        form = TeacherStudentForm(instance=student, arms=led_arms)
        if student.current_class_arm:
            form.fields['class_arm'].initial = student.current_class_arm

    context = {
        "greeting": get_greeting(request.user),
        "form": form,
        "student": student,
    }
    return render(request, "dashboard/teacher/student_form.html", context)


@role_required("TEACHER")
def teacher_class_subjects(request, arm_id):
    """
    Class teacher ticks the subjects the class offers and picks each subject's teacher.
    A teacher picked here can enter scores for that subject in this class (and nothing else).
    """
    arm = get_object_or_404(_class_teacher_arms(request.user), pk=arm_id)
 
    teachers = list(
        Teacher.objects.select_related("user")
        .order_by("user__first_name", "user__last_name", "user__username")
    )
    teacher_by_id = {str(t.id): t for t in teachers}
 
    if request.method == "POST":
        selected = Subject.objects.filter(pk__in=request.POST.getlist("subjects"))
        arm.subjects.set(selected)
 
        for subject in selected:
            teacher = teacher_by_id.get(request.POST.get(f"teacher_{subject.pk}", "").strip())
            typed = request.POST.get(f"name_{subject.pk}", "").strip()
            ClassSubjectTeacher.objects.update_or_create(
                class_arm=arm,
                subject=subject,
                defaults={
                    "teacher": teacher,
                    "teacher_name": "" if teacher else typed,   # typed name only if no account picked
                },
            )
 
        # a subject taken off the class loses its assignment (and the teacher's access)
        ClassSubjectTeacher.objects.filter(class_arm=arm).exclude(subject__in=selected).delete()
 
        messages.success(request, f"Subjects for {arm} saved ({selected.count()} selected).")
        return redirect("dashboard:teacher_student_list")
 
    selected_ids = set(arm.subjects.values_list("pk", flat=True))
    assignments = {a.subject_id: a for a in ClassSubjectTeacher.objects.filter(class_arm=arm)}
    rows = []
    for s in Subject.objects.all():
        a = assignments.get(s.pk)
        rows.append({
            "subject": s,
            "checked": s.pk in selected_ids,
            "teacher_id": a.teacher_id if a else None,
            "typed_name": a.teacher_name if a else "",
        })
 
    return render(request, "dashboard/teacher/class_subjects.html", {
        "arm": arm,
        "rows": rows,
        "teachers": teachers,
    })

def _class_teacher_arms(user):
    """Arms where this user is one of the class teachers."""
    teacher = Teacher.objects.filter(user=user).first()
    if not teacher:
        return ClassArm.objects.none()
    return ClassArm.objects.filter(class_teachers=teacher).select_related("class_level")

@role_required("TEACHER")
def teacher_class_subjects_home(request):
    arms = list(_class_teacher_arms(request.user))
    if len(arms) == 1:
        return redirect("dashboard:teacher_class_subjects", arm_id=arms[0].id)
    return redirect("dashboard:teacher_student_list")