from django import forms
from .models import Payment


class PaymentForm(forms.ModelForm):
    payment_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date", "class": "w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"})
    )

    class Meta:
        model = Payment
        fields = ["amount", "payment_date", "payment_method", "reference_number"]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm", "step": "0.01", "placeholder": "0.00"}),
            "payment_method": forms.Select(attrs={"class": "w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"}),
            "reference_number": forms.TextInput(attrs={"class": "w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm", "placeholder": "e.g. TRN-8820931"}),
        }