import json

from django.contrib.auth import login
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model
from django.forms import model_to_dict
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from rest_framework import permissions, status
from rest_framework import views
from rest_framework.decorators import api_view

from .models import Student, Attendance, AttendanceClass, User, StudentCourse
from .serializer import LoginSerializer, StudentCourseSerializer
from rest_framework import generics


class ExtendedEncoder(DjangoJSONEncoder):

    def default(self, o):
        if isinstance(o, Model):
            return model_to_dict(o)

        return super().default(o)


class LoginView(views.APIView):
    # This view should be accessible also for unauthenticated users.
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        s = LoginSerializer(data=self.request.data,
                            context={'request': self.request})
        s.is_valid(raise_exception=True)
        user = s.validated_data['user']
        student = Student.objects.get(user=user)
        login(request, user)
        return JsonResponse(student, status=status.HTTP_202_ACCEPTED, encoder=ExtendedEncoder, safe=False)


@csrf_exempt
@api_view(["GET", "POST"])
def confirm(request):
    r = json.loads(request.body)
    assc = get_object_or_404(AttendanceClass, id=r["ass_c_id"])
    ass = assc.assign
    cr = ass.course
    cl = ass.class_id
    s = Student.objects.get(USN=r["USN"])
    status = 'True'
    if assc.status == 1:
        try:
            a = Attendance.objects.get(course=cr, student=s, date=assc.date, attendanceclass=assc)
            a.status = status
            a.save()
        except Attendance.DoesNotExist:
            a = Attendance(course=cr, student=s, status=status, date=assc.date, attendanceclass=assc)
            a.save()
    else:
        a = Attendance(course=cr, student=s, status=status, date=assc.date, attendanceclass=assc)
        a.save()
        assc.status = 1
        assc.save()
    return JsonResponse(a, encoder=ExtendedEncoder, safe=False)


class StudentCourseList(generics.ListAPIView):
    serializer_class = StudentCourseSerializer

    def get_queryset(self):
        """
        This view should return a list of all the studentcourses
        for the currently authenticated user.
        """
        usn = self.request.query_params.get("USN", "")
        student = Student.objects.get(USN=usn)
        return StudentCourse.objects.filter(student=student)


@csrf_exempt
@api_view(["GET", "POST"])
def getUnits(request):
    r = json.loads(request.body)
    student = Student.objects.get(USN=r["USN"])
    student_courses = StudentCourse.objects.filter(student=student)
    return JsonResponse(student_courses.all(), encoder=ExtendedEncoder, safe=False)
