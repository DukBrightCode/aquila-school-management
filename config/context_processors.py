from django.conf import settings
from django.db.utils import OperationalError, ProgrammingError

from apps.core.models import SiteSetting, Announcement


def school_info(request):
    default_name = getattr(settings, 'SCHOOL_NAME', 'Aquila British International School')
    default_motto = getattr(settings, 'SCHOOL_MOTTO', 'Scientia Omnia Vincit')

    try:
        # First run: creates the settings row using your current name and motto,
        # so you don't have to retype them in the admin.
        site, _ = SiteSetting.objects.get_or_create(
            pk=1,
            defaults={'school_name': default_name, 'school_motto': default_motto},
        )
        announcement = Announcement.objects.filter(is_active=True).first()
    except (OperationalError, ProgrammingError):
        # Database tables don't exist yet (before you run migrate)
        return {
            'SCHOOL_NAME': default_name,
            'SCHOOL_MOTTO': default_motto,
            'SITE': None,
            'ANNOUNCEMENT': None,
        }

    return {
        'SCHOOL_NAME': site.school_name,
        'SCHOOL_MOTTO': site.school_motto,
        'SITE': site,
        'ANNOUNCEMENT': announcement,
    }