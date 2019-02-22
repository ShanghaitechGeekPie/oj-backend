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
    serializer_class = StudentInfoSerializer
    permission_classes = (userInfoReadWritePermission,)
    lookup_field = 'uid'

    def get_queryset(self):
        #student_uid = self.kwargs['uid']
        #return Student.objects.get(user__uid=student_uid)
        return Stduent.objects.all()

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = self.update(request, *args, **kwargs)
        email = self.get_queryset().user.email
        user_key = self.get_queryset().user.rsa_pub_key
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
    serializer_class = InstructorInfoSerializer
    permission_classes = (userInfoReadWritePermission,)
    lookup_field = 'uid'

    def get_queryset(self):
        instr_uid = self.kwargs['uid']
        return Instructor.objects.all()

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = self.update(request, *args, **kwargs)
        email = self.get_queryset().user.email
        user_key = self.get_queryset().user.rsa_pub_key
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
        if request.user is AnonymousUser:
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
    permission_classes = (courseReadWritePermission,)

    def get_queryset(self):
        student_uid = self.request.user.uid
        return Course.objects.filter(student__user__uid=student_uid)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class courseList4Instr(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    '''
    `/insturctor/<str:uid>/course/`
    '''
    serializer_class = CoursesSerializer
    permission_classes = (courseReadWritePermission,)

    def get_queryset(self):
        instr_uid = self.request.user.uid
        return Course.objects.filter(instructor__user__uid=instr_uid)

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = self.create(request, *args, **kwargs)
        this_course = Course.objects.filter(name=request.data['name'], year=int(
            request.data['year']), semaster=request.data['semaster'])
        try:
            MWUpdateCourse(this_course.name, this_course.uid)
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
    permission_classes = (assignmentInfoReadWritePermisson,)

    def get_queryset(self):
        this_student = self.kwargs['student_id']
        this_course = self.kwargs['course_id']
        return Assignment.objects.filter(course__uid=this_course, student__user__uid=this_student)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class courseInformation(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    '''
    `/course/<str:course_id>`
    '''
    serializer_class = CoursesSerializer
    permission_classes = (courseReadWritePermission,)

    def get_queryset(self):
        course_uid = self.kwargs['uid']
        return Course.objects.get(uid=course_uid)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        response = self.update(request, *args, **kwargs)
        this_course = self.get_queryset()
        try:
            MWUpdateCourse(this_course.name, this_course.uid)
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
    permission_classes = (assignmentInfoReadWritePermisson,)

    def get_queryset(self):
        this_course = self.kwargs['uid']
        this_instr = self.request.user.uid
        return Assignment.objects.filter(course__uid=this_course, course__instructor__user__uid=this_instr)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # TODO: notify using redis.
        response = self.create(request, *args, **kwargs)
        this_assignment = Assignment.objects.get(
            course__uid=self.kwargs['uid'], name=request.data['name'], descr_link=request.data['descr_link'])
        try:
            MWCourseAddAssignment(
                self.kwargs['uid'], this_assignment.name, this_assignment.uid)
            repo = MWCourseAddRepo(self.kwargs['uid'], this_assignment.uid, [
            ], repo_name='_grading_script', owner_uid=None)
            git_repo = repo.response.json().get('ssh_url_to_repo')
        except (MiddlewareError, MWUpdateError):
            return JsonResponse(data={}, status=500)
        if isinstance(response, Response):
            response.data['ssh_url_to_repo'] = git_repo
            response.content = simplejson.dumps(response.data)
        return response


class assignmentDetail(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    '''
    `/course/<str:course_id>/assignment/<str:assignment_id>`
    '''
    serializer_class = AssignmentSerializer
    permission_classes = (assignmentInfoReadWritePermisson, )

    def get_queryset(self):
        return Assignment.objects.filter(uid=self.kwargs['assignment_id'], course__uid=self.kwargs['course_id'])

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
    permission_classes = (courseInstrInfoReadWritePermission,)

    def get_queryset(self):
        this_course = Course.objects.get(uid=self.kwargs['uid'])
        return this_course.instructor.all()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        this_course = Course.objects.get(uid=self.kwargs['uid'])
        if not this_course.instructor.filter(user__uid=request.user.uid).exists():
            return JsonResponse(data={}, status=403)
        try:
            validate_email(request.data['email'])
        except ValidationError:
            return JsonResponse(status=400, data={})
        try:
            this_instr = Instructor.objects.get(user__email=request.data['email'])
        except:
            this_instr = Instructor(
                enroll_email=request.data['email'], user=None)
            try:
                this_user = User.objects.get(email=request.data['email'])
                this_instr.user = this_user
            except:
                pass
            this_instr.save()
        this_course.instructor.add(this_instr)
        MWCourseAddInstr(
            course_uid=self.kwargs['uid'], instr_email=request.data['email'])
        return JsonResponse(data={}, status=201)


class courseInstrDetail(generics.GenericAPIView, mixins.RetrieveModelMixin, mixins.DestroyModelMixin):
    '''
    `/course/<str:course_id>/instructor/<str:instr_email>`
    '''
    serializer_class = InstructorBasicInfoSerializer
    permission_classes = (courseInstrInfoReadWritePermission,)

    def get_queryset(self):
        this_course = Course.objects.get(uid=self.kwargs['course_id'])
        return this_course.instructor.get(enroll_email=self.kwargs['instr_email'])

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
        this_instr.delete()
        return response


class courseStudentList(generics.GenericAPIView, mixins.ListModelMixin):
    '''
    `/course/<str:course_id>/student/`
    '''
    serializer_class = StudentBasicInfoSerializer
    permission_classes = (courseStudentInfoReadWritePermission)

    def get_queryset(self):
        return Course.objects.get(uid=self.kwargs['course_id']).student.all()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        this_course = Course.objects.get(uid=self.kwargs['uid'])
        if not this_course.instructor.filter(user__uid=request.user.uid).exists():
            return JsonResponse(data={}, status=403)
        try:
            validate_email(request.data['email'])
        except ValidationError:
            return JsonResponse(status=400, data={})
        try:
            this_student = Student.objects.get(user__email=request.data['email'])
        except:
            this_student = Student(enroll_email=request.data['email'], user=None)
            try:
                this_user = User.objects.get(email=request.data['email'])
                this_student.user = this_user
            except:
                pass
            this_student.save()
            MWUpdateUser(request.data['email'])
        this_course.student.add(this_student)
        for assignment in this_course.assignment_set.all():
            MWCourseAddRepo(
                self.kwargs['course_id'], assignment.uid, request.data['email'], owner_uid=this_student.uid)
        return JsonResponse(data={}, status=201)


class courseStudentDetail(generics.GenericAPIView, mixins.RetrieveModelMixin):
    '''
    `/course/<str:course_id>/student/<str:student_email>`
    '''

    serializer_class = StudentBasicInfoSerializer
    permission_classes = (courseStudentInfoReadWritePermission)

    def get_queryset(self):
        return Course.objects.get(uid=self.kwargs['course_id']).student.get(enroll_email=self.kwargs['student_email'])

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        this_course = Course.objects.get(uid=self.kwargs['course_id'])
        if not this_course.instructor.filter(user__uid=request.user.uid).exists():
            return JsonResponse(data={}, status=403)
        try:
            this_student = this_course.student.get(enroll_email=self.kwargs['student_email'])
        except:
            return JsonResponse(data={}, status=404)
        response = JsonResponse(data=this_student, safe=False, status=201)
        this_student.delete()
        return response


class courseJudgeList(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    '''
    `/course/<str:course_id>/judge/`
    '''
    serializer_class = courseJudgeSerializer
    permission_classes = (courseJudgeReadWritePermisson,)

    def get_queryset(self):
        this_course = Course.objects.get(uid=self.kwargs['course_id'])
        return this_course.judge.all()

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
    permission_classes = (courseJudgeReadWritePermisson)

    def get_queryset(self):
        this_course = Course.objects.get(uid=self.kwargs['course_id'])
        return this_course.judge.get(uid=self.kwargs['judge_id'])

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
        this_course.judge.delete(this_judge)
        return JsonResponse(JudgeSerializer(this_judge), safe=False, status=201)


class assignmentJudgeList(generics.GenericAPIView, mixins.ListModelMixin):
    '''
    `/course/<str:course_id>/assignment/<str:assignment_id>/judge/`
    '''
    serializer_class = courseJudgeSerializer
    permission_classes = (courseJudgeReadWritePermisson,)

    def get_queryset(self):
        this_assignment = Assignment.objects.filter(
            uid=self.kwargs['assignment_id'], course__uid=self.kwargs['course_id'])
        return this_assignment.judge.all()

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
            this_assignment = Assignment.objects.get(uid=self.kwargs['assignment_id'])
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
    permission_classes = (courseJudgeReadWritePermisson)

    def get_queryset(self):
        this_assignment = Assignment.objects.get(
            uid=self.kwargs['assignment_id'], course__uid=self.kwargs['course_id'])
        return this_assignment.judge.get(uid=self.kwargs['judge_id'])

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
        this_course.judge.delete(this_judge)
        this_redis = redis.Redis(connection_pool=redisConnectionPool)
        this_redis.publish('assignment_judge', request.data['uid'])
        return JsonResponse(JudgeSerializer(this_judge), safe=False, status=201)


class submissionHistoryList(generics.GenericAPIView, mixins.ListModelMixin):
    '''
    `/student/<str:student_id>/course/<str:course_id>/assignment/<str:assignment_id>/history/`
    '''
    serializer_class = SubmissionRecordSerializer
    permission_classes = (submissionRecordReadPermission,)

    def get_queryset(self):
        this_student = self.kwargs['student_id']
        this_assignment = self.kwargs['assignment_id']
        return Record.objects.filter(student__user__uid=this_student, assignment__uid=this_assignment)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class submissionHistoryDetail(generics.GenericAPIView, mixins.RetrieveModelMixin):
    '''
    `/student/<str:student_id>/course/<str:course_id>/assignment/<str:assignment_id>/history/<str:git_commit_id>`
    '''
    serializer_class = SubmissionRecordSerializer
    permission_classes = (submissionRecordReadPermission)

    def get_queryset(self):
        this_student = self.kwargs['student_id']
        this_assignment = self.kwargs['assignment_id']
        this_record = self.kwargs['git_commit_id']
        return Record.objects.filter(student__user__uid=this_student, assignment__uid=this_assignment, git_commit_id=this_record)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class instrJudgeList(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    '''
    `/judge/`
    '''
    serializer_class = JudgeSerializer
    permission_classes = (judgeReadWritePermission,)

    def get_queryset(self):
        this_user = self.request.user
        return Judge.objects.filter(maintainer=this_user.instructor)

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class instrJudgeDetail(generics.GenericAPIView, mixins.UpdateModelMixin, mixins.DestroyModelMixin, mixins.RetrieveModelMixin):
    '''
    `/judge/<str:uid>`
    '''
    serializer_class = JudgeSerializer
    permission_classes = (judgeReadWritePermission)

    def get_queryset(self):
        this_user = self.request.user
        return Judge.objects.filter(maintainer=this_user.instructor, uid=self.kwargs['uid'])

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
    permission_classes = (recordReadOnly,)

    def get_queryset(self):
        this_assignment = self.kwargs['course_id']
        this_course = self.kwargs['assignment_id']
        this_course_student_list = Course.objects.get(
            uid=this_course).student.all()
        query_set = None
        for this_student in this_course_student_list:
            this_student_record = Record.objects.filter(
                student=this_student, assignment__uid=this_assignment).order_by('-submission_time')[0]
            if query_set:
                query_set = query_set | this_student_record
            else:
                query_set = this_course_student_list
        return query_set

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class pendingAssignment(generics.GenericAPIView, mixins.ListModelMixin):
    '''
    `/course/<str:course_id>/assignment/<str:assignment_id>/queue/`
    '''

    def get(self, request, course_id):
        if request.user is AnonymousUser:
            return Response(data={}, status=401)
        if not (Course.objects.get(uid=course_id).insturctor.filter(user__uid=request.user.uid).exists() or Course.objects.filter(uid=course_id).student.get(user__uid=request.user.uid).exists()):
            return Response(data={}, status=403)
        redis_server = redis.Redis(
            connection_pool=redisConnectionPool)
        all_pending = redis_server.zrange(self.kwargs['assignment_id'], 0, -1)
        pending_list = []
        for submission in all_pending:
            submission = simplejson.loads(submission)
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
        payload = {'upstream': request.data['upstream'], "owner_uids": simplejson.loads(
            request.data['additional_data'])}
        payload = simplejson.dumps(payload)
        this_redis.zadd(request.data["assignment_uid"], {
                        payload: time.time()})
        return Response(data=this_submission, status=201)


class oauthLoginParam(generics.GenericAPIView):
    '''
    `/user/login/oauth/param`
    '''

    def get(self, request, *args, **kwargs):
        host = request.META.get('HTTP_HOST')
        schema = "https://" #if OJ_ENFORCE_HTTPS else request.MATA.get['HTTP_X_FORWARDED_PROTO']
        return JsonResponse(status=200, data={'login_url': schema+host+reverse('oidc_authentication_init')})
