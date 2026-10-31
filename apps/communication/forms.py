from django import forms
from .models import Announcement

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'target_role', 'is_pinned', 'expires_at', 'body']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-800 text-sm transition',
                'placeholder': 'e.g. End of First Term Resumption Date',
                'maxlength': '200',
                'x-model': 'titleText',
            }),
            'target_role': forms.Select(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-800 text-sm transition bg-white'
            }),
            'is_pinned': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500'
            }),
            'expires_at': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-800 text-sm transition bg-white'
            }),
            'body': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-slate-800 text-sm transition',
                'rows': 6,
                'placeholder': 'Write the full body of the announcement here...',
                'x-model': 'bodyText',
            }),
        }