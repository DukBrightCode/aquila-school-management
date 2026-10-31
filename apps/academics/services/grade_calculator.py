from decimal import Decimal, ROUND_HALF_UP
from django.db.models import Sum
from apps.academics.models import AssessmentType, GradingScale, Score


def calculate_term_result(student, subject, term) -> dict:
    """
    Calculates a student's term result for a given subject based on active administrator-configured
    AssessmentTypes for the specified term.

    Returns dict with exactly:
        {
            "total_score": Decimal,
            "grade_letter": str,
            "remark": str
        }
    """
    # 1. Fetch active assessment types for the term
    active_assessments = AssessmentType.objects.filter(term=term, is_active=True)

    if not active_assessments.exists():
        raise ValueError(f"No active assessment configuration found for term '{term}'.")

    # 2. Validate active assessment weights total exactly 100%
    total_weight = active_assessments.aggregate(total=Sum("weight_percentage"))["total"] or Decimal("0")
    if total_weight != Decimal("100.00"):
        raise ValueError(
            f"Active assessment weights for term '{term}' total {total_weight}%, but must total exactly 100%."
        )

    # 3. Retrieve student's entered raw scores for active components
    scores = Score.objects.filter(
        student=student,
        subject=subject,
        term=term,
        assessment_type__in=active_assessments
    ).select_related("assessment_type")

    scores_by_assessment = {score.assessment_type_id: score for score in scores}

    # 4. Calculate total weighted score contribution
    total_score = Decimal("0.00")

    for assessment in active_assessments:
        score_obj = scores_by_assessment.get(assessment.id)
        if score_obj and score_obj.score_value is not None:
            raw_score = score_obj.score_value
            max_score = assessment.max_score
            weight = assessment.weight_percentage

            if max_score > 0:
                weighted_contribution = (raw_score / max_score) * weight
                total_score += weighted_contribution

    # Round total score to 2 decimal places
    total_score = total_score.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # 5. Look up grading scale letter and remark
    grading_entry = GradingScale.objects.filter(
        min_score__lte=total_score,
        max_score__gte=total_score
    ).first()

    if grading_entry:
        grade_letter = grading_entry.grade_letter
        remark = grading_entry.remark
    else:
        grade_letter = "N/A"
        remark = "Ungraded"

    return {
        "total_score": total_score,
        "grade_letter": grade_letter,
        "remark": remark,
    }