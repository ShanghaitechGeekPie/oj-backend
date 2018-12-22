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
from django.views import View
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed
from rest_framework.parsers import JSONParser
from rest_framework import status
try:
    from django.utils import simplejson
except:
    import simplejson

import oj_backend.backend.middleware_connector as mw_connector
from oj_backend.backend.models import Student, Instructor, Course, Assignment, Record, Judge, PendingAssignment
from oj_backend.backend.utils import student_active_test, student_test, insturctor_test, student_taking_course_test, student_submit_assignment_test, instructor_giving_course_test, regrade_assignment, return_http_401, return_http_405, return_http_403, return_http_400, return_http_200, return_http_404
from oj_backend.backend.serializers import *

class studentInfomation(View):
    """
    Supported method: `POST`, `GET`

    Registered at `/student/<str:id>/` where id is the uid of the student in
    the database.

    It will return the student's basic information, including `uid`, `name`,
    `email` and `student_id`.
    """

    def get(self, request, id):
        if not student_test(request, id):
            return return_http_403()

        student = Student.objects.get(uid=id)
        serializer = StudentInfoSerializer(student)
        return JsonResponse(serializer.data, safe=False)

    def post(self, request, id):
        if not student_test(request, id):
            return return_http_403()
        serializer = StudentInfoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class insturctorInfomation(View):
    """
    Supported method: `POST`, `GET`

    Registered at `/insturctor/<str:id>/` where id is the uid of the student in
    the database.
    """

    def get(self, request, id):
        if not insturctor_test(request, id):
            return return_http_403()

        instr = Instructor.objects.get(uid=id)
        serializer = InstructorInfoSerializer(instr)
        return JsonResponse(serializer.data, safe=False)

    def post(self, request, id):
        if not insturctor_test(request, id):
            return return_http_403()

        serializer = InstructorInfoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class courseBasicInfo(View):
    """
    Supported method: `POST`, `GET`, `DELETE`

    Registered at `/course/<str:id>`.
    """

    def get(self, request, id):
        if not student_taking_course_test(request, id):
            return return_http_403()
        course = Course.objects.get(uid=id)
        serializer = CoursesSerializer(course)
        return JsonResponse(serializer.data, safe=False)

    def post(self, request, id):
        if not (student_taking_course_test(request, id)
                and instructor_giving_course_test(request, id)):
            return return_http_403()
        serializer = CoursesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        if not (student_taking_course_test(request, id)
                and instructor_giving_course_test(request, id)):
            return return_http_403()
        course = Course.objects.get(uid=id)
        if course:
            resp = JsonResponse(CoursesSerializer(course).data, safe=False)
            course.delete()
            return JsonResponse(resp, safe=False)
        return return_http_400()


class studentCourseList(View):
    """
    Supported method: `GET`

    Registered at `/student/<str:id>/course/`.

    It will return the courses in which the student with this uid enrolled in.
    """

    def get(self, request, id):
        if not student_test(request, id):
            return return_http_403()

        courses = Course.objects.filter(student__uid__contains=id)
        serializer = CoursesSerializer(courses, many=True)
        return JsonResponse(serializer.data, safe=False)


class instructorCourseList(View):
    """
    Supported method: `GET`

    Registered at `/insturctor/<str:id>/course/`.

    It will return the courses in which the student with this uid enrolled in.
    """

    def get(self, request, id):
        if not student_test(request, id):
            return return_http_403()

        courses = Course.objects.filter(instructor__uid__contains=id)
        serializer = CoursesSerializer(courses, many=True)
        return JsonResponse(serializer.data, safe=False)


class studentSubmissionList(View):
    """
    Supported method: `GET`

    Registered at
    `/student/<str:id>/course/<str:course_id>/assignment/<str:assignment_id>/history/`

    It provides student's submission history under an assignment. This API
    is accessiable by instructor.
    """

    def get(self, request, id, course_id, assignment_id):
        if not (student_test(request, id)
                and student_taking_course_test(request, course_id)) \
                or instructor_giving_course_test(request, course_id):
            return return_http_403()

        records = Record.objects.filter(
            assignment__uid__contain=assignment_id, student__uid__contain=id)
        serializer = SubmissionRecordSerializer(records, many=True)
        return JsonResponse(serializer.data, safe=False)

class studentSubmissionDetail(View):
    """
    Supported method: `GET`

    Registered at
    `/student/<str:id>/course/<str:course_id>/assignment/<str:assignment_id>/history/<str:commit_id>/`

    It provides student's submission history under an assignment. This API
    is accessiable by instructor.
    """

    def get(self, request, id, course_id, assignment_id, commit_id):
        if not (student_test(request, id)
                and student_taking_course_test(request, course_id)) \
                or instructor_giving_course_test(request, course_id):
            return return_http_403()

        records = Record.objects.get(git_commit_id=commit_id)
        if records:
            serializer = SubmissionRecordSerializer(records)
            return JsonResponse(serializer.data, safe=False)
        return return_http_404()


class courseAssignmentList(View):
    """
    Supported method: `GET`, `POST`

    Registered at `/course/<str:course_id>/assignment/`.
    """

    def get(self, request, course_id):
        if not (student_taking_course_test(request, course_id)
                and instructor_giving_course_test(request, course_id)):
            return return_http_403()

        assignments = Assignment.objects.filter(
            course__uid__contains=course_id)
        serializer = AssignmentSerializer(assignments, many=True)
        return JsonResponse(serializer.data, safe=False)

    def post(self, request, course_id):
        # when posting to this URL. we create a new assignment.
        if not instructor_giving_course_test(request, course_id):
            return return_http_403()
        # Validate input.
        request.data['state'] = 1
        # when creating a new assignment, the state is always 1 (see below for detail).
        # NOTE: Key `state` is an integer, it stores which state of the assignment
        # creating progress the assignment is in.
        #
        # |   state  | integer |
        # ----------------------
        # |  CREATED |    1    |
        # | FINISHED |    2    |
        # |   BUILT  |    3    |
        # | DISABLED |    0    |
        #
        # When the user creates a new assignment, the backend will set the key of
        # the new assignment to `CREATED` and instructs the user to finish the
        # grading script in a certain repo. When user finished, he/she would inform
        # the backend. The backend then will set it to `FINISHED` and instruct the
        # image builder to build the grading image. When building finished, the key
        # will be set to `BUILT`, the backend then will instruct the
        # gitlab-middleware to create repo for students and the scheduler will
        # start to accept submission from gitlab-middleware (the scheduler SHOULD
        # ONLY asscept submissions when state is `BUILT`).
        serializer = AssignmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # start creating new assignment.
            course = Course.objects.get(uid=course_id)
            course_name = "{}-{}{}".format(course.code.replace(" ", ""),
                                           course.year, course.semaster)
            # example course name: SI100C-2017Fall
            response = mw_connector.create_repo(user=request.user.email, course=course_name, assignment=request['name'])
            return JsonResponse(response, status=status.HTTP_201_CREATED)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class courseAssignment(View):
    """
    Supported method: `GET`, `POST`, `DELETE`

    Registered at `/course/<str:course_id>/assignment/<str:assignment_id>/`
    """

    def get(self, request, course_id, assignment_id):
        if not (student_taking_course_test(request, course_id)
                and instructor_giving_course_test(request, course_id)):
            return return_http_403()

        assignments = Assignment.objects.filter(
            course__uid__contains=course_id, uid__contains=assignment_id)
        serializer = AssignmentSerializer(assignments)
        return JsonResponse(serializer.data, safe=False)

    def post(self, request, course_id, assignment_id):
        """
        update course info, start a regrade.
        """
        if not instructor_giving_course_test(request, course_id):
            return return_http_403()

        # Validate input.
        this_assignment = Assignment.objects.filter(
            course__uid__contains=course_id, uid__contains=assignment_id)
        if this_assignment:
            if this_assignment.state == 1:
                if request.data['state'] != 1 or request.data['state'] != 2:
                    return return_http_400()
            elif request.data['state'] != this_assignment.state:
                return return_http_400()
        else:
            return return_http_400()

        serializer = AssignmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # TODO: start to build image or start a regrade.
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, course_id, assignment_id):
        if not instructor_giving_course_test(request, course_id):
            return return_http_403()

        assignment = Assignment.objects.filter(
            course__uid__contains=course_id, uid__contains=assignment_id)
        if assignment:
            assignment.delete()
            return return_http_200()
        return return_http_400()


class assignmentScoreboard(View):
    """
    This API is accessiable by instructor.

    Supported method: `GET`

    Registered at `/course/<str: course_id>/assignment/<str: assignment_id>/scores/`
    """

    def get(self, request, course_id, assignment_id):
        if not (student_taking_course_test(request, course_id) or instructor_giving_course_test(request, course_id)):
            return return_http_403()
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


class pendingAssignmentList(View):
    """
    Supported method: `GET`.

    Registered at `/course/<str:course_id>/queue`.
    """

    def get(self, request, course_id, assignment_id):
        if not (student_taking_course_test(request, course_id) or instructor_giving_course_test(request, course_id)):
            return return_http_403()
        this_course = Course.objects.get(uid=course_id)
        course_name = this_course.name
        this_assignment = Assignment.objects.get(uid=assignment_id)
        assignment_name = this_assignment.name
        course_assignment_url = mw_connector.get_gitlab_student_repo(
            '', course_name, assignment_name)
        all_pending_assignment = pendingAssignment.objects.filter(
            upstream__startswith=course_assignment_url)
        serializer = pendingAssignmentSerializer(
            all_pending_assignment, many=True)
        return JsonResponse(serializer.data, safe=False)


class courseInstructorList(View):
    """
    Supported method: `GET`, `POST`

    Registered at `/course/<str:course_id>/instructor/`
    """

    def get(self, request, course_id):
        if not (student_taking_course_test(request, course_id) or instructor_giving_course_test(request, course_id)):
            return return_http_403()
        all_instr = Course.objects.get(uid=course_id).instructor.all()
        serializer = InstructorBasicInfoSerializer(all_instr, many=True)
        return JsonResponse(serializer.data, safe=False)

    def post(self, request, course_id):
        if not instructor_giving_course_test(request, course_id):
            return return_http_403()
        instr = Instructor.objects.get(uid=request.data['uid'])
        course = Course.objects.get(uid=course_id)
        if instr and course:
            course.instructor.add(instr)
            return JsonResponse(InstructorBasicInfoSerializer(instr).data, safe=False)
        return return_http_400()


class courseInstructorsBasicInfo(View):
    """
    Supported method: `GET`, `DELETE`

    Registered at `/course/<str:course_id>/instructor/<str:instr_id>/`
    """

    def get(self, request, course_id, instr_id):
        if not (student_taking_course_test(request, course_id) or instructor_giving_course_test(request, course_id)):
            return return_http_403()
        course = Course.objects.get(uid=course_id)
        if not course:
            return return_http_404()
        instr = course.instructor.get(uid=instr_id)
        if instr:
            serializer = InstructorBasicInfoSerializer(instr, many=False)
            return JsonResponse(serializer.data, safe=False)
        return return_http_404()

    def delete(self, request, course_id, instr_id):
        if not instructor_giving_course_test(request, course_id):
            return return_http_403()
        this_course = Course.objects.get(uid=course_id)
        if instr_id != this_course.creator:
            this_instr = Instructor.objects.get(uid=instr_id)
            if this_instr:
                this_course.instructor.remove(this_instr)
                return JsonResponse(InstructorBasicInfoSerializer(this_instr).data, safe=False)
            return return_http_404()
        else:
            return return_http_403()
        return return_http_400()


class courseStudentList(View):
    """
    Supported method: `POST`, `GET`

    Registered at `/course/<str:id>/students/`.
    """

    def get(self, request, id):
        course = Course.objects.get(uid=id)
        if not course:
            return return_http_404()
        student_list = course.student.all()
        serializer = StudentBasicInfoSerializer(student_list, many=False)
        return JsonResponse(serializer.data, safe=False)

    def post(self, request, id):
        course = Course.objects.get(uid=id)
        if not course:
            return return_http_404()
        student = Student.objects.get(email=request.data['email'])
        if student:
            course.student.add(student)
            return JsonResponse(StudentBasicInfoSerializer(student).data)
        return return_http_400()


class courseStudentInfo(View):
    """
    Supported method: `POST`, `GET`, `DELETE`

    Registered at `/course/<str:id>/students/<id:uid>`.
    """

    def get(self, request, id, uid):
        if not (student_taking_course_test(request, id) or instructor_giving_course_test(request, id)):
            return return_http_403()
        course = Course.objects.get(uid=id)
        if not course:
            return return_http_404()
        student = course.student.get(uid=uid)
        if student:
            serializer = StudentBasicInfoSerializer(student)
            return JsonResponse(serializer.data, safe=False)
        return return_http_400()

    def delete(self, request, id, uid):
        if not instructor_giving_course_test(request, id):
            return return_http_403()
        this_course = Course.objects.get(uid=id)
        this_student = Student.objects.get(uid=uid)
        if this_course and this_course.student.get(uid=uid):
            this_course.student.remove(this_student)
            return JsonResponse(StudentBasicInfoSerializer(this_student).data, safe=False)
        return return_http_404()


class courseJudgerList(View):
    """
    Supported method: `GET`, `POST`

    Registered at `/course/<str:id>/judger/`
    """

    def get(self, request, id):
        if not instructor_giving_course_test(request, id):
            return return_http_403()
        this_course = Course.objects.get(uid=id)
        if this_course:
            judger_list = this_course.juder.all()
            serializer = JudgerSerializer(judger_list, many=True)
            return JsonResponse(serializer.data, safe=False)
        return return_http_404()

    def post(self, request, id):
        if not instructor_giving_course_test(request, id):
            return return_http_403()
        this_course = Course.objects.get(uid=id)
        if this_course:
            judger = Judger.objects.get(uid=request.data['uid'])
            if judger:
                this_course.judger.add(judger)
                serializer = JudgerSerializer(judger, many=True)
                return JsonResponse(serializer.data, safe=False)
            return return_http_404()


class courseJudger(View):
    """
    Supported method: `GET`, `DELETE`

    Registered at `/course/<str:id>/judger/<str:uid>`
    """

    def get(self, request, id, uid):
        if not instructor_giving_course_test(request, id):
            return return_http_403()
        this_course = Course.objects.get(uid=id)
        if this_course:
            judger = this_course.juder.get(uid=id)
            serializer = JudgerSerializer(judger)
            return JsonResponse(serializer.data, safe=False)
        return return_http_404()

    def delete(self, request, id, uid):
        if not instructor_giving_course_test(request, id):
            return return_http_403()
        this_course = Course.objects.get(uid=id)
        if this_course:
            judger = this_course.juder.get(uid=uid)
            if judger:
                this_course.judeger.remove(judger)
                serializer = JudgerSerializer(judger)
                return JsonResponse(serializer.data, safe=False)
            return return_http_404()
        else:
            return return_http_404()


class judgerList(View):
    """
    Suppoerted method: `GET`, `POST`

    Registered at `/judger/`
    """

    def get(self, request):
        pass

    def post(self, request):
        pass

    def delete(self, request):
        pass
