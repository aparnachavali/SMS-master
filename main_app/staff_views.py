import json

import requests
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (
    HttpResponseRedirect, get_object_or_404, redirect, render)
from django.templatetags.static import static
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from datetime import date
from .forms import *
from .models import *

days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']


def staff_home(request):
    staff = get_object_or_404(Instructor, custom_user=request.user)
    total_leave = LeaveReportStaff.objects.filter(staff=staff).count()
    sections = Section.objects.filter(staff=staff)
    students = set()
    for section in sections:
        section_students = SectionStudents.objects.filter(section=section)
        for ss in section_students:
            students.add(ss.student.id)
    total_students = len(students)
    total_sections = sections.count()
    attendance_list = Attendance.objects.filter(section__in=sections)
    total_attendance = attendance_list.count()
    attendance_list = []
    sections_list = []
    for section in sections:
        attendance_count = Attendance.objects.filter(section=section).count()
        sections_list.append(str(section.subject) + " " + str(section.session))
        attendance_list.append(attendance_count)
    context = {
        'page_title': 'Instructor Panel - ' + str(staff.custom_user.last_name) + ' (' + str(staff.course) + ')',
        'total_students': total_students,
        'total_attendance': total_attendance,
        'total_leave': total_leave,
        'total_sections': total_sections,
        'sections_list': sections_list,
        'attendance_list': attendance_list
    }
    return render(request, 'staff_template/home_content.html', context)


def staff_take_attendance(request):
    staff = get_object_or_404(Instructor, custom_user=request.user)
    sections = Section.objects.filter(staff=staff)
    context = {
        'sections': sections,
        'page_title': 'Take Attendance'
    }

    return render(request, 'staff_template/staff_take_attendance.html', context)


@csrf_exempt
def get_students(request):
    section_id = request.POST.get('section')
    try:
        section = get_object_or_404(Section, id=section_id)

        section_students = SectionStudents.objects.filter(section=section)

        student_data = []
        for ss in section_students:
            data = {
                "id": ss.student.id,
                "name": ss.student.custom_user.last_name + " " + ss.student.custom_user.first_name
            }
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return e


@csrf_exempt
def get_students_with_date(request):
    section_id = request.POST.get('section')
    selected_date = request.POST.get('date')

    try:
        section = get_object_or_404(Section, id=section_id)

        section_students = SectionStudents.objects.filter(section=section)

        student_data = []
        for ss in section_students:
            student_leave = LeaveReportStudent.objects.filter(
                date=selected_date, student=ss.student, status=1)
            if len(student_leave) > 0:
                data = {
                    "id": ss.student.id,
                    "name": ss.student.custom_user.last_name + " " + ss.student.custom_user.first_name + " (on leave)"
                }
                student_data.append(data)
            else:
                data = {
                    "id": ss.student.id,
                    "name": ss.student.custom_user.last_name + " " + ss.student.custom_user.first_name
                }
                student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return e


@csrf_exempt
def save_attendance(request):
    student_data = request.POST.get('student_ids')
    selected_date = request.POST.get('date')
    section_id = request.POST.get('section')
    students = json.loads(student_data)
    try:
        section = get_object_or_404(Section, id=section_id)
        attendance = Attendance(section=section, date=selected_date)
        attendance.save()
        section_time_slots = SectionTimeSlot.objects.filter(section=section)
        is_slot_valid = False
        for ts in section_time_slots:
            sd = date.fromisoformat(selected_date)
            if ts.day == days[sd.weekday()]:
                is_slot_valid = True
        if not is_slot_valid:
            return HttpResponse("TSI")
        for student_dict in students:
            student = get_object_or_404(Student, id=student_dict.get('id'))
            attendance_report = AttendanceReport(student=student, attendance=attendance,
                                                 status=student_dict.get('status'))
            attendance_report.save()
    except Exception as e:
        return None

    return HttpResponse("OK")


def staff_update_attendance(request):
    staff = get_object_or_404(Instructor, custom_user=request.user)
    sections = Section.objects.filter(staff=staff)
    context = {
        'sections': sections,
        'page_title': 'Update Attendance'
    }

    return render(request, 'staff_template/staff_update_attendance.html', context)


@csrf_exempt
def get_student_attendance(request):
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        date = get_object_or_404(Attendance, id=attendance_date_id)
        attendance_data = AttendanceReport.objects.filter(attendance=date)
        student_data = []
        for attendance in attendance_data:
            data = {"id": attendance.student.custom_user.id,
                    "name": attendance.student.custom_user.last_name + " " + attendance.student.custom_user.first_name,
                    "status": attendance.status}
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return e


@csrf_exempt
def staff_get_attendance(request):
    section = request.POST.get('section')
    try:
        attendances = Attendance.objects.filter(section=section)
        attendance_list = []
        for attd in attendances:
            data = {
                "id": attd.id,
                "attendance_date": str(attd.date),
                "section_id": str(attd.section.id)
            }
            attendance_list.append(data)
        return JsonResponse(json.dumps(attendance_list), safe=False)
    except Exception as e:
        return None


@csrf_exempt
def update_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    students = json.loads(student_data)
    try:
        attendance = get_object_or_404(Attendance, id=date)

        for student_dict in students:
            student = get_object_or_404(
                Student, custom_user_id=student_dict.get('id'))
            attendance_report = get_object_or_404(
                AttendanceReport, student=student, attendance=attendance)
            attendance_report.status = student_dict.get('status')
            attendance_report.save()
    except Exception as e:
        return None

    return HttpResponse("OK")


def staff_apply_leave(request):
    form = LeaveReportStaffForm(request.POST or None)
    staff = get_object_or_404(Instructor, custom_user_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStaff.objects.filter(staff=staff),
        'page_title': 'Apply for Leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('staff_apply_leave'))
            except Exception:
                messages.error(request, "Could not apply!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_apply_leave.html", context)


def staff_feedback(request):
    form = FeedbackStaffForm(request.POST or None)
    staff = get_object_or_404(Instructor, custom_user_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStaff.objects.filter(staff=staff),
        'page_title': 'Add Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(request, "Feedback submitted for review")
                return redirect(reverse('staff_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_feedback.html", context)


def staff_view_profile(request):
    staff = get_object_or_404(Instructor, custom_user=request.user)
    form = StaffEditForm(request.POST or None,
                         request.FILES or None, instance=staff)
    context = {'form': form, 'page_title': 'View/Update Profile'}
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                custom_user = staff.custom_user
                if password != None:
                    custom_user.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    custom_user.profile_pic = passport_url
                custom_user.first_name = first_name
                custom_user.last_name = last_name
                custom_user.address = address
                custom_user.gender = gender
                custom_user.save()
                staff.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('staff_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
                return render(request, "staff_template/staff_view_profile.html", context)
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
            return render(request, "staff_template/staff_view_profile.html", context)

    return render(request, "staff_template/staff_view_profile.html", context)


@csrf_exempt
def staff_fcmtoken(request):
    token = request.POST.get('token')
    try:
        staff_user = get_object_or_404(CustomUser, id=request.user.id)
        staff_user.fcm_token = token
        staff_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def staff_view_notification(request):
    staff = get_object_or_404(Instructor, custom_user=request.user)
    notifications = NotificationStaff.objects.filter(staff=staff)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "staff_template/staff_view_notification.html", context)


def staff_add_result(request):
    staff = get_object_or_404(Instructor, custom_user=request.user)
    sections = Section.objects.filter(staff=staff)
    context = {
        'page_title': 'Result Upload',
        'sections': sections
    }
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_list')
            section_id = request.POST.get('section')
            mid1 = request.POST.get('mid1')
            mid2 = request.POST.get('mid2')
            assignment1 = request.POST.get('assignment1')
            assignment2 = request.POST.get('assignment2')
            assignment3 = request.POST.get('assignment3')
            assignment4 = request.POST.get('assignment4')
            student = get_object_or_404(Student, id=student_id)
            section = get_object_or_404(Section, id=section_id)
            try:
                data = StudentResult.objects.get(
                    student=student, section=section)
                data.mid1 = mid1
                data.mid2 = mid2
                data.assignment1 = assignment1
                data.assignment2 = assignment2
                data.assignment3 = assignment3
                data.assignment4 = assignment4
                data.save()
                messages.success(request, "Scores Updated")
            except:
                result = StudentResult(student=student, section=section)
                result.mid1 = mid1
                result.mid2 = mid2
                result.assignment1 = assignment1
                result.assignment2 = assignment2
                result.assignment3 = assignment3
                result.assignment4 = assignment4
                result.save()
                messages.success(request, "Scores Saved")
        except Exception as e:
            messages.warning(request, "Error Occured While Processing Form"+request.POST.get('assignment3'))
    return render(request, "staff_template/staff_add_result.html", context)


@csrf_exempt
def fetch_student_result(request):
    try:
        section_id = request.POST.get('section')
        student_id = request.POST.get('student')
        student = get_object_or_404(Student, id=student_id)
        section = get_object_or_404(Section, id=section_id)
        result = StudentResult.objects.get(student=student, section=section)
        result_data = {
            'mid1': result.mid1,
            'mid2': result.mid2,
            'assignment1': result.assignment1,
            'assignment2': result.assignment2,
            'assignment3': result.assignment3,
            'assignment4': result.assignment4,
        }
        return HttpResponse(json.dumps(result_data))
    except Exception as e:
        return HttpResponse('False')


def staff_notify_student(request):
    staff = get_object_or_404(Instructor, custom_user=request.user)

    student = CustomUser.objects.filter(user_type=3)
    context = {
        'page_title': "Send Notifications To Students",
        'students': student
    }
    return render(request, "staff_template/student_notification.html", context)


@csrf_exempt
def staff_student_notification(request):
    staff = get_object_or_404(Instructor, custom_user=request.user)
    student_id = request.POST.get('student_id')
    message = request.POST.get('message')
    student = get_object_or_404(Student, custom_user_id=student_id)
    try:
        notification = StaffNotificationStudent()
        notification.student = student
        notification.staff = staff
        notification.message = message
        notification.sender = "staff"
        notification.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def staff_view_student_notification(request):
    staff = get_object_or_404(Instructor, custom_user=request.user)
    notifications = StaffNotificationStudent.objects.filter(
        staff=staff, sender="student")
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "staff_template/staff_view_student_notification.html", context)


def staff_view_assignment(request):
    staff = get_object_or_404(Instructor, custom_user=request.user)
    sections = Section.objects.filter(staff=staff)
    context = {
        'sections': sections,
        'page_title': "View Assignment Submissions"
    }
    return render(request, "staff_template/staff_view_assignment.html", context)

@csrf_exempt
def get_assignments(request):
    try:
        section_id = request.POST.get('section')
        student_id = request.POST.get('student_id')
        student = get_object_or_404(Student, id=student_id)
        section = get_object_or_404(Section, id=section_id)
        assignements = Assignment.objects.filter(student=student, section=section)
        assignement_data = []
        for assignment in assignements:
            data = {
                'name': assignment.name,
                'url': assignment.file_name.url
            }
            assignement_data.append(data)
        return HttpResponse(json.dumps(assignement_data))
    except Exception as e:
        print(e)
        return HttpResponse('False')
