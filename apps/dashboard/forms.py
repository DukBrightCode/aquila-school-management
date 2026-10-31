from apps.academics.models import AssessmentType
from apps.academics.models import GradingScale
from apps.academics.models import PredefinedRemark
from django import forms


class AssessmentTypeForm(forms.ModelForm):

  class Meta:
    model = AssessmentType
    fields = ['name', 'weight_percentage', 'max_score', 'term']
    widgets = {
        'name': forms.TextInput(
            attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border'
            }
        ),
        'weight_percentage': forms.NumberInput(
            attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border'
            }
        ),
        'max_score': forms.NumberInput(
            attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border'
            }
        ),
        'term': forms.Select(
            attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border'
            }
        ),
    }
    
    
    

#Grading Scale Classes



class GradingScaleForm(forms.ModelForm):

  class Meta:
    model = GradingScale
    fields = ['grade_letter', 'min_score', 'max_score', 'remark']
    widgets = {
        'grade_letter': forms.TextInput(
            attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border'
            }
        ),
        'min_score': forms.NumberInput(
            attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border'
            }
        ),
        'max_score': forms.NumberInput(
            attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border'
            }
        ),
        'remark': forms.TextInput(
            attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2 border'
            }
        ),
    }
    


class PredefinedRemarkForm(forms.ModelForm):

  class Meta:
    model = PredefinedRemark
    fields = ['type', 'text']
    widgets = {
        'type': forms.Select(
            attrs={
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2.5'
                    ' border focus:ring-blue-500 focus:border-blue-500'
                    ' sm:text-sm bg-white'
                )
            }
        ),
        'text': forms.Textarea(
            attrs={
                'class': (
                    'mt-1 block w-full rounded-md border-gray-300 shadow-sm p-2.5'
                    ' border focus:ring-blue-500 focus:border-blue-500'
                    ' sm:text-sm'
                ),
                'rows': 3,
                'placeholder': (
                    'e.g., Shows commendable improvement in class participation'
                    ' and assignments.'
                ),
            }
        ),
    }
    labels = {
        'type': 'Remark Authority Level',
        'text': 'Remark Statement',
    }