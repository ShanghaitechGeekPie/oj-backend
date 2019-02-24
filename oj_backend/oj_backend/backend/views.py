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
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed, Http404, HttpResponse
from django.contrib.auth.models import AnonymousUser
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
from uuid import uuid1

import oj_backend.backend.middleware_connector as mw_connector
from oj_backend.backend.utils import student_active_test, student_test, insturctor_test, student_taking_course_test, student_submit_assignment_test, instructor_giving_course_test, regrade_assignment
from oj_backend.backend.models import *
from oj_backend.backend.serializers import *
from oj_backend.backend.permissions import *
from oj_backend.settings import redisConnectionPool, OIDC_OP_AUTHORIZATION_ENDPOINT, OJ_SUBMISSION_TOKEN, OJ_ENFORCE_HTTPS
from oj_backend.backend.middleware_connector import *


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
            MWUpdateUser(email)
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
            MWUpdateUser(email)
            MWUpdateUserKey(email, user_key)
        except (MWUpdateError, MiddlewareError):
            return JsonResponse({"cause": "server error"}, status=500)
        return response


class userRole(generics.GenericAPIView):
    '''
    `/user/role`
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


class courseList4Students(generics.GenericAPIView, mixins.ListModelMixin):
    '''
    `/student/<str:uid>/course/`
    '''
    serializer_class = CoursesSerializer
    permission_classes = (courseReadWritePermission, IsAuthenticated)
    queryset = Course.objects.all()

    def get_object(self):
        student_uid = self.request.user.uid
        queryset = self.get_queryset()
        obj = get_list_or_404(queryset, student__user__uid=student_uid)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class courseList4Instr(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    '''
    `/insturctor/<str:uid>/course/`
    '''
    serializer_class = CoursesSerializer
    permission_classes = (courseReadWritePermission, IsAuthenticated)
    queryset = Course.objects.all()

    def get_object(self):
        instr_uid = self.request.user.uid
        queryset = self.get_queryset()
        obj = get_list_or_404(queryset, instructor__user__uid=instr_uid)
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user.uid, uid=uuid1())

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = self.create(request, *args, **kwargs)
        this_course = Course.objects.get(uid=response.data['uid'])
        this_course.instructor.add(request.user.instructor)
        try:
            MWUpdateCourse(this_course.name, str(this_course.uid))
        except (MiddlewareError, MWUpdateError):
            # rollback.
            this_course.delete()
            return JsonResponse(status=500, data={})
        return response


class assignmentList4Student(generics.GenericAPIView, mixins.ListModelMixin):
    '''
    `/student/<str:student_id>/course/<str:course_id>/assignment/`
    '''
    serializer_class = AssignmentSerializer
    permission_classes = (assignmentInfoReadWritePermisson, IsAuthenticated)
    queryset = Assignment.objects.all()

    def get_object(self):
        this_student = self.kwargs['student_id']
        this_course = self.kwargs['course_id']
        queryset = self.get_queryset()
        obj = get_list_or_404(
            queryset, course__uid=this_course, student__user__uid=this_student)
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class courseInformation(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    '''
    `/course/<str:course_id>`
    '''
    serializer_class = CoursesSerializer
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
        response = self.update(request, *args, **kwargs)
        this_course = self.get_object()
        try:
            MWUpdateCourse(this_course.name, str(this_course.uid))
        except (MiddlewareError, MWUpdateError):
            return JsonResponse(status=500, data={})
        return response

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class assignmentList4Instr(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    '''
    `/course/<str:uid>/assignment/`
    '''
    serializer_class = AssignmentSerializer
    permission_classes = (assignmentInfoReadWritePermisson, IsAuthenticated)
    queryset = Assignment.objects.all()

    def get_object(self):
        this_course = self.kwargs['uid']
        this_instr = self.request.user.uid
        queryset = self.get_queryset()
        obj = get_list_or_404(
            queryset, course__uid=this_course, course__instructor__user__uid=this_instr)
        self.check_object_permissions(self.request, obj)
        return obj

    def perform_create(self, serializer):
        this_course = get_object_or_404(Course, uid=self.kwargs['uid'])
        serializer.save(course=this_course)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = self.create(request, *args, **kwargs)
        this_assignment = Assignment.objects.get(
            course__uid=self.kwargs['uid'], name=request.data['name'], descr_link=request.data['descr_link'])
        try:
            MWCourseAddAssignment(
                self.kwargs['uid'], this_assignment.name, str(this_assignment.uid))
            repo = MWCourseAddRepo(self.kwargs['uid'], str(this_assignment.uid), [
            ], repo_name='_grading_script', owner_uid=None)
            git_repo = repo.response.json().get('ssh_url_to_repo')
            this_assignment.git_org_add = git_repo[0:-len('_grading_script')]
        except (MiddlewareError, MWUpdateError):
            return JsonResponse(data={}, status=500)
        if isinstance(response, Response):
            response.data['ssh_url_to_repo'] = git_repo
            response.content = simplejson.dumps(response.data)
        this_course = get_object_or_404(Course, uid=self.kwargs['uid'])
        try:
            for student in this_course.students.all():
                if student.user:
                    MWCourseAddRepo(this_course.uid, this_assignment.uid,
                                    student.enroll_email, owner_uid=student.user.uid)
        except:
            return JsonResponse(status=500, data={})
        return response


class assignmentDetail(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    '''
    `/course/<str:course_id>/assignment/<str:assignment_id>`
    '''
    serializer_class = AssignmentSerializer
    permission_classes = (assignmentInfoReadWritePermisson, IsAuthenticated)
    queryset = Assignment.objects.all()

    def get_object(self):
        queryset = self.get_queryset()
        obj = get_object_or_404(
            queryset, uid=self.kwargs['assignment_id'], course__uid=self.kwargs['course_id'])
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # TODO: notify using redis.
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        # TODO: notify using redis.
        return self.delete(request, *args, **kwargs)


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
            return JsonResponse(data={}, status=401)
        if not this_course.instructor.filter(user__uid=request.user.uid).exists():
            return JsonResponse(data={}, status=403)
        try:
            validate_email(request.data['enroll_email'])
        except ValidationError:
            return JsonResponse(status=400, data={})
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
            return JsonResponse(data={}, status=403)
        this_instr = this_course.instructor.get(
            enroll_email=self.kwargs['instr_email'])
        if this_instr.user.uid == this_course.creator:
            return JsonResponse(data={'cause': "You could not delete creator from a course's instructor list."}, status=403)
        if not this_instr.exists():
            return JsonResponse(data={}, status=404)
        response = JsonResponse(data=this_instr, safe=False, status=201)
        this_course.instructor.remove(this_instr)
        return response


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
            return JsonResponse(data={}, status=403)
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
            MWCourseAddRepo(
                self.kwargs['course_id'], assignment.uid, request.data['enroll_email'], owner_uid=this_student.uid)
        return JsonResponse(data=this_student, status=201, safe=False)


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
            return JsonResponse(data={}, status=403)
        try:
            this_student = this_course.students.get(
                enroll_email=self.kwargs['student_email'])
        except:
            return JsonResponse(data={}, status=404)
        response = JsonResponse(data=this_student, safe=False, status=201)
        this_course.students.remove(this_student)
        return response


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
            return JsonResponse(data={}, status=404)
        if not this_judge.maintainer == request.user:
            return JsonResponse(data={}, status=403)
        try:
            this_course = Course.objects.get(uid=self.kwargs['course_id'])
        except:
            return JsonResponse(data={}, status=404)
        try:
            this_course.instructor.get(uer__uid=request.user.uid)
        except:
            return JsonResponse(data={}, status=403)
        this_course.judge.add(this_judge)
        return JsonResponse(JudgeSerializer(this_judge), safe=False, status=201)


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
            return JsonResponse(data={}, status=404)
        try:
            this_course.instructor.get(user__uid=request.user.uid)
        except:
            return JsonResponse(data={}, status=403)
        this_judge = Judge.objects.get(uid=request.data['uid'])
        this_course.default_judge.remove(this_judge)
        return JsonResponse(JudgeSerializer(this_judge), safe=False, status=201)


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
            this_judge = Judge.objects.get(uid=request.data['uid'])
        except:
            return JsonResponse(data={}, status=404)
        if not this_judge.maintainer == request.user.instructor:
            return JsonResponse(data={}, status=403)
        try:
            this_assignment = Assignment.objects.get(
                uid=self.kwargs['assignment_id'])
        except:
            return JsonResponse(data={}, status=404)
        try:
            this_assignment.course.instructor.get(user__uid=request.user.uid)
        except:
            return JsonResponse(data={}, status=403)
        this_assignment.judge.add(this_judge)
        this_redis = redis.Redis(connection_pool=redisConnectionPool)
        this_redis.publish('assignment_judge', request.data['uid'])
        return JsonResponse(JudgeSerializer(this_judge), safe=False, status=201)


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
            this_assignment = Assignment.objects.get(uid=self.kwargs['assignment_id'], course__uid=self.kwargs['course_id'])
        except:
            return JsonResponse(data={}, status=404)
        try:
            this_assignment.course.instructor.get(user__uid=request.user.uid)
        except:
            return JsonResponse(data={}, status=403)
        this_judge = Judge.objects.get(uid=self.kwargs['judge_id'])
        this_assignment.judge.delete(this_judge)
        this_redis = redis.Redis(connection_pool=redisConnectionPool)
        this_redis.publish('assignment_judge', request.data['uid'])
        return JsonResponse(JudgeSerializer(this_judge), safe=False, status=201)


class submissionHistoryList(generics.GenericAPIView, mixins.ListModelMixin):
    '''
    `/student/<str:student_id>/course/<str:course_id>/assignment/<str:assignment_id>/history/`
    '''
    serializer_class = SubmissionRecordSerializer
    permission_classes = (submissionRecordReadPermission, IsAuthenticated)
    queryset = Record.objects.all()

    def get_object(self):
        this_student = self.kwargs['student_id']
        this_assignment = self.kwargs['assignment_id']
        queryset = self.get_queryset()
        obj = get_list_or_404(
            queryset, student__user__uid=this_student, assignment__uid=this_assignment)
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
    queryset = Record.objects.all()

    def get_object(self):
        this_student = self.kwargs['student_id']
        this_assignment = self.kwargs['assignment_id']
        this_record = self.kwargs['git_commit_id']
        queryset = self.get_queryset()
        obj = get_list_or_404(
            queryset, student__user__uid=this_student, assignment__uid=this_assignment, git_commit_id=this_record)
        return obj

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class instrJudgeList(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    '''
    `/judge/`
    '''
    serializer_class = JudgeSerializer
    permission_classes = (judgeReadWritePermission, IsAuthenticated)
    queryset = Judge.objects.all()

    def get_object(self):
        obj = get_list_or_404(self.get_queryset(),
                              maintainer=self.request.user.instructor)
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
    queryset = Judge.objects.all()

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
            pending_list.append(submission)
        return JsonResponse(pending_list, status=200, safe=False)


class internalSubmissionInterface(generics.GenericAPIView):
    '''
    `/internal/subbmission/`
    '''

    def post(self, request, *args, **kwargs):
        auth_token = request.META.get("HTTP_AUTHORIZATION")
        if auth_token != OJ_SUBMISSION_TOKEN:
            return JsonResponse(status=401, data={})
        this_submission = simplejson.dumps(request.DATA)
        this_redis = redis.Redis(connection_pool=redisConnectionPool)
        now = int(time.time())
        payload = {'upstream': request.data['upstream'], "owner_uids": simplejson.loads(
            request.data['additional_data']), 'receive_time': now}
        payload = simplejson.dumps(payload)
        this_redis.zadd(request.data["assignment_uid"], {
                        payload: now})
        return Response(data=this_submission, status=201)


class oauthLoginParam(generics.GenericAPIView):
    '''
    `/user/login/oauth/param`
    '''

    def get(self, request, *args, **kwargs):
        host = request.META.get('HTTP_HOST')
        # if OJ_ENFORCE_HTTPS else request.MATA.get['HTTP_X_FORWARDED_PROTO']
        schema = "https://"
        return JsonResponse(status=200, data={'login_url': schema+host+reverse('oidc_authentication_init')})
