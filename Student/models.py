from django.db import models
from django.contrib.auth.models import User


class Course(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='student_profile')
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    phone = models.CharField(max_length=10)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, null=True, blank=True)
    date_of_birth = models.DateField()
    address = models.TextField()
    profile_image = models.ImageField(upload_to='student_profiles/', null=True, blank=True)
    gender = models.CharField(max_length=10, choices=(('Male', 'Male'), ('Female', 'Female')))
    year = models.IntegerField()

    def __str__(self):
        return self.name

    @property
    def cgpa(self):
        """Average percentage across all subjects converted to 10-point CGPA."""
        marks = list(self.marks_set.all())
        if not marks:
            return None
        avg_pct = sum(m.percentage for m in marks) / len(marks)
        return round(avg_pct / 10, 2)


class Marks(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE) #one suject marks can be assinged to many student.
    subject = models.CharField(max_length=100)
    marks_obtained = models.IntegerField()
    total_marks = models.IntegerField(default=100)

    @property                           #property is used to calculate values without storing them in the database. It allows us to define a method that can be accessed like an attribute.
    def percentage(self):
        return (self.marks_obtained / self.total_marks) * 100

    @property
    def grade(self):
        if self.percentage >= 90:
            return 'A'
        elif self.percentage >= 80:
            return 'B'
        elif self.percentage >= 70:
            return 'C'
        elif self.percentage >= 60:
            return 'D'
        else:
            return 'F'

    def __str__(self):
        return f"{self.student.name} - {self.subject}"
