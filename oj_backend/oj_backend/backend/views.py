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

from django.views import View
from django.core.exceptions import ValidationError
from django.core.validators import validate_email, validate_ipv46_address
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed, Http404, HttpResponse, HttpResponseForbidden
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.urls import path, include, reverse
from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework import status, generics, mixins
from rest_framework.parsers import JSONParser
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
try:
    from django.utils import simplejson
except:
    import simplejson

import redis
import time
import logging
from uuid import uuid1, UUID

import oj_backend.backend.middleware_connector as mw_connector
from oj_backend.backend.utils import student_active_test, student_test, insturctor_test, student_taking_course_test, student_submit_assignment_test, instructor_giving_course_test, regrade_assignment
from oj_backend.backend.models import *
from oj_backend.backend.serializers import *
from oj_backend.backend.permissions import *
from oj_backend.settings import redisConnectionPool, OJ_SUBMISSION_TOKEN, OJ_ENFORCE_HTTPS
from oj_backend.backend.middleware_connector import *

backend_logger = logging.getLogger('backend.main')


class studentInformation(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    '''
    `/student/<str:uid>`
    '''
    queryset = Student.objects.all()
    serializer_class = StudentInfoSerializer
    permission_classes = (userInfoReadWritePermission, IsAuthenticated)
    lookup_field = 'uid'

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, user__uid=self.kwargs['uid'])
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = self.update(request, *args, **kwargs)
        email = self.get_object().user.email
        user_key = self.get_object().user.rsa_pub_key
        try:
            MWUpdateUserKey(email, user_key)
        except (MWUpdateError, MiddlewareError):
            return JsonResponse({"cause": "server error"}, status=500)
        return response


class insturctorInformation(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin):
    '''
    `/instructor/<str:uid>/`
    '''
    queryset = Instructor.objects.all()
    serializer_class = InstructorInfoSerializer
    permission_classes = (userInfoReadWritePermission, IsAuthenticated)
    lookup_field = 'uid'

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, user__uid=self.kwargs['uid'])
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = self.update(request, *args, **kwargs)
        email = self.get_object().user.email
        user_key = self.get_object().user.rsa_pub_key
        try:
            MWUpdateUserKey(email, user_key)
        except (MWUpdateError, MiddlewareError):
            return JsonResponse({"cause": "server error"}, status=500)
        return response


class userRole(generics.GenericAPIView):
    '''
    `/user/role`

    And

    `/user/`
    '''

    def get(self, request):
        if not request.user.is_authenticated:
            return Response(status=401)
        data = {
            'uid': request.user.uid,
            'is_student': Student.objects.filter(user__uid=request.user.uid).exists(),
            'is_instructor': Instructor.objects.filter(user__uid=request.user.uid).exists()
        }
        return JsonResponse(data=data, status=200)


class userInstr(generics.GenericAPIView, mixins.RetrieveModelMixin):
    '''
    `/user/<str:uid>/instructor`
    '''
    serializer_class = InstructorBasicInfoSerializer
    permission_classes = (
        IsAuthenticated, studentinstrUserInfoReadWritePermission)

    def get_queryset(self):
        return Instructor.objects.filter(user__uid=self.kwargs['uid'])

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, user=self.request.user)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(data={'cuase': 'Unauthorized'}, status=401)
        try:
            uid = UUID(self.kwargs['uid'])
        except:
            return JsonResponse(data={'cuase': 'Bad request'}, status=400)
        if request.user.uid != uid:
            return JsonResponse(data={'cause': 'Forbidden'}, status=403)
        if Instructor.objects.filter(enroll_email=request.user.email, user=request.user).exists():
            return JsonResponse(data={'cause': 'Already exists.'}, status=409)
        this_instr = Instructor(
            enroll_email=request.user.email, user=request.user)
        this_instr.save()
        serializer = self.serializer_class(this_instr)
        return JsonResponse(serializer.data, status=201)


class userStudent(generics.GenericAPIView, mixins.RetrieveModelMixin):
    '''
    `/user/<str:uid>/student`
    '''
    serializer_class = StudentBasicInfoSerializer
    permission_classes = (
        IsAuthenticated, studentinstrUserInfoReadWritePermission)

    def get_queryset(self):
        return Student.objects.filter(user__uid=self.kwargs['uid'])

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(queryset, user=self.request.user)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse(data={'cuase': 'Unauthorized'}, status=401)
        try:
            uid = UUID(self.kwargs['uid'])
        except:
            return JsonResponse(data={'cuase': 'Bad request'}, status=400)
        if request.user.uid != uid:
            return JsonResponse(data={'cause': 'Forbidden'}, status=403)
        try:
            nickname = self.request.data['nickname']
            student_id = self.request.data['student_id']
        except KeyError:
            return JsonResponse(data={'cause': 'Invalid request'}, status=400)
        if Student.objects.filter(enroll_email=request.user.email, user=request.user).exists():
            return JsonResponse(data={'cause': 'Already exists.'}, status=409)
        this_student = Student(enroll_email=request.user.email,
                               user=request.user, nickname=nickname, student_id=student_id)
        this_student.save()
        serializer = self.serializer_class(this_student)
        return JsonResponse(serializer.data, status=201)


class courseList4Students(generics.GenericAPIView, mixins.ListModelMixin):
    '''
    `/student/<str:uid>/course/`
    '''
    serializer_class = CoursesViewSerializer
    permission_classes = (courseReadWritePermission, IsAuthenticated)

    def get_queryset(self):
        this_student = get_object_or_404(Student.objects.filter(
            user=self.request.user), user__uid=self.kwargs['uid'])
        return this_student.course_set.all()

    def get_object(self):
        student_uid = self.request.user.uid
        queryset = self.get_queryset()
        obj = queryset.filter(student__user__uid=student_uid)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        try:
            uid = UUID(self.kwargs['uid'])
        except:
            return JsonResponse(data={'cuase': 'Bad request'}, status=400)
        if request.user.uid != uid:
            return JsonResponse(data={'cause': 'Forbidden'}, status=403)
        return self.list(request, *args, **kwargs)


class courseList4Instr(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    '''
    `/insturctor/<str:uid>/course/`
    '''
    serializer_class = CoursesCreateSerializer
    permission_classes = (courseReadWritePermission, IsAuthenticated)

    def get_queryset(self):
        this_instr = get_object_or_404(Instructor.objects.filter(
            user=self.request.user), user__uid=self.kwargs['uid'])
        return this_instr.course_set.all()

    def get_object(self):
        instr_uid = self.request.user.uid
        queryset = self.get_queryset()
        obj = queryset.filter(instructor__user__uid=instr_uid)
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user.uid, uid=uuid1())

    def get(self, request, *args, **kwargs):
        try:
            uid = UUID(self.kwargs['uid'])
        except:
            return JsonResponse(data={'cuase': 'Bad request'}, status=400)
        if request.user.uid != uid:
            return JsonResponse(data={'cause': 'Forbidden'}, status=403)
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = self.create(request, *args, **kwargs)
        this_course = Course.objects.get(uid=response.data['uid'])
        this_course.instructor.add(request.user.instructor)
        try:
            course_name = get_course_project_name(
                this_course.code, this_course.year, this_course.semester)
            MWUpdateCourse(course_name, str(this_course.uid))
        except (MiddlewareError, MWUpdateError):
            # rollback.
            this_course.delete()
            return JsonResponse(status=500, data={"cuase": "Git server error."})
        for instr in this_course.instructor.all():
            try:
                MWCourseAddInstr(this_course.uid, instr.enroll_email)
            except (MiddlewareError, MWUpdateError):
                MWUpdateUser(instr.enroll_email)
                MWCourseAddInstr(this_course.uid, instr.enroll_email)
        return response


class assignmentList4Student(generics.GenericAPIView, mixins.ListModelMixin):
    '''
    `/student/<str:student_id>/course/<str:course_id>/assignment/`
    '''
    serializer_class = AssignmentViewSerializer
    permission_classes = (assignmentInfoReadWritePermisson, IsAuthenticated)

    def get_queryset(self):
        this_student = get_object_or_404(
            Student, user__uid=self.kwargs['student_id'])
        this_course = get_object_or_404(
            this_student.course_set.all(), uid=self.kwargs['course_id'])
        return this_course.assignment_set.all()

    def get_object(self):
        this_student = self.kwargs['student_id']
        this_course = self.kwargs['course_id']
        queryset = self.get_queryset()
        obj = queryset.filter(course__uid=this_course,
                              course__student__user__uid=this_student)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class courseInformation(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    '''
    `/course/<str:uid>`
    '''
    serializer_class = CoursesViewSerializer
    permission_classes = (courseReadWritePermission, IsAuthenticated)
    queryset = Course.objects.all()

    def get_object(self):
        course_uid = self.kwargs['uid']
        queryset = self.get_queryset()
        obj = get_object_or_404(
            queryset, uid=course_uid)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class assignmentList4Instr(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    '''
    `/course/<str:uid>/assignment/`
    '''
    serializer_class = AssignmentCreateSerializer
    permission_classes = (assignmentInfoReadWritePermisson, IsAuthenticated)

    def get_queryset(self):
        this_course = get_object_or_404(Course, uid=self.kwargs['uid'])
        return this_course.assignment_set.all()

    def get_object(self):
        this_course = self.kwargs['uid']
        this_instr = self.request.user.uid
        queryset = self.get_queryset()
        obj = queryset.filter(course__uid=this_course, course__instructor__user__uid=this_instr)
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_create(self, serializer):
        this_course = get_object_or_404(Course, uid=self.kwargs['uid'])
        serializer.save(course=this_course)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        this_course = get_object_or_404(Course, uid=self.kwargs['uid'])
        if not this_course.instructor.filter(user=request.user):
            return JsonResponse(data={'cause': 'Forbidden'}, status=403)
        response = self.create(request, *args, **kwargs)
        this_assignment = Assignment.objects.get(uid=response.data['uid'])
        deadline = this_assignment.deadline
        try:
            MWCourseAddAssignment(
                self.kwargs['uid'], this_assignment.short_name, str(this_assignment.uid))
            repo = MWCourseAddRepo(self.kwargs['uid'], str(this_assignment.uid), [
            ], deadline, repo_name='_grading_script', owner_uid=None)
            git_repo = repo.response.json().get('ssh_url_to_repo')
            this_assignment.git_org_addr = git_repo[0:-len('_grading_script')]
            this_assignment.save()
        except (MiddlewareError, MWUpdateError):
            this_assignment.delete()
            return JsonResponse(data={"cuase": "Git server error."}, status=500)
        if isinstance(response, Response):
            response.data['ssh_url_to_repo'] = git_repo
            response.content = simplejson.dumps(response.data)
        try:
            for student in this_course.students.all():
                if student.user:
                    MWCourseAddRepo(this_course.uid, this_assignment.uid,
                                    student.enroll_email, deadline, owner_uid=student.user.uid)
        except:
            return JsonResponse(status=500, data={})
        return response


class assignmentDetail(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    '''
    `/course/<str:course_id>/assignment/<str:assignment_id>`
    '''
    serializer_class = AssignmentViewSerializer
    permission_classes = (assignmentInfoReadWritePermisson, IsAuthenticated)

    def get_queryset(self):
        this_course = get_object_or_404(Course, uid=self.kwargs['course_id'])
        return this_course.assignment_set.all()

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(
            queryset, uid=self.kwargs['assignment_id'], course__uid=self.kwargs['course_id'])
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        response = self.delete(request, *args, **kwargs)
        this_course = Course.objects.get(uid=self.kwargs['course_id'])
        this_assignment = Assignment.objects.get(uid=self.kwargs['assignment_id'])
        for student in this_course.students.all():
            MWCourseDelRepo(this_course.uid, this_assignment.uid, student.enroll_email)
        return response


class courseInstrList(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    '''
     `/course/<str:uid>/instructor/`
    '''
    serializer_class = InstructorBasicInfoSerializer
    permission_classes = (courseInstrInfoReadWritePermission, IsAuthenticated)

    def get_queryset(self):
        this_course = get_object_or_404(Course, uid=self.kwargs['uid'])
        return this_course.instructor.all()

    def get_object(self):
        obj = self.get_queryset()
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        this_course = Course.objects.get(uid=self.kwargs['uid'])
        if not request.user.is_authenticated:
            return JsonResponse(data={'cause': 'Unauthorized'}, status=401)
        if not this_course.instructor.filter(user__uid=request.user.uid).exists():
            return JsonResponse(data={'cause': 'Forbidden'}, status=403)
        try:
            validate_email(request.data['enroll_email'])
        except ValidationError:
            return JsonResponse(status=400, data={'cause': 'Bad request'})
        try:
            this_instr = Instructor.objects.get(
                enroll_email=request.data['enroll_email'])
        except:
            this_instr = Instructor(
                enroll_email=request.data['enroll_email'], user=None)
            try:
                this_user = User.objects.get(
                    email=request.data['enroll_email'])
                this_instr.user = this_user
            except:
                pass
        this_instr.save()
        this_course.instructor.add(this_instr)
        try:
            MWCourseAddInstr(
                course_uid=self.kwargs['uid'], instr_email=request.data['enroll_email'])
        except:
            MWUpdateUser(request.data['enroll_email'])
            MWCourseAddInstr(
                course_uid=self.kwargs['uid'], instr_email=request.data['enroll_email'])
        return JsonResponse(data={}, status=201)


class courseInstrDetail(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.DestroyModelMixin):
    '''
    `/course/<str:course_id>/instructor/<str:instr_email>`
    '''
    serializer_class = InstructorBasicInfoSerializer
    permission_classes = (courseInstrInfoReadWritePermission, IsAuthenticated)

    def get_queryset(self):
        this_course = get_object_or_404(Course, uid=self.kwargs['course_id'])
        return this_course.instructor.all()

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(),
                                enroll_email=self.kwargs['instr_email'])
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        this_course = Course.objects.get(uid=self.kwargs['course_id'])
        if not this_course.instructor.filter(user__uid=request.user.uid).exists():
            return JsonResponse(data={'cause': 'Forbidden'}, status=403)
        try:
            this_instr = this_course.instructor.get(
                enroll_email=self.kwargs['instr_email'])
        except:
            return JsonResponse(data={'cause': 'Not found'}, status=404)
        if this_instr.user:
            if this_instr.user.uid == UUID(this_course.creator):
                return JsonResponse(data={'cause': "You could not delete creator from a course's instructor list."}, status=400)
        this_course.instructor.remove(this_instr)
        return HttpResponse(content='', status=204)


class courseStudentList(generics.GenericAPIView, mixins.ListModelMixin):
    '''
    `/course/<str:course_id>/student/`
    '''
    serializer_class = StudentBasicInfoSerializer
    permission_classes = (
        courseStudentInfoReadWritePermission, IsAuthenticated)

    def get_queryset(self):
        return get_object_or_404(Course, uid=self.kwargs['course_id']).students.all()

    def get_object(self):
        obj = self.get_queryset()
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        this_course = Course.objects.get(uid=self.kwargs['course_id'])
        if not this_course.instructor.filter(user__uid=request.user.uid).exists():
            return JsonResponse(data={'cause': 'Forbidden'}, status=403)
        try:
            validate_email(request.data['enroll_email'])
        except ValidationError:
            return JsonResponse(status=400, data={'cause': 'invalid email'})
        try:
            this_student = Student.objects.get(
                enroll_email=request.data['enroll_email'])
        except:
            this_student = Student(
                enroll_email=request.data['enroll_email'], user=None, student_id=request.data['student_id'])
            try:
                this_user = User.objects.get(
                    email=request.data['enroll_email'])
                this_student.user = this_user
            except:
                pass
            this_student.save()
            MWUpdateUser(request.data['enroll_email'])
        this_course.students.add(this_student)
        for assignment in this_course.assignment_set.all():
            if this_student.user:
                MWCourseAddRepo(
                    self.kwargs['course_id'], assignment.uid, request.data['enroll_email'], assignment.deadline, owner_uid=this_student.user.uid)
        return JsonResponse(data=StudentBasicInfoSerializer(this_student).data, status=201, safe=False)


class courseStudentDetail(generics.GenericAPIView, mixins.RetrieveModelMixin):
    '''
    `/course/<str:course_id>/student/<str:student_email>`
    '''

    serializer_class = StudentBasicInfoSerializer
    permission_classes = (
        courseStudentInfoReadWritePermission, IsAuthenticated)

    def get_queryset(self):
        return get_object_or_404(Course, uid=self.kwargs['course_id']).students.all()

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(
            queryset, enroll_email=self.kwargs['student_email'])
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        this_course = Course.objects.get(uid=self.kwargs['course_id'])
        if not this_course.instructor.filter(user__uid=request.user.uid).exists():
            return JsonResponse(data={'cause': 'Forbidden'}, status=403)
        try:
            this_student = this_course.students.get(
                enroll_email=self.kwargs['student_email'])
        except:
            return JsonResponse(data={'cause': 'Not found'}, status=404)
        this_course.students.remove(this_student)
        if this_student.user:
            for assignment in this_course.assignment_set.all():
                MWCourseDelRepo(this_course.uid, assignment.uid, this_student.enroll_email)
        return HttpResponse(content='', status=204)


class courseJudgeList(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    '''
    `/course/<str:course_id>/judge/`
    '''
    serializer_class = courseJudgeSerializer
    permission_classes = (courseJudgeReadWritePermisson, IsAuthenticated)

    def get_queryset(self):
        return get_object_or_404(Course, uid=self.kwargs['course_id']).default_judge.all()

    def get_object(self):
        obj = self.get_queryset()
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            this_judge = Judge.objects.get(uid=request.data['uid'])
        except:
            return JsonResponse(data={'cause': 'Not Found'}, status=404)
        maintiainer = this_judge.maintainer.user
        if not maintiainer == request.user:
            return JsonResponse(data={'cause': 'Forbidden'}, status=403)
        try:
            this_course = Course.objects.get(uid=self.kwargs['course_id'])
        except:
            return JsonResponse(data={'cause': 'Not Found'}, status=404)
        try:
            this_course.instructor.get(user__uid=request.user.uid)
        except:
            return JsonResponse(data={'cause': 'Forbidden'}, status=403)
        this_course.default_judge.add(this_judge)
        return JsonResponse(JudgeSerializer(this_judge).data, safe=False, status=201)


class courseJudgeDetail(generics.GenericAPIView, mixins.RetrieveModelMixin):
    '''
    `/course/<str:course_id>/judge/<str:judge_id>`
    '''
    serializer_class = courseJudgeSerializer
    permission_classes = (courseJudgeReadWritePermisson, IsAuthenticated)

    def get_queryset(self):
        return get_object_or_404(Course, uid=self.kwargs['course_id']).default_judge.all()

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(),
                                uid=self.kwargs['judge_id'])
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        try:
            this_course = Course.objects.get(uid=self.kwargs['course_id'])
        except:
            return JsonResponse(data={'cause': 'Not Found'}, status=404)
        try:
            this_course.instructor.get(user__uid=request.user.uid)
        except:
            return JsonResponse(data={'cause': 'Forbidden'}, status=403)
        this_course.default_judge.remove(this_judge)
        return HttpResponse(content='', status=204)


class assignmentJudgeList(generics.GenericAPIView, mixins.ListModelMixin):
    '''
    `/course/<str:course_id>/assignment/<str:assignment_id>/judge/`
    '''
    serializer_class = courseJudgeSerializer
    permission_classes = (courseJudgeReadWritePermisson, IsAuthenticated)

    def get_queryset(self):
        return get_object_or_404(
            Assignment, uid=self.kwargs['assignment_id'], course__uid=self.kwargs['course_id']).judge.all()

    def get_object(self):
        obj = self.get_queryset()
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            uid = request.data['uid']
        except:
            return JsonResponse(data={'cause': 'missing parameter'}, status=400)
        try:
            this_judge = Judge.objects.get(uid=request.data['uid'])
        except:
            return JsonResponse(data={'cause': 'Not Found'}, status=404)
        maintainer = this_judge.maintainer.user
        if not maintainer == request.user:
            return JsonResponse(data={'cause': 'Forbidden'}, status=403)
        try:
            this_assignment = Assignment.objects.get(
                uid=self.kwargs['assignment_id'])
        except:
            return JsonResponse(data={''}, status=404)
        try:
            this_assignment.course.instructor.get(user__uid=request.user.uid)
        except:
            return JsonResponse(data={'cause': 'Forbidden'}, status=403)
        this_assignment.judge.add(this_judge)
        this_redis = redis.Redis(connection_pool=redisConnectionPool)
        backend_logger.info(
            'Published redis data to assignment_judge: {}'.format(request.data['uid']))
        this_redis.publish('assignment_judge', request.data['uid'])
        return JsonResponse(JudgeSerializer(this_judge).data, safe=False, status=201)


class assignmentJudgeDetail(generics.GenericAPIView, mixins.RetrieveModelMixin):
    '''
    `/course/<str:course_id>/assignment/<str:assignment_id>/judge/<str:judge_id>`
    '''
    serializer_class = courseJudgeSerializer
    permission_classes = (courseJudgeReadWritePermisson, IsAuthenticated)

    def get_queryset(self):
        return get_object_or_404(
            Assignment, uid=self.kwargs['assignment_id'], course__uid=self.kwargs['course_id']).judge.all()

    def get_object(self):
        obj = get_object_or_404(self.get_queryset(),
                                uid=self.kwargs['judge_id'])
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        try:
            this_assignment = Assignment.objects.get(
                uid=self.kwargs['assignment_id'], course__uid=self.kwargs['course_id'])
        except:
            return JsonResponse(data={'cause': 'Not found'}, status=404)
        try:
            this_assignment.course.instructor.get(user__uid=request.user.uid)
        except:
            return JsonResponse(data={'cause': 'Forbidden'}, status=403)
        this_judge = Judge.objects.get(uid=self.kwargs['judge_id'])
        this_assignment.judge.reomve(this_judge)
        backend_logger.info(
            'Published redis data to assignment_judge: {}'.format(request.data['uid']))
        this_redis = redis.Redis(connection_pool=redisConnectionPool)
        this_redis.publish('assignment_judge', request.data['uid'])
        return HttpResponse(content='', status=204)


class submissionHistoryList(generics.GenericAPIView, mixins.ListModelMixin):
    '''
    `/student/<str:student_id>/course/<str:course_id>/assignment/<str:assignment_id>/history/`
    '''
    serializer_class = SubmissionRecordSerializer
    permission_classes = (submissionRecordReadPermission, IsAuthenticated)

    def get_queryset(self):
        this_student = get_object_or_404(
            Student, user__uid=self.kwargs['student_id'])
        this_assignment = get_object_or_404(
            Assignment, uid=self.kwargs['assignment_id'], course__uid=self.kwargs['course_id'])
        return this_student.record_set.filter(assignment=this_assignment)

    def get_object(self):
        this_student = self.kwargs['student_id']
        this_assignment = self.kwargs['assignment_id']
        queryset = self.get_queryset()
        obj = queryset.filter(student__user__uid=this_student, assignment__uid=this_assignment)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class submissionHistoryDetail(generics.GenericAPIView, mixins.RetrieveModelMixin):
    '''
    `/student/<str:student_id>/course/<str:course_id>/assignment/<str:assignment_id>/history/<str:git_commit_id>`
    '''
    serializer_class = SubmissionRecordSerializer
    permission_classes = (submissionRecordReadPermission, IsAuthenticated)

    def get_queryset(self):
        this_student = get_object_or_404(
            Student, uid=self.kwargs['student_id'])
        this_assignment = get_object_or_404(
            Assignment, uid=self.kwargs['assignment_id'], course__uid=self.kwargs['course_id'])
        return this_student.record_set.filter(assignment=this_assignment)

    def get_object(self):
        this_student = self.kwargs['student_id']
        this_assignment = self.kwargs['assignment_id']
        this_record = self.kwargs['git_commit_id']
        queryset = self.get_queryset()
        obj = queryset.get(student__user__uid=this_student, assignment__uid=this_assignment, git_commit_id=this_record)
        self.check_object_permissions(obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class instrJudgeList(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    '''
    `/judge/`
    '''
    serializer_class = JudgeSerializer
    permission_classes = (judgeReadWritePermission, IsAuthenticated)

    def get_queryset(self):
        this_instr = self.request.user.instructor
        if not this_instr:
            raise PermissionDenied
        return this_instr.judge_set.all()

    def get_object(self):
        obj = self.get_queryset().filter(maintainer=self.request.user.instructor)
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_create(self, serializer):
        serializer.save(maintainer=self.request.user.instructor)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class instrJudgeDetail(generics.GenericAPIView, mixins.UpdateModelMixin, mixins.DestroyModelMixin, mixins.RetrieveModelMixin):
    '''
    `/judge/<str:uid>`
    '''
    serializer_class = JudgeSerializer
    permission_classes = (judgeReadWritePermission, IsAuthenticated)

    def get_queryset(self):
        this_instr = self.request.user.instructor
        if not this_instr:
            raise PermissionDenied
        return this_instr.judge_set.all()

    def get_object(self):
        this_user = self.request.user
        obj = get_object_or_404(self.get_queryset(),
                                maintainer=this_user.instructor, uid=self.kwargs['uid'])
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class assignmentScoreboardDetail(generics.GenericAPIView, mixins.ListModelMixin):
    '''
    `/course/<str:course_id>/assignment/<str:assignment_id>/scores/`
    '''
    serializer_class = ScoreBoardSerializer
    permission_classes = (recordReadOnly, IsAuthenticated)

    def get_queryset(self):
        this_course = self.kwargs['course_id']
        this_assignment = self.kwargs['assignment_id']
        this_course_student_list = Course.objects.get(
            uid=this_course).students.all()
        query_set = None
        for this_student in this_course_student_list:
            this_student_record = Record.objects.filter(
                student=this_student, assignment__uid=this_assignment).order_by('-submission_time')[0]
            if query_set:
                query_set = query_set | this_student_record
            else:
                query_set = this_student_record
        return query_set

    def get_object(self):
        obj = self.get_queryset()
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class pendingAssignment(generics.GenericAPIView, mixins.ListModelMixin):
    '''
    `/course/<str:course_id>/assignment/<str:assignment_id>/queue/`
    '''

    def get(self, request, course_id, assignment_id):
        if not request.user.is_authenticated:
            return Response(data={}, status=401)
        this_course = get_object_or_404(Course, uid=course_id)
        if not (this_course.instructor.filter(user__uid=request.user.uid).exists() or this_course.students.filter(user__uid=request.user.uid).exists()):
            return Response(data={}, status=403)
        redis_server = redis.Redis(
            connection_pool=redisConnectionPool)
        all_pending = redis_server.zrange(assignment_id, 0, -1)
        pending_list = []
        for submission in all_pending:
            submission = simplejson.loads(submission)
            display_submission = {}
            display_submission['submission_time'] = submission['receive_time']
            display_submission['submitter'] = ', '.join(Student.objects.get(
                user__uid=submitter).nickname for submitter in submission['owner_uids'])
            pending_list.append(display_submission)
        return JsonResponse(pending_list, status=200, safe=False)


class internalSubmissionInterface(generics.GenericAPIView):
    '''
    `/internal/subbmission/`
    '''

    def post(self, request, *args, **kwargs):
        auth_token = request.META.get("HTTP_AUTHORIZATION", None)
        if auth_token != OJ_SUBMISSION_TOKEN:
            remote = request.META.get(
                'HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', None))
            backend_logger.error('Submission interface recieved an unauthorized submission. Token: {}; From {}; Payload: {}'.format(
                auth_token, remote, request.data))
            return JsonResponse(status=401, data={'cause': 'Invalid token.'})
        this_submission = simplejson.dumps(request.data)
        this_redis = redis.Redis(connection_pool=redisConnectionPool)
        now = int(time.time())
        try:
            upstream = request.data['upstream']
            owner_uids = simplejson.loads(
                request.data['additional_data'])
            assignment_uid = request.data["assignment_uid"]
        except KeyError:
            return JsonResponse(data={'cause': 'Missing parameter in request'}, status=400)
        payload = {'upstream': upstream,
                   "owner_uids": owner_uids, 'receive_time': now}
        payload = simplejson.dumps(payload)
        backend_logger.info('Submission relied. Payload: {}; Channel: {}; Weight: {}'.format(
            payload, assignment_uid, now))
        this_redis.zadd(assignment_uid, {payload: now})
        return Response(data=simplejson.loads(this_submission), status=201)


class OIDCLoginParam(generics.GenericAPIView):
    '''
    `/user/login/oauth/param`

    AND

    `/user/auth/openid/param`
    '''

    def get(self, request, *args, **kwargs):
        host = request.META.get('HTTP_HOST')
        scheme = "https://" if request.is_secure() else "http://"
        return JsonResponse(status=200, data={'login_url': scheme+host+reverse('oidc_auth_request'), 'logout_url': scheme+host+reverse('oidc_end_session')})
