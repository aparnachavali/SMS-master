from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.contrib import messages
from .models import Section, Instructor, Student, StudentResult
from .forms import EditResultForm
from django.urls import reverse


class EditResultView(View):
    def get(self, request, *args, **kwargs):
        resultForm = EditResultForm()
        staff = get_object_or_404(Instructor, custom_user=request.user)
        resultForm.fields['section'].queryset = Section.objects.filter(staff=staff)
        context = {
            'form': resultForm,
            'page_title': "Edit Student's Result"
        }
        return render(request, "staff_template/edit_student_result.html", context)

    def post(self, request, *args, **kwargs):
        form = EditResultForm(request.POST)
        context = {'form': form, 'page_title': "Edit Student's Result"}
        if form.is_valid():
            try:
                student = form.cleaned_data.get('student')
                section = form.cleaned_data.get('section')
                assignment1 = form.cleaned_data.get('assignment1')
                assignment2 = form.cleaned_data.get('assignment2')
                assignment3 = form.cleaned_data.get('assignment3')
                assignment4 = form.cleaned_data.get('assignment4')
                mid1 = form.cleaned_data.get('mid1')
                mid2 = form.cleaned_data.get('mid2')
                # Validating
                result = StudentResult.objects.get(student=student, section=section)
                result.mid1 = mid1
                result.mid2 = mid2
                result.assignment1 = assignment1
                result.assignment2 = assignment2
                result.assignment3 = assignment3
                result.assignment4 = assignment4
                result.save()
                messages.success(request, "Result Updated")
                return redirect(reverse('edit_student_result'))
            except Exception as e:
                messages.warning(request, "Result Could Not Be Updated")
        else:
            messages.warning(request, "Result Could Not Be Updated")
        return render(request, "staff_template/edit_student_result.html", context)
