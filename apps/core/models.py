from django.db import models
from django.utils import timezone


class Event(models.Model):
    EVENT_TYPE_CHOICES = [
        ('academic', 'Academic'),
        ('sports', 'Sports'),
        ('cultural', 'Cultural'),
        ('general', 'General'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, default='general')
    date = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to='events/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def __str__(self):
        return self.title

    @property
    def is_upcoming(self):
        return self.date >= timezone.now()


class Gallery(models.Model):
    CATEGORY_CHOICES = [
        ('school_life', 'School Life'),
        ('academic', 'Academic Activities'),
        ('sports', 'Sports & Events'),
        ('facilities', 'Facilities'),
        ('achievements', 'Achievements'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='school_life')
    image = models.ImageField(upload_to='gallery/')
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Gallery Image'
        verbose_name_plural = 'Gallery Images'

    def __str__(self):
        return self.title


class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    summary = models.CharField(max_length=300, help_text='Brief summary for the news card')
    image = models.ImageField(upload_to='news/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    published_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-published_date']
        verbose_name = 'News'
        verbose_name_plural = 'News'

    def __str__(self):
        return self.title


# ADD THIS BELOW your existing News model in core/models.py
# (Keep your Event, Gallery and News models exactly as they are.)

class SiteSetting(models.Model):
    school_name = models.CharField(max_length=200, default='My School')
    school_motto = models.CharField(max_length=200, blank=True)
    tagline = models.CharField(max_length=300, blank=True,
        default="Nurturing tomorrow's leaders through academic excellence, innovation, and strong character development.")
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    hero_image = models.ImageField(upload_to='site/', blank=True, null=True)

    # Admissions banner
    admissions_open = models.BooleanField(default=False)
    admissions_text = models.CharField(max_length=300, blank=True,
        help_text='e.g. Admissions are open for the 2026/2027 session.')

    # Principal's message
    principal_name = models.CharField(max_length=150, blank=True)
    principal_title = models.CharField(max_length=150, blank=True, default="Principal")
    principal_photo = models.ImageField(upload_to='site/', blank=True, null=True)
    principal_message = models.TextField(blank=True)

    # Contact and social
    phone = models.CharField(max_length=50, blank=True)
    phone_list = models.TextField(blank=True,
        help_text='Shown in the footer. One line per group of numbers, for example: 08161351248, 08051851894')
    whatsapp = models.CharField(max_length=20, blank=True,
        help_text='Digits only, with country code and no plus sign. Example: 2348012345678')
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True, help_text='Example: https://www.yourschool.com')
    address = models.CharField(max_length=300, blank=True)
    office_hours = models.CharField(max_length=200, blank=True,
        help_text='Example: Monday to Friday, 8:00 AM to 4:00 PM')
    map_embed_url = models.URLField(max_length=1000, blank=True,
        help_text='Google Maps > Share > Embed a map > copy ONLY the address inside src="..."')
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    youtube = models.URLField(blank=True)

    class Meta:
        verbose_name = 'Site Setting'
        verbose_name_plural = 'Site Settings'

    def save(self, *args, **kwargs):
        self.pk = 1  # only one settings row
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def phone_lines(self):
        return [line.strip() for line in self.phone_list.splitlines() if line.strip()]

    def __str__(self):
        return 'Site Settings'


class Announcement(models.Model):
    """Short notice shown in a bar at the very top of the home page."""
    text = models.CharField(max_length=250)
    link = models.CharField(max_length=300, blank=True, help_text='Optional page or URL')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.text[:60]


class SchoolStat(models.Model):
    """Numbers shown under the hero, e.g. '1,200+' / 'Students'."""
    value = models.CharField(max_length=30)
    label = models.CharField(max_length=60)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.value} {self.label}'


class Feature(models.Model):
    """The 'Why choose us' cards."""
    ICON_CHOICES = [('cap', 'Graduation cap'), ('check', 'Checkmark'),
                    ('building', 'Building'), ('book', 'Book'), ('users', 'People')]
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=20, choices=ICON_CHOICES, default='cap')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class Achievement(models.Model):
    """Success stories: exam results, awards, competition wins, alumni success."""
    CATEGORY_CHOICES = [('exams', 'Exam results'), ('academic', 'Academic award'),
                        ('sports', 'Sports'), ('competition', 'Competition'),
                        ('alumni', 'Alumni success')]
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='academic')
    year = models.PositiveIntegerField(blank=True, null=True)
    image = models.ImageField(upload_to='achievements/', blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_featured', '-year', '-created_at']

    def __str__(self):
        return self.title


class Testimonial(models.Model):
    ROLE_CHOICES = [('parent', 'Parent'), ('student', 'Student'),
                    ('alumnus', 'Alumnus'), ('teacher', 'Teacher')]
    name = models.CharField(max_length=120)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='parent')
    message = models.TextField()
    photo = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', '-id']

    def __str__(self):
        return f'{self.name} ({self.get_role_display()})'
    

class HeroSlide(models.Model):
    """Background photos that fade in turn at the top of the home page."""
    title = models.CharField(max_length=150, blank=True,
        help_text='Short label for your own reference. Also used as the photo description.')
    image = models.ImageField(upload_to='hero/')
    order = models.PositiveIntegerField(default=0, help_text='Lower numbers show first.')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', '-id']
        verbose_name = 'Hero Slide'
        verbose_name_plural = 'Hero Slides'

    def __str__(self):
        return self.title or f'Slide {self.pk}'
    
class QuickLink(models.Model):
    """Big buttons near the top: Student login, Results, Fee payment..."""
    label = models.CharField(max_length=60)
    description = models.CharField(max_length=120, blank=True)
    url = models.CharField(max_length=300, help_text='Page like /accounts/login/ or a full https:// link')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.label


class DownloadFile(models.Model):
    """Prospectus, admission form, fee schedule, school calendar."""
    title = models.CharField(max_length=150)
    description = models.CharField(max_length=200, blank=True)
    file = models.FileField(upload_to='downloads/')
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['order', 'title']

    def __str__(self):
        return self.title


class FAQ(models.Model):
    question = models.CharField(max_length=250)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question


class KeyDate(models.Model):
    """Resumption, open day, exams, holidays. Past dates hide automatically."""
    title = models.CharField(max_length=150)
    date = models.DateField()
    note = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return f'{self.title} ({self.date})'

    @property
    def days_left(self):
        return (self.date - timezone.localdate()).days

