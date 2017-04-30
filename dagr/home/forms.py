from django import forms

class DocumentForm(forms.Form):
    docFile = forms.FileField(label="select a local file")

