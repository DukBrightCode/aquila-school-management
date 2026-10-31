# Save as: apps/core/cms_views.py
from datetime import date, datetime

from django import forms
from django.contrib import messages
from django.core.paginator import Paginator
from django.forms import modelform_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from apps.accounts.permissions import role_required

from .models import (
    Achievement, Announcement, DownloadFile, Event, FAQ, Feature, Gallery,
    HeroSlide, KeyDate, News, QuickLink, SchoolStat, SiteSetting, Testimonial,
)


# Same rule your admin dashboard uses: only users whose role is ADMIN.
admin_required = role_required("ADMIN")


# ---------- What can be managed ----------
REGISTRY = {
    'events': dict(model=Event, title='Events', one='event',
        fields=['title', 'event_type', 'date', 'location', 'description', 'image', 'is_featured', 'is_published'],
        columns=['title', 'event_type', 'date', 'is_published']),
    'news': dict(model=News, title='News', one='news story',
        fields=['title', 'summary', 'content', 'image', 'published_date', 'is_featured', 'is_published'],
        columns=['title', 'published_date', 'is_featured', 'is_published']),
    'achievements': dict(model=Achievement, title='Achievements', one='achievement',
        fields=['title', 'description', 'category', 'year', 'image', 'is_featured', 'is_published'],
        columns=['title', 'category', 'year', 'is_published']),
    'testimonials': dict(model=Testimonial, title='Testimonials', one='testimonial',
        fields=['name', 'role', 'message', 'photo', 'order', 'is_published'],
        columns=['name', 'role', 'order', 'is_published']),
    'gallery': dict(model=Gallery, title='Gallery', one='photo',
        fields=['title', 'description', 'category', 'image', 'is_published'],
        columns=['title', 'category', 'is_published']),
    'hero-slides': dict(model=HeroSlide, title='Hero Slides', one='slide',
        fields=['title', 'image', 'order', 'is_active'],
        columns=['title', 'order', 'is_active']),
    'banners': dict(model=Announcement, title='Website Banner', one='banner',
        fields=['text', 'link', 'is_active'],
        columns=['text', 'is_active']),
    'stats': dict(model=SchoolStat, title='School Numbers', one='number',
        fields=['value', 'label', 'order', 'is_active'],
        columns=['value', 'label', 'order', 'is_active']),
    'features': dict(model=Feature, title='Why Choose Us', one='feature',
        fields=['title', 'description', 'icon', 'order', 'is_active'],
        columns=['title', 'icon', 'order', 'is_active']),
    'quick-links': dict(model=QuickLink, title='Quick Links', one='link',
        fields=['label', 'description', 'url', 'order', 'is_active'],
        columns=['label', 'url', 'order', 'is_active']),
    'key-dates': dict(model=KeyDate, title='Key Dates', one='date',
        fields=['title', 'date', 'note', 'is_active'],
        columns=['title', 'date', 'is_active']),
    'downloads': dict(model=DownloadFile, title='Downloads', one='file',
        fields=['title', 'description', 'file', 'order', 'is_published'],
        columns=['title', 'order', 'is_published']),
    'faqs': dict(model=FAQ, title='FAQs', one='FAQ',
        fields=['question', 'answer', 'order', 'is_published'],
        columns=['question', 'order', 'is_published']),
}

GROUPS = [
    ('Content', ['events', 'news', 'achievements', 'testimonials', 'gallery']),
    ('Home page', ['hero-slides', 'banners', 'stats', 'features', 'quick-links']),
    ('Information', ['key-dates', 'downloads', 'faqs']),
]

SETTINGS_SECTIONS = [
    ('School identity', ['school_name', 'school_motto', 'tagline', 'logo', 'hero_image']),
    ('Admissions banner', ['admissions_open', 'admissions_text']),
    ("Principal's message", ['principal_name', 'principal_title', 'principal_photo', 'principal_message']),
    ('Contact and social media', ['phone', 'phone_list', 'whatsapp', 'email', 'website', 'address',
                                  'office_hours', 'map_embed_url', 'facebook', 'instagram', 'youtube']),
]


# ---------- Styled forms ----------
INPUT = ('mt-1 block w-full rounded-md border border-gray-300 shadow-sm p-2.5 sm:text-sm '
         'focus:border-blue-500 focus:ring-blue-500 bg-white')


class StyledForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            w = f.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs['class'] = 'mt-1 h-4 w-4 rounded border-gray-300 text-blue-600'
            elif isinstance(w, forms.FileInput):
                w.attrs['class'] = 'mt-1 block w-full text-sm text-gray-600'
            else:
                w.attrs['class'] = INPUT
            if isinstance(w, forms.Textarea):
                w.attrs['rows'] = 5
            if isinstance(f, forms.DateTimeField):
                f.widget = forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': INPUT},
                                               format='%Y-%m-%dT%H:%M')
                f.input_formats = ['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M']
            elif isinstance(f, forms.DateField):
                f.widget = forms.DateInput(attrs={'type': 'date', 'class': INPUT}, format='%Y-%m-%d')


def make_form(model, fields):
    return modelform_factory(model, form=StyledForm, fields=fields)


# ---------- Helpers ----------
def page(request, template, **ctx):
    ctx['groups'] = [(g, [(k, REGISTRY[k]['title']) for k in keys]) for g, keys in GROUPS]
    return render(request, template, ctx)


def get_cfg(key):
    cfg = REGISTRY.get(key)
    if not cfg:
        raise Http404
    return cfg


def cell(obj, name):
    field = obj._meta.get_field(name)
    value = getattr(obj, name)
    if field.choices:
        return getattr(obj, f'get_{name}_display')()
    if isinstance(value, datetime):
        if timezone.is_aware(value):
            value = timezone.localtime(value)
        return value.strftime('%d %b %Y, %I:%M %p')
    if isinstance(value, date):
        return value.strftime('%d %b %Y')
    return value


# ---------- Views ----------
@admin_required
def home(request):
    sections = []
    for group, keys in GROUPS:
        items = [dict(key=k, title=REGISTRY[k]['title'], count=REGISTRY[k]['model'].objects.count())
                 for k in keys]
        sections.append((group, items))
    return page(request, 'website/home.html', sections=sections, active='home', page_title='Manage website')


@admin_required
def site_settings(request):
    site = SiteSetting.load()
    all_fields = [f for _, names in SETTINGS_SECTIONS for f in names]
    form = make_form(SiteSetting, all_fields)(request.POST or None, request.FILES or None, instance=site)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Site settings saved.')
        return redirect('website:settings')
    sections = [(title, [form[n] for n in names]) for title, names in SETTINGS_SECTIONS]
    return page(request, 'website/form.html', form=form, sections=sections, active='settings',
                heading='Site Settings', page_title='Site Settings', back=None)


@admin_required
def item_list(request, key):
    cfg = get_cfg(key)
    model = cfg['model']
    pager = Paginator(model.objects.all(), 20).get_page(request.GET.get('page'))
    headers = [model._meta.get_field(c).verbose_name.capitalize() for c in cfg['columns']]
    rows = [dict(obj=o, cells=[cell(o, c) for c in cfg['columns']]) for o in pager]
    return page(request, 'website/list.html', key=key, cfg=cfg, headers=headers, rows=rows,
                pager=pager, active=key, page_title=cfg['title'])


@admin_required
def item_form(request, key, pk=None):
    cfg = get_cfg(key)
    obj = get_object_or_404(cfg['model'], pk=pk) if pk else None
    form = make_form(cfg['model'], cfg['fields'])(request.POST or None, request.FILES or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"{cfg['title']}: saved.")
        return redirect('website:list', key=key)
    heading = f"{'Edit' if obj else 'Add'} {cfg['one']}"
    return page(request, 'website/form.html', form=form, sections=[(None, list(form))], active=key,
                heading=heading, page_title=heading, back=key)


@admin_required
def item_delete(request, key, pk):
    cfg = get_cfg(key)
    obj = get_object_or_404(cfg['model'], pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Deleted.')
        return redirect('website:list', key=key)
    return page(request, 'website/delete.html', obj=obj, key=key, cfg=cfg, active=key, page_title='Delete')