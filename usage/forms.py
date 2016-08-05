from django.forms import ModelForm
from .models import (
    University, UniversityD, UniversityDD, NovaUsage, HpcUsage)


class UniversityForm(ModelForm):
    class Meta:
        model = University
        fields = '__all__'


class UniversitydForm(ModelForm):
    class Meta:
        model = UniversityD
        fields = '__all__'


class UniversityddForm(ModelForm):
    class Meta:
        model = UniversityDD
        fields = '__all__'


class NovausageForm(ModelForm):
    class Meta:
        model = NovaUsage
        fields = '__all__'

class HpcusageForm(ModelForm):
    class Meta:
        model = HpcUsage
        fields = '__all__'
