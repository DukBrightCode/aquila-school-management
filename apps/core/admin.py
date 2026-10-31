from django.contrib import admin
from .models import Event, Gallery, HeroSlide, News, SiteSetting, Announcement, SchoolStat, Feature, Achievement, Testimonial, QuickLink, DownloadFile, FAQ, KeyDate

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'date', 'is_featured', 'is_published', 'created_at']
    list_filter = ['event_type', 'is_featured', 'is_published', 'date']
    search_fields = ['title', 'description', 'location']
    list_editable = ['is_featured', 'is_published']
    date_hierarchy = 'date'
    prepopulated_fields = {}
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'event_type')
        }),
        ('Event Details', {
            'fields': ('date', 'location', 'image')
        }),
        ('Publishing', {
            'fields': ('is_featured', 'is_published')
        }),
    )


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'is_published', 'created_at']
    list_filter = ['category', 'is_published', 'created_at']
    search_fields = ['title', 'description']
    list_editable = ['is_published']
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category')
        }),
        ('Image', {
            'fields': ('image',)
        }),
        ('Publishing', {
            'fields': ('is_published',)
        }),
    )


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_featured', 'is_published', 'published_date', 'created_at']
    list_filter = ['is_featured', 'is_published', 'published_date']
    search_fields = ['title', 'content', 'summary']
    list_editable = ['is_featured', 'is_published']
    date_hierarchy = 'published_date'
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'summary', 'content')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Publishing', {
            'fields': ('is_featured', 'is_published', 'published_date')
        }),
    )



@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    fieldsets = (
        ('School identity', {'fields': ('school_name', 'school_motto', 'tagline', 'logo', 'hero_image')}),
        ('Admissions banner', {'fields': ('admissions_open', 'admissions_text')}),
        ("Principal's message", {'fields': ('principal_name', 'principal_title', 'principal_photo', 'principal_message')}),
        ('Contact and social media', {'fields': (
            'phone', 'phone_list', 'whatsapp', 'email', 'website',
            'address', 'office_hours', 'map_embed_url',
            'facebook', 'instagram', 'youtube',
        )}),
    )

    def has_add_permission(self, request):
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('text', 'is_active', 'created_at')
    list_editable = ('is_active',)


@admin.register(SchoolStat)
class SchoolStatAdmin(admin.ModelAdmin):
    list_display = ('value', 'label', 'order', 'is_active')
    list_editable = ('order', 'is_active')


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ('title', 'icon', 'order', 'is_active')
    list_editable = ('order', 'is_active')


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'year', 'is_featured', 'is_published')
    list_filter = ('category', 'is_published', 'is_featured')
    list_editable = ('is_featured', 'is_published')
    search_fields = ('title', 'description')


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'order', 'is_published')
    list_filter = ('role', 'is_published')
    list_editable = ('order', 'is_published')


@admin.register(QuickLink)
class QuickLinkAdmin(admin.ModelAdmin):
    list_display = ('label', 'url', 'order', 'is_active')
    list_editable = ('order', 'is_active')


@admin.register(DownloadFile)
class DownloadFileAdmin(admin.ModelAdmin):
    list_display = ('title', 'order', 'is_published')
    list_editable = ('order', 'is_published')


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'order', 'is_published')
    list_editable = ('order', 'is_published')


@admin.register(KeyDate)
class KeyDateAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'is_active')
    list_editable = ('is_active',)
    ordering = ('date',)
    
@admin.register(HeroSlide)
class HeroSlideAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'order', 'is_active')
    list_editable = ('order', 'is_active')