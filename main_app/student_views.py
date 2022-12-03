import json
import math
from datetime import datetime, time

from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,
                              redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .forms import *
from .models import *


def student_home(request):
    student = get_object_or_404(Student, custom_user=request.user)
    total_subject = SectionStudents.objects.filter(student=student).count()
    total_attendance = AttendanceReport.objects.filter(student=student).count()
    total_present = AttendanceReport.objects.filter(
        student=student, status__in=[True]).count()
    if total_attendance == 0:  # Don't divide. DivisionByZero
        percent_absent = percent_present = 0
    else:
        percent_present = math.floor((total_present / total_attendance) * 100)
        percent_absent = math.ceil(100 - percent_present)
    subject_name = []
    data_present = []
    data_absent = []
    section_students = SectionStudents.objects.filter(student=student)

    for ss in section_students:
        attendance = Attendance.objects.filter(section=ss.section)
        present_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status__in=[True], student=student).count()
        absent_count = AttendanceReport.objects.filter(
            attendance__in=attendance, status__in=[False], student=student).count()
        subject_name.append(ss.section.subject)
        data_present.append(present_count)
        data_absent.append(absent_count)
    context = {
        'total_attendance': total_attendance,
        'percent_present': percent_present,
        'percent_absent': percent_absent,
        'total_subject': total_subject,
        'data_present': data_present,
        'data_absent': data_absent,
        'data_name': subject_name,
        'page_title': 'Student Homepage'

    }
    return render(request, 'student_template/home_content.html', context)


@csrf_exempt
def student_view_attendance(request):
    student = get_object_or_404(Student, custom_user=request.user)
    if request.method != 'POST':
        section_students = SectionStudents.objects.filter(student=student)
        sections = []
        for ss in section_students:
            sections.append(ss.section)
        context = {
            'sections': sections,
            'page_title': 'View Attendance'
        }
        return render(request, 'student_template/student_view_attendance.html', context)
    else:
        section_id = request.POST.get('section')
        start = request.POST.get('start_date')
        end = request.POST.get('end_date')
        print("sectionid: " + str(section_id))
        try:
            section = get_object_or_404(Section, id=section_id)
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
            attendance = Attendance.objects.filter(
                date__range=(start_date, end_date), section=section)
            attendance_reports = AttendanceReport.objects.filter(
                attendance__in=attendance, student=student)
            json_data = []
            for report in attendance_reports:
                data = {
                    "date": str(report.attendance.date),
                    "status": report.status
                }
                json_data.append(data)
            return JsonResponse(json.dumps(json_data), safe=False)
        except Exception as e:
            print(e)
            return None


def student_apply_leave(request):
    form = LeaveReportStudentForm(request.POST or None)
    student = get_object_or_404(Student, custom_user=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStudent.objects.filter(student=student),
        'page_title': 'Apply for leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('student_apply_leave'))
            except Exception:
                messages.error(request, "Could not submit")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "student_template/student_apply_leave.html", context)


def student_feedback(request):
    form = FeedbackStudentForm(request.POST or None)
    student = get_object_or_404(Student, custom_user=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStudent.objects.filter(student=student),
        'page_title': 'Student Feedback'

    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.student = student
                obj.save()
                messages.success(
                    request, "Feedback submitted for review")
                return redirect(reverse('student_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "student_template/student_feedback.html", context)


def student_view_profile(request):
    student = get_object_or_404(Student, custom_user=request.user)
    form = StudentEditForm(request.POST or None, request.FILES or None,
                           instance=student)
    context = {'form': form,
               'page_title': 'View/Edit Profile'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = student.custom_user
                if password != None:
                    admin.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    admin.profile_pic = passport_url
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                student.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('student_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))

    return render(request, "student_template/student_view_profile.html", context)


@csrf_exempt
def student_fcmtoken(request):
    token = request.POST.get('token')
    student_user = get_object_or_404(CustomUser, id=request.user.id)
    try:
        student_user.fcm_token = token
        student_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def student_view_notification(request):
    student = get_object_or_404(Student, custom_user=request.user)
    notifications = NotificationStudent.objects.filter(student=student)
    context = {
        'notifications': notifications,
        'page_title': "View Admin Notifications"
    }
    return render(request, "student_template/student_view_notification.html", context)


def student_view_staff_notification(request):
    student = get_object_or_404(Student, custom_user=request.user)
    notifications = StaffNotificationStudent.objects.filter(
        student=student, sender="staff")
    context = {
        'notifications': notifications,
        'page_title': "View Staff Notifications"
    }
    return render(request, "student_template/student_view_staff_notification.html", context)


def student_view_result(request):
    student = get_object_or_404(Student, custom_user=request.user)
    results = StudentResult.objects.filter(student=student)
    context = {
        'results': results,
        'page_title': "View Results"
    }
    return render(request, "student_template/student_view_result.html", context)


def student_add_subject(request):
    student = get_object_or_404(Student, custom_user=request.user)
    form = StudentSubjectForm(student, request.POST)
    context = {'form': form,
               'page_title': 'Add subject'
               }
    if request.method == 'POST':
        try:
            if form.is_valid():
                section = form.cleaned_data.get('section')
                existing_sections = SectionStudents.objects.filter(
                    student=student)
                if existing_sections.count() >= 3:
                    messages.error(
                        request, "Cannot to add more than 3 subjects")
                    return redirect(reverse('student_add_subject'))
                section = get_object_or_404(Section, id=section.id)
                ss = SectionStudents()
                ss.student = student
                ss.section = section
                ss.save()
                messages.success(request, "Subject Added!")
                return redirect(reverse('student_add_subject'))
            else:
                messages.error(request, "Invalid Data Provided")
        except Exception as e:
            messages.error(
                request, "Error Occured While Adding Subject" + str(e))

    return render(request, "student_template/student_add_subjects.html", context)


def student_manage_subjects(request):
    student = get_object_or_404(Student, custom_user=request.user)
    section_data = []
    student_sections = SectionStudents.objects.filter(student=student)
    for ss in student_sections:
        section_timeslots = SectionTimeSlot.objects.filter(section=ss.section)
        timeslot = ""
        for ts in section_timeslots:
            t = time.fromisoformat(str(ts.timeslot))
            timeslot += t.strftime("%H:%M") + " " + ts.day + ", "
        timeslot = timeslot[:-2]
        data = {
            'section': ss.section,
            'timeslot': timeslot
        }
        section_data.append(data)
    context = {
        'section_data': section_data,
        'page_title': 'Manage Subjects'
    }

    return render(request, "student_template/student_manage_subjects.html", context)


@csrf_exempt
def student_fcmtoken(request):
    token = request.POST.get('token')
    student_user = get_object_or_404(CustomUser, id=request.user.id)
    try:
        student_user.fcm_token = token
        student_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def student_notify_staff(request):
    student = get_object_or_404(Student, custom_user=request.user)
    student_sections = SectionStudents.objects.filter(student=student)

    staffSubjects = []
    for ss in student_sections:
        staffSubjects.append({
            'staff': ss.section.staff,
            'subject': ss.section.subject.name
        })
    context = {
        'page_title': "Send Notifications To Staff",
        'staffSubjects': staffSubjects,
    }
    return render(request, "student_template/staff_notification.html", context)


@csrf_exempt
def student_staff_notification(request):
    student = get_object_or_404(Student, custom_user=request.user)
    id = request.POST.get('id')
    message = request.POST.get('message')
    staff = get_object_or_404(Instructor, custom_user_id=id)
    try:
        notification = StaffNotificationStudent()
        notification.student = student
        notification.staff = staff
        notification.message = message
        notification.sender = "student"
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


@csrf_exempt
def student_subject_delete(request, section_id):
    try:
        student = get_object_or_404(Student, custom_user=request.user)
        student_subject = get_object_or_404(
            SectionStudents, student=student, section_id=section_id)
        student_subject.delete()
        messages.success(request, "Subject deleted successfully!")
        return redirect(reverse('student_manage_subjects'))

    except Exception as e:
        return e


def student_add_assignment(request):
    student = get_object_or_404(Student, custom_user=request.user)
    form = AssignmentForm(student, request.POST or None, request.FILES or None)
    context = {
        'form': form,
        'page_title': 'Add Assignment'
    }
    if request.method == 'POST':
        print(form.data.get('file_name'))
        if form.is_valid():
            name = form.cleaned_data.get('name')
            section = form.cleaned_data.get('section')
            passport = form.cleaned_data.get('file_name')
            try:
                assignment = Assignment()
                assignment.student = student
                if passport is not None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    assignment.file_name = passport_url
                assignment.section = section
                assignment.name = name
                assignment.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('student_add_assignment'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
        else:
            messages.error(request, "Fill Form Properly")
    return render(request, 'student_template/student_assignment_upload_template.html', context)


def student_manage_assignments(request):
    student = get_object_or_404(Student, custom_user=request.user)
    section_students = SectionStudents.objects.filter(student=student)
    sections = []
    for ss in section_students:
        sections.append(ss.section)
    context = {
        'sections': sections,
        'page_title': 'Manage Assignments'
    }
    return render(request, "student_template/student_manage_assignments.html", context)


@csrf_exempt
def student_get_assignments(request):
    student = get_object_or_404(Student, custom_user=request.user)
    try:
        section_id = request.POST.get('section')
        section = get_object_or_404(Section, id=section_id)
        assignements = Assignment.objects.filter(student=student, section=section)
        assignement_data = []
        for assignment in assignements:
            data = {
                'id': assignment.id,
                'name': assignment.name,
                'url': assignment.file_name.url
            }
            assignement_data.append(data)
        return HttpResponse(json.dumps(assignement_data))
    except Exception as e:
        print(e)
        return HttpResponse('False')


@csrf_exempt
def student_assignment_delete(request, assignment_id):
    try:
        student = get_object_or_404(Student, custom_user=request.user)
        assignment = get_object_or_404(Assignment, id=assignment_id, student=student)
        assignment.delete()
        messages.success(request, "Assignment deleted successfully!")
        return redirect(reverse('student_manage_assignments'))

    except Exception as e:
        return e
