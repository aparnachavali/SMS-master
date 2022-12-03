from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager
from django.dispatch import receiver
from django.db.models.signals import post_save
from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = CustomUser(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        assert extra_fields["is_staff"]
        assert extra_fields["is_superuser"]
        return self._create_user(email, password, **extra_fields)


class AcademicSession(models.Model):
    start_year = models.DateField()
    end_year = models.DateField()

    def __str__(self):
        return "From " + str(self.start_year) + " to " + str(self.end_year)


class CustomUser(AbstractUser):
    USER_TYPE = ((1, "HOD"), (2, "Staff"), (3, "Student"))
    GENDER = [("M", "Male"), ("F", "Female")]
    username = None  # Removed username, using email instead
    email = models.EmailField(unique=True)
    user_type = models.CharField(default=1, choices=USER_TYPE, max_length=1)
    gender = models.CharField(max_length=1, choices=GENDER)
    profile_pic = models.ImageField()
    address = models.TextField()
    fcm_token = models.TextField(default="")  # For firebase notifications
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return self.last_name + ", " + self.first_name


class Admin(models.Model):
    custom_user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.custom_user.last_name + ", " + self.custom_user.first_name


class Course(models.Model):
    name = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Student(models.Model):
    custom_user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    course = models.ForeignKey(
        Course, on_delete=models.DO_NOTHING, null=True, blank=False)
    session = models.ForeignKey(
        AcademicSession, on_delete=models.DO_NOTHING, null=True)

    def __str__(self):
        return self.custom_user.last_name + ", " + self.custom_user.first_name


class Instructor(models.Model):
    course = models.ForeignKey(
        Course, on_delete=models.DO_NOTHING, null=True, blank=False)
    custom_user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.custom_user.last_name + " " + self.custom_user.first_name


class Subject(models.Model):
    name = models.CharField(max_length=120)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Section(models.Model):
    staff = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    session = models.ForeignKey(AcademicSession, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['subject', 'staff', 'session'], name='unique_section')
        ]

    def __str__(self):
        return str(self.subject) + ";  Prof: " + str(self.staff) + ";  Session: " + str(self.session)


DAY_CHOICES = (
    ('Mon','Mon'),
    ('Tue', 'Tue'),
    ('Wed','Wed'),
    ('Thu','Thu'),
    ('Fri','Fri'),
)


class SectionTimeSlot(models.Model):
    timeslot = models.TimeField(default='10:00', verbose_name='time')
    day = models.CharField(default="Mon", max_length=3, choices=DAY_CHOICES)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['section', 'timeslot', 'day'], name='unique_timeslot')
        ]


class SectionStudents(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['section', 'student'], name='unique_section_students')
        ]


class Attendance(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class AttendanceReport(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE)
    status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LeaveReportStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LeaveReportStaff(models.Model):
    staff = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    date = models.CharField(max_length=60)
    message = models.TextField()
    status = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class FeedbackStaff(models.Model):
    staff = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    feedback = models.TextField()
    reply = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationStaff(models.Model):
    staff = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NotificationStudent(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class StaffNotificationStudent(models.Model):
    student_selected = models.BooleanField(default=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    staff = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    sender = models.TextField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class StudentNotificationStaff(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    staff = models.ForeignKey(Instructor, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Assignment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    name = models.TextField()
    file_name = models.FileField(upload_to=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class StudentResult(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    mid2 = models.TextField(default=0, verbose_name="Mid 2")
    mid1 = models.TextField(default=0, verbose_name="Mid 1")
    assignment1 = models.TextField(default=0, verbose_name="Assignment 1")
    assignment2 = models.TextField(default=0, verbose_name="Assignment 2")
    assignment3 = models.TextField(default=0, verbose_name="Assignment 3")
    assignment4 = models.TextField(default=0, verbose_name="Assignment 4")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.user_type == 1:
            Admin.objects.create(custom_user=instance)
        if instance.user_type == 2:
            Instructor.objects.create(custom_user=instance)
        if instance.user_type == 3:
            Student.objects.create(custom_user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    if instance.user_type == 1:
        instance.custom_user.save()
    if instance.user_type == 2:
        instance.instructor.save()
    if instance.user_type == 3:
        instance.student.save()
