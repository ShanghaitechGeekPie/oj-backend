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
from datetime import datetime
from django.views import View
from django.db.models import Max, F, Q
from django.db.models.expressions import RawSQL
from django.db import connection
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.core.validators import validate_email, validate_ipv46_address
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed, Http404, HttpResponse, HttpResponseForbidden
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.urls import path, include, reverse
from django.utils import timezone
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
            if not MW_if_user_exists(instr.enroll_email):
                try:
                    MWUpdateUser(instr.enroll_email)
                except (MiddlewareError, MWUpdateError):
                    return JsonResponse(data={'cause': 'Git server error.'}, status=500)
            try:
                MWCourseAddInstr(this_course.uid, instr.enroll_email)
            except (MiddlewareError, MWUpdateError):
                return JsonResponse(data={'cause': 'Git server error.'}, status=500)
        return response


class assignmentList4Student(generics.GenericAPIView):
    '''
    `/student/<str:student_id>/course/<str:course_id>/assignment/`
    '''

    def get(self, request, *args, **kwargs):
        this_student = get_object_or_404(
            Student, user__uid=self.kwargs['student_id'])
        this_course = get_object_or_404(
            this_student.course_set.all(), uid=self.kwargs['course_id'])
        this_assignment_set = this_course.assignment_set.all()
        
        BASE="""
        DROP TABLE IF EXISTS gitidtableS;
        CREATE TEMPORARY TABLE gitidtableS (gitid VARCHAR(40));
        DROP PROCEDURE
        IF EXISTS Id2R;
        CREATE PROCEDURE Id2R (aid VARCHAR(32))
        BEGIN
            INSERT INTO gitidtableS SELECT
                `oj_database_record`.`commit_tag`
            FROM
                `oj_database_record`
            INNER JOIN `oj_database_record_student` ON (
                `oj_database_record`.`id` = `oj_database_record_student`.`record_id`
            )
            WHERE
                (
                    `oj_database_record`.`assignment_id` = aid
                    AND `oj_database_record_student`.`student_id` = {student_id}
                )
            ORDER BY
                `oj_database_record`.`submission_time` DESC
            LIMIT 1;
        END;
        {call}
        """
        SQL = BASE.format(
            student_id=this_student.id,
            call="".join(["CALL Id2R('{}');".format(str(assign.uid).replace("-", ""))
                          for assign in this_assignment_set])
        )
        with connection.cursor() as cursor:
            cursor.execute(SQL)
            cursor.execute("SELECT * FROM gitidtableS;")
            gitids = [i[0]for i in cursor.fetchall()]
        
        last_rec = Record.objects.filter(commit_tag__in=gitids)
        last_rec = {i['assignment_id']: i['grade'] for i in list(last_rec.values())}
        assignment_with_grade = list(this_assignment_set.values\
                ('uid', 'course_id', 'name', 'descr_link', 'deadline',\
                 'release_date', 'deadline', 'short_name', overall_score=F('grade')))
        for i in range(len(assignment_with_grade)):
            try:
                assignment_with_grade[i]['score'] = last_rec[assignment_with_grade[i]['uid']]
            except KeyError:
                assignment_with_grade[i]['score'] = 0
                
        assignment_with_grade = sorted(
            assignment_with_grade,
            key=lambda x: (x["deadline"], x["release_date"], x["name"])
        )

        return JsonResponse(assignment_with_grade, safe=False)


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
        return this_course.assignment_set.all().order_by("deadline","release_date","name")

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
            this_assignment.git_org_addr = git_repo.split('_grading_script')[0]
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
    serializer_class = AssignmentDetailSerializer
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
        this_course = Course.objects.get(uid=self.kwargs['course_id'])
        this_assignment = Assignment.objects.get(
            uid=self.kwargs['assignment_id'])
        MWCourseDelAssignment(this_course.uid, this_assignment.uid)
        return self.destroy(request, *args, **kwargs)


class courseInstrList(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    '''
     `/course/<str:uid>/instructor/`
    '''
    serializer_class = InstructorBasicInfoSerializer
    permission_classes = (courseInstrInfoReadWritePermission, IsAuthenticated)

    def get_queryset(self):
        this_course = get_object_or_404(Course, uid=self.kwargs['uid'])
        return this_course.instructor.all()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        this_course = Course.objects.get(uid=self.kwargs['uid'])
        if not request.user.is_authenticated:
            return JsonResponse(data={'cause': 'Unauthorized'}, status=401)
        if not this_course.instructor.filter(user__uid=request.user.uid).exists():
            return JsonResponse(data={'cause': 'Forbidden'}, status=403)
        try:
            enroll_email = request.data['enroll_email']
        except KeyError:
            return JsonResponse(data={'cause': 'Bad Request.'})
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

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        this_course = Course.objects.get(uid=self.kwargs['course_id'])
        if not this_course.instructor.filter(user__uid=request.user.uid).exists():
            return JsonResponse(data={'cause': 'Forbidden'}, status=403)
        try:
            enroll_email = request.data['enroll_email']
            student_id = request.data['student_id']
        except KeyError:
            return JsonResponse(data={'cause': 'Bad Request.'})
        try:
            validate_email(enroll_email)
        except ValidationError:
            return JsonResponse(status=400, data={'cause': 'invalid email'})
        try:
            this_student = Student.objects.get(
                enroll_email=enroll_email)
        except:
            this_student = Student(
                enroll_email=enroll_email, user=None, student_id=student_id)
            try:
                this_user = User.objects.get(email=enroll_email)
                this_student.user = this_user
            except:
                pass
            this_student.save()
            MWUpdateUser(enroll_email)
        this_course.students.add(this_student)
        if this_student.user:
            for assignment in this_course.assignment_set.all():
                MWCourseAddRepo(self.kwargs['course_id'], assignment.uid, enroll_email,
                                assignment.deadline, owner_uid=this_student.user.uid)
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
                MWCourseDelRepo(this_course.uid, assignment.uid,
                                this_student.enroll_email)
        return HttpResponse(content='', status=204)


class courseJudgeList(generics.GenericAPIView, mixins.ListModelMixin, mixins.CreateModelMixin):
    '''
    `/course/<str:course_id>/judge/`
    '''
    serializer_class = courseJudgeSerializer
    permission_classes = (courseJudgeReadWritePermisson, IsAuthenticated)

    def get_queryset(self):
        return get_object_or_404(Course, uid=self.kwargs['course_id']).default_judge.all()

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
        this_judge = get_object_or_404(Judge.objects.all(), uid=self.kwargs['judge_id'] )
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

        try:
            this_assignment = Assignment.objects.get(
                uid=self.kwargs['assignment_id'])
        except:
            return JsonResponse(data={''}, status=404)

        if not this_assignment.course.instructor.filter(user__uid=request.user.uid).exists():
            return JsonResponse(data={'cause': 'Forbidden'}, status=403)

        if (not this_assignment.course.default_judge.filter(uid=this_judge.uid).exists()) and \
                this_judge.maintainer.user != request.user:  # if the judge neither belongs to course nor the person
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
        return this_student.record_set.filter(assignment=this_assignment).order_by('-submission_time')

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
        obj = queryset.get(student__user__uid=this_student,
                           assignment__uid=this_assignment, commit_tag=this_record)
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

    def get_object(self):
        obj = get_object_or_404(Judge.objects.all(), uid=self.kwargs['uid'])
        self.check_object_permissions(self.request, obj)
        return obj

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)


class assignmentScoreboardDetail(generics.GenericAPIView):
    '''
    `/course/<str:course_id>/assignment/<str:assignment_id>/scores/`
    '''
    permission_classes = (courseStudentInfoReadWritePermission, IsAuthenticated)

    def get(self, request, *args, **kwargs):
        this_course = self.kwargs['course_id']
        this_assignment = self.kwargs['assignment_id']
        this_course_student_list = get_object_or_404(Course, uid=this_course).students.all().values("id", "user_id", "nickname", "user__name", "student_id")

        BASE="""
        DROP TABLE IF EXISTS gitidtable;
        CREATE TEMPORARY TABLE gitidtable (
            gitid VARCHAR (40),
            gitcount INT
        );
        DROP PROCEDURE
        IF EXISTS Id2R;
        CREATE PROCEDURE Id2R (id INT)
        BEGIN
            INSERT INTO gitidtable SELECT
                *
            FROM
                (
                    SELECT
                        `oj_database_record`.`commit_tag`
                    FROM
                        `oj_database_record`
                    INNER JOIN `oj_database_record_student` ON (
                        `oj_database_record`.`id` = `oj_database_record_student`.`record_id`
                    )
                    WHERE
                        (
                            `oj_database_record`.`assignment_id` = '{assignment_id}'
                            AND `oj_database_record_student`.`student_id` = id
                        )
                    ORDER BY
                        `oj_database_record`.`submission_time` DESC
                    LIMIT 1
                ) AS T1
            INNER JOIN (
                SELECT
                    count(*)
                FROM
                    `oj_database_record`
                INNER JOIN `oj_database_record_student` ON (
                    `oj_database_record`.`id` = `oj_database_record_student`.`record_id`
                )
                WHERE
                    (
                        `oj_database_record`.`assignment_id` = '{assignment_id}'
                        AND `oj_database_record_student`.`student_id` = id
                    )
            ) AS T2;
        END;
        {call}
        """
        SQL = BASE.format(
            assignment_id=this_assignment.replace("-", ""),
            call="".join(["CALL Id2R({});".format(stu['id'])
                          for stu in this_course_student_list])
        )
        with connection.cursor() as cursor:
            cursor.execute(SQL)
            cursor.execute("SELECT * FROM gitidtable;")
            gitid2times = {i[0]:i[1] for i in cursor.fetchall()}
            gitids = [i for i in gitid2times]
        
        last_rec = Record.objects.filter(commit_tag__in=gitids).order_by('-grade')

        backend_logger.info('Searching scoreboard for: {}; last_rec: {}'.format(
                this_assignment, str(last_rec.values())))
        oscore = get_object_or_404(Assignment,uid=this_assignment).grade

        student_with_grade = []
        stu_set=set()
        for i in last_rec.values("student__user_id", "student__nickname", "student__user__name", "student__student_id", 'grade', 'delta', 'submission_time' ,"commit_tag"):
            stu_set.add(i['student__user_id'])
            student_with_grade.append({
                'nickname': i['student__nickname'],
                "name": i["student__user__name"],
                "student_id": i["student__student_id"],
                'overall_score': oscore,
                'score': i['grade'],
                'delta': i['delta'],
                'submission_time': i['submission_time'],
                'submission_count': gitid2times[i["commit_tag"]]
            })

        for i in this_course_student_list:
            if(not i['user_id'] in stu_set):
                student_with_grade.append({
                    'nickname': i['nickname'],
                    "name": i["user__name"],
                    "student_id": i["student_id"],
                    'overall_score': oscore,
                    'score': 0,
                    'delta': None,
                    'submission_time': None,
                    'submission_count': 0
                })
        
        student_with_grade = sorted(
            student_with_grade,
            key=lambda x: (
                -x['score'],
                x['submission_time'].timestamp() if x['submission_time'] else 10**11
            )
        )
        return JsonResponse(student_with_grade, safe=False)


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
        if upstream.endswith("_grading_script.git"):
            # The upstream stores the grading script.
            payload = simplejson.dumps(payload)
            channel = "grade_script_pushed"
            backend_logger.info('Submission relied. Payload: {}; Channel: {}'.format(
                payload, channel))
            this_redis.publish(channel, payload)
        else:
            # The upstream stores the student's submission.
            R = Record(assignment=Assignment.objects.get(uid=assignment_uid),
                       grade=0,
                       delta=0,
                       grade_time=timezone.make_aware(datetime.fromtimestamp(0)),
                       submission_time=timezone.make_aware(datetime.fromtimestamp(now)),
                       redis_message=simplejson.dumps(payload),
                       state=1)
            R.save()
            stuSet = Student.objects.filter(user__in=owner_uids)
            R.student.add(*stuSet)
            channel = assignment_uid
            payload['record_id'] = R.id
            payload = simplejson.dumps(payload)
            backend_logger.info('Submission relied. Payload: {}; Channel: {}; Weight: {}'.format(
                payload, channel, now))
            this_redis.zadd(channel, {payload: now})
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


class assignmentScoreboardDetail4Student(generics.GenericAPIView):
    '''
    `/student/<str:student_id>/course/<str:course_id>/assignment/<str:assignment_id>/scores/`
    '''

    def get(self, request, *args, **kwargs):
        this_course = self.kwargs['course_id']
        this_assignment = self.kwargs['assignment_id']
        this_course_student_list = get_object_or_404(Course, uid=this_course).students.all().values("id", "user_id", "nickname")

        BASE="""
        DROP TABLE IF EXISTS gitidtable;
        CREATE TEMPORARY TABLE gitidtable (
            gitid VARCHAR (40),
            gitcount INT
        );
        DROP PROCEDURE
        IF EXISTS Id2R;
        CREATE PROCEDURE Id2R (id INT)
        BEGIN
            INSERT INTO gitidtable SELECT
                *
            FROM
                (
                    SELECT
                        `oj_database_record`.`commit_tag`
                    FROM
                        `oj_database_record`
                    INNER JOIN `oj_database_record_student` ON (
                        `oj_database_record`.`id` = `oj_database_record_student`.`record_id`
                    )
                    WHERE
                        (
                            `oj_database_record`.`assignment_id` = '{assignment_id}'
                            AND `oj_database_record_student`.`student_id` = id
                        )
                    ORDER BY
                        `oj_database_record`.`submission_time` DESC
                    LIMIT 1
                ) AS T1
            INNER JOIN (
                SELECT
                    count(*)
                FROM
                    `oj_database_record`
                INNER JOIN `oj_database_record_student` ON (
                    `oj_database_record`.`id` = `oj_database_record_student`.`record_id`
                )
                WHERE
                    (
                        `oj_database_record`.`assignment_id` = '{assignment_id}'
                        AND `oj_database_record_student`.`student_id` = id
                    )
            ) AS T2;
        END;
        {call}
        """
        SQL = BASE.format(
            assignment_id=this_assignment.replace("-", ""),
            call="".join(["CALL Id2R({});".format(stu['id'])
                          for stu in this_course_student_list])
        )
        with connection.cursor() as cursor:
            cursor.execute(SQL)
            cursor.execute("SELECT * FROM gitidtable;")
            gitid2times = {i[0]:i[1] for i in cursor.fetchall()}
            gitids = [i for i in gitid2times]
        
        last_rec = Record.objects.filter(commit_tag__in=gitids).order_by('-grade')

        backend_logger.info('Searching scoreboard for: {}; last_rec: {}'.format(
                this_assignment, str(last_rec.values())))
        oscore = get_object_or_404(Assignment,uid=this_assignment).grade

        student_with_grade = []
        stu_set=set()
        for i in last_rec.values("student__user_id", "student__nickname", 'grade', 'delta', 'submission_time' ,"commit_tag"):
            stu_set.add(i['student__user_id'])
            student_with_grade.append({
                'nickname': i['student__nickname'],
                'overall_score': oscore,
                'score': i['grade'],
                'delta': i['delta'],
                'submission_time': i['submission_time'],
                'submission_count': gitid2times[i["commit_tag"]]
            })

        for i in this_course_student_list:
            if(not i['user_id'] in stu_set):
                student_with_grade.append({
                    'nickname': i['nickname'],
                    'overall_score': oscore,
                    'score': 0,
                    'delta': None,
                    'submission_time': None,
                    'submission_count': 0
                })
        
        student_with_grade = sorted(
            student_with_grade,
            key=lambda x: (
                -x['score'],
                x['submission_time'].timestamp() if x['submission_time'] else 10**11
            )
        )
        return JsonResponse(student_with_grade, safe=False)
