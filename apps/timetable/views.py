from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from apps.accounts.permissions import role_required
from apps.school_structure.models import ClassArm, Subject
from apps.staff.models import Teacher
from .models import Period, TimetableSlot


@login_required
def class_timetable(request):
    """
    Read-only weekly schedule grid view accessible by any authenticated user.
    """
    class_arms = ClassArm.objects.select_related("class_level").all().order_by("class_level__order", "name")
    selected_class_arm_id = request.GET.get("class_arm")

    selected_class_arm = None
    timetable_grid = []
    periods = Period.objects.all().order_by("start_time")
    days = [
        ("MONDAY", "Monday"),
        ("TUESDAY", "Tuesday"),
        ("WEDNESDAY", "Wednesday"),
        ("THURSDAY", "Thursday"),
        ("FRIDAY", "Friday"),
    ]

    if selected_class_arm_id:
        selected_class_arm = get_object_or_404(ClassArm, id=selected_class_arm_id)
        slots = TimetableSlot.objects.filter(
            class_arm=selected_class_arm
        ).select_related("subject", "teacher__user", "period")

        # Key lookup map: (period_id, day_code) -> slot instance
        slot_map = {(slot.period_id, slot.day_of_week): slot for slot in slots}

        # Build daily matrix structure
        for period in periods:
            row_slots = []
            for day_code, day_name in days:
                row_slots.append(slot_map.get((period.id, day_code)))
            timetable_grid.append({
                "period": period,
                "slots": row_slots,
            })

    context = {
        "class_arms": class_arms,
        "selected_class_arm": selected_class_arm,
        "periods": periods,
        "days": days,
        "timetable_grid": timetable_grid,
    }
    return render(request, "timetable/class_timetable.html", context)


@role_required("ADMIN")
def edit_timetable(request, class_arm_id):
    """
    Admin-only portal view to update slot allocations for a given class arm.
    """
    class_arm = get_object_or_404(ClassArm, id=class_arm_id)
    periods = Period.objects.all().order_by("start_time")
    subjects = Subject.objects.all().order_by("name")
    teachers = Teacher.objects.select_related("user").all().order_by("user__first_name")
    days = [
        ("MONDAY", "Monday"),
        ("TUESDAY", "Tuesday"),
        ("WEDNESDAY", "Wednesday"),
        ("THURSDAY", "Thursday"),
        ("FRIDAY", "Friday"),
    ]

    if request.method == "POST":
        period_id = request.POST.get("period")
        day_of_week = request.POST.get("day_of_week")
        subject_id = request.POST.get("subject")
        teacher_id = request.POST.get("teacher")

        period = get_object_or_404(Period, id=period_id)
        subject = get_object_or_404(Subject, id=subject_id)
        teacher = Teacher.objects.filter(id=teacher_id).first() if teacher_id else None

        TimetableSlot.objects.update_or_create(
            class_arm=class_arm,
            day_of_week=day_of_week,
            period=period,
            defaults={"subject": subject, "teacher": teacher},
        )
        messages.success(request, f"Timetable entry for {day_of_week.capitalize()} ({period.name}) updated successfully.")
        return redirect(f"{request.path}?class_arm={class_arm.id}")

    slots = TimetableSlot.objects.filter(class_arm=class_arm).select_related("subject", "teacher__user", "period")
    slot_map = {(slot.period_id, slot.day_of_week): slot for slot in slots}

    timetable_grid = []
    for period in periods:
        row_slots = []
        for day_code, day_name in days:
            row_slots.append(slot_map.get((period.id, day_code)))
        timetable_grid.append({
            "period": period,
            "slots": row_slots,
        })

    context = {
        "class_arm": class_arm,
        "periods": periods,
        "subjects": subjects,
        "teachers": teachers,
        "days": days,
        "timetable_grid": timetable_grid,
    }
    return render(request, "timetable/class_timetable.html", context)


@login_required
@role_required("ADMIN")
def period_list(request):
    """
    Admin view to manage timetable periods.
    """
    periods = Period.objects.all().order_by("start_time")

    context = {
        "periods": periods,
    }
    return render(request, "timetable/period_list.html", context)