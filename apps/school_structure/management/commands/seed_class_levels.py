from django.core.management.base import BaseCommand
from apps.school_structure.models import ClassLevel, ClassArm


class Command(BaseCommand):
    help = "Seeds standard ClassLevel and ClassArm records idempotently."

    def handle(self, *args, **options):
        # List of class levels with (name, category, order)
        class_levels_data = [
            # Primary School (Order 1 - 6)
            ("Primary 1", ClassLevel.Category.PRIMARY, 1),
            ("Primary 2", ClassLevel.Category.PRIMARY, 2),
            ("Primary 3", ClassLevel.Category.PRIMARY, 3),
            ("Primary 4", ClassLevel.Category.PRIMARY, 4),
            ("Primary 5", ClassLevel.Category.PRIMARY, 5),
            ("Primary 6", ClassLevel.Category.PRIMARY, 6),
            # Junior Secondary School (Order 7 - 9)
            ("JSS1", ClassLevel.Category.JSS, 7),
            ("JSS2", ClassLevel.Category.JSS, 8),
            ("JSS3", ClassLevel.Category.JSS, 9),
            # Senior Secondary School (Order 10 - 12)
            ("SS1", ClassLevel.Category.SSS, 10),
            ("SS2", ClassLevel.Category.SSS, 11),
            ("SS3", ClassLevel.Category.SSS, 12),
        ]

        created_levels_count = 0
        created_arms_count = 0

        for name, category, order in class_levels_data:
            class_level, created = ClassLevel.objects.get_or_create(
                name=name,
                defaults={"category": category, "order": order},
            )
            if created:
                created_levels_count += 1
            else:
                # Update category and order in case they changed
                class_level.category = category
                class_level.order = order
                class_level.save()

            # Create Arms 'A', 'B', 'C' for JSS and SSS levels only
            if category in (ClassLevel.Category.JSS, ClassLevel.Category.SSS):
                for arm_name in ["A", "B", "C"]:
                    _, arm_created = ClassArm.objects.get_or_create(
                        class_level=class_level,
                        name=arm_name,
                    )
                    if arm_created:
                        created_arms_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeding complete! Class Levels created: {created_levels_count}, "
                f"Class Arms created: {created_arms_count}."
            )
        )