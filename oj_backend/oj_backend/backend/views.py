#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2018 ericdiao <hi@ericdiao.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed
from rest_framework.parsers import JSONParser
try:
    from django.utils import simplejson
except:
    import simplejson

from oj_backend.backend.models import Student, Instructor, Course, Assignment, Record
from oj_backend.backend.utils import student_active_test, student_test, student_taking_course_test, student_submit_assignment_test, return_http_401, return_http_405
from oj_backend.backend.serializers import *


def student_login(request):
    """
    /student/login/
    """
    if request.method == 'GET':
        return return_http_405()
    username = request.POST['username']
    password = request.POST['password']
    user = authenticate(request, username=username, password=password)
    if user:
        login(request, user)
        return JsonResponse({'message': 'Success'}, status=204)
    else:
        return return_http_401()


def student_logout(request):
    """
    /student/logout/
    """
    logout(request)
    return JsonResponse({'message': 'Success'}, status=204)


@login_required
def student_info(request, id):
    """
    /student/<str:id>/
    """
    if not student_test(request, id):
        return return_http_401()

    if request.method == 'GET':
        student = Student.objects.get(uid=id)
        serializer = StudentBasicInfoSerializer(student)
        return JsonResponse(serializer.data, safe=False)
    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = StudentBasicInfoSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
    else:
        return return_http_405()


@login_required
def student_course_list(request, id):
    """
    /student/<str:id>/course/
    """
    if not student_test(request, id):
        return return_http_401()

    if request.method == 'GET':
        courses = Course.objects.filter(student__uid__contains=id)
        serializer = StudentCoursesSerializer(courses, many=True)
        return JsonResponse(serializer.data, safe=False)
    else:
        return return_http_405()


@login_required
def student_course_assginment_list(request, id, course_id):
    """
    /student/<str:id>/course/<str:course_id>/
    """
    if not (student_taking_course_test(request, course_id) and student_test(request, id)):
        return return_http_401()

    if request.method == 'GET':
        assignments = Assignment.objects.filter(
            course__uid__contains=course_id)
        serializer = StudentAssignmentSerializer(assignments, many=True)
        return JsonResponse(serializer.data, safe=False)
    else:
        return return_http_405()


@login_required
def student_assignment_detail(request, id, course_id, assignment_id):
    """
    /student/<str:id>/course/<str:course_id>/<str:assignment_id>/
    """
    if not student_taking_course_test(request, course_id) and student_test(request, id):
        return return_http_401()

    if request.method == 'GET':
        assignments = Assignment.objects.filter(
            uid=assignment_id)
        serializer = StudentAssignmentSerializer(assignments, many=True)
        return JsonResponse(serializer.data, safe=False)
    else:
        return return_http_405()


@login_required
def stutdent_assignment_history_list(request, id, course_id, assignment_id):
    """
    /student/<str:id>/course/<str:course_id>/<str:assignment_id>/history/
    """
    if not (student_taking_course_test(request, course_id) and student_test(request, id)):
        return return_http_401()

    if request.method == 'GET':
        records = Record.objects.filter(
            assignment__uid__contain=assignment_id, student__uid__contain=id)
        serializer = StudentSubmissionRecordSerializer(records, many=True)
        return JsonResponse(serializer.data, safe=False)
    else:
        return return_http_405()


@login_required
def course_info(request, course_id):
    """
    /course/<str:course_id>/
    """
    if not student_taking_course_test(request, course_id):
        return return_http_401()

    if request.method == 'GET':
        course = Course.objects.get(uid=course_id)
        serializer = StudentCoursesSerializer(course)
        return JsonResponse(serializer.data, safe=False)
    else:
        return return_http_405


@login_required
def course_assignment_info(request, course_id, assignment_id):
    """
    /course/<str:course_id>/<str:assignment_id>/
    """
    if not student_taking_course_test(request, course_id):
        return return_http_401()

    if request.method == 'GET':
        assignment = Assignment.objects.get(uid=assignment_id)
        serializer = StudentAssignmentSerializer(assignment)
        return JsonResponse(serializer.data, safe=False)
    else:
        return return_http_405()


@login_required
def course_assignment_scores(request, course_id, assignment_id):
    """
    /course/<str:course_id>/<str:assignment_id>/scores/
    """
    if not student_taking_course_test(request, course_id):
        return return_http_401()

    if request.method == 'GET':
        # must be improved using other ways.
        records = None
        this_course = Course.objects.get(uid=course_id)
        all_records = Record.objects.filter(
            assignment__uid__contains=assignment_id)
        students = this_course.objects.student_set.all()
        for student in students:
            student_uid = student.uid
            try:
                this_student_record = all_records.filter(
                    student__uid__contains=student_uid).order_by('-submission_time')[0]
                if records:
                    records = records | this_student_record
                else:
                    records = this_student_record
            except IndexError:
                pass
        records = records.order_by('submission_time')
        serializer = ScoreBoardSerializer(records, many=True)
        return JsonResponse(serializer.data, safe=False)
    else:
        return return_http_405()


@login_required
def course_judging_queue(request, course_id):
    """
    /course/<str:course_id>/queue/
    """
    return JsonResponse(simplejson.dump({'massage': "Coming soon"}), status=500)
