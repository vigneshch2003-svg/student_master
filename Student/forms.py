from django import forms
from .models import Student, Marks, Course


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'fb-input'}),
            'description': forms.Textarea(attrs={'class': 'fb-textarea', 'rows': 3}),
        }


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        exclude = ['user']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'fb-input'}),
            'roll_number': forms.TextInput(attrs={'class': 'fb-input'}),
            'email': forms.EmailInput(attrs={'class': 'fb-input'}),
            'phone': forms.TextInput(attrs={'class': 'fb-input'}),
            'course': forms.Select(attrs={'class': 'fb-select'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'fb-input', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'fb-textarea', 'rows': 3}),
            'gender': forms.Select(attrs={'class': 'fb-select'}),
            'year': forms.NumberInput(attrs={'class': 'fb-input'}),
        }


class MarksForm(forms.ModelForm):
    class Meta:
        model = Marks
        fields = '__all__'
        widgets = {
            'student': forms.Select(attrs={'class': 'fb-select'}),
            'subject': forms.TextInput(attrs={'class': 'fb-input'}),
            'marks_obtained': forms.NumberInput(attrs={'class': 'fb-input'}),
            'total_marks': forms.NumberInput(attrs={'class': 'fb-input'}),
        }

    def __init__(self, *args, **kwargs):
        student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        if student:
            # Restrict student dropdown to same course only
            if student.course:
                self.fields['student'].queryset = Student.objects.filter(course=student.course)
            else:
                self.fields['student'].queryset = Student.objects.filter(pk=student.pk)
            self.fields['student'].initial = student.pk

    def clean(self):
        cleaned_data = super().clean()
        total_marks = cleaned_data.get('total_marks')
        marks_obtained = cleaned_data.get('marks_obtained')
        if total_marks == 0:
            raise forms.ValidationError("Total marks cannot be zero.")
        if marks_obtained is not None and total_marks is not None and marks_obtained > total_marks:
            raise forms.ValidationError("Marks obtained cannot exceed total marks.")
        return cleaned_data
