from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Stage placeholders for routing:
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('school/', include('apps.school_structure.urls')),
    path("students/", include("apps.students.urls", namespace="students")),
    path("staff/", include("apps.staff.urls", namespace="staff")),
    path("attendance/", include("apps.attendance.urls", namespace="attendance")),
    path("academics/", include("apps.academics.urls", namespace="academics")),
    path("timetable/", include("apps.timetable.urls", namespace="timetable")),
    path("finance/", include("apps.finance.urls", namespace="finance")),
    path("library/", include("apps.library.urls", namespace="library")),
    path("communication/", include("apps.communication.urls", namespace="communication")),
    path('dashboard/', include('apps.dashboard.urls')),
    path('manage-website/', include('apps.core.cms_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom Error Handlers
handler404 = 'config.views.page_not_found'
handler500 = 'config.views.server_error'