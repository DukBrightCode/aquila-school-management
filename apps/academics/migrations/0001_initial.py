from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("school_structure", "__first__"),
        ("students", "__first__"),
        ("staff", "__first__"),
    ]

    operations = [
        migrations.CreateModel(
            name="AssessmentType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100)),
                ("max_score", models.DecimalField(decimal_places=2, max_digits=8)),
                ("weight_percentage", models.DecimalField(decimal_places=2, max_digits=5)),
                ("active", models.BooleanField(default=True)),
                ("term", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assessment_types", to="school_structure.term")),
            ],
            options={"ordering": ["term", "name", "pk"]},
        ),
        migrations.CreateModel(
            name="GradingScale",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("min_score", models.DecimalField(decimal_places=2, max_digits=6)),
                ("max_score", models.DecimalField(decimal_places=2, max_digits=6)),
                ("grade_letter", models.CharField(max_length=10)),
                ("remark", models.CharField(max_length=255)),
            ],
            options={"ordering": ["-min_score", "-max_score"]},
        ),
        migrations.CreateModel(
            name="Score",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("score_value", models.DecimalField(decimal_places=2, max_digits=8)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("assessment_type", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="scores", to="academics.assessmenttype")),
                ("class_arm", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="scores", to="school_structure.classarm")),
                ("entered_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="entered_scores", to="staff.teacher")),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="scores", to="students.student")),
                ("subject", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="scores", to="school_structure.subject")),
                ("term", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="scores", to="school_structure.term")),
            ],
            options={"ordering": ["student_id", "assessment_type_id"]},
        ),
        migrations.AddConstraint(
            model_name="assessmenttype",
            constraint=models.UniqueConstraint(fields=("term", "name"), name="academics_assessment_term_name_unique"),
        ),
        migrations.AddConstraint(
            model_name="assessmenttype",
            constraint=models.CheckConstraint(condition=models.Q(max_score__gt=0), name="academics_assessment_max_score_gt_zero"),
        ),
        migrations.AddConstraint(
            model_name="assessmenttype",
            constraint=models.CheckConstraint(condition=models.Q(weight_percentage__gte=0) & models.Q(weight_percentage__lte=100), name="academics_assessment_weight_0_100"),
        ),
        migrations.AddConstraint(
            model_name="score",
            constraint=models.UniqueConstraint(fields=("student", "subject", "term", "assessment_type"), name="academics_score_student_subject_term_assessment_unique"),
        ),
    ]
