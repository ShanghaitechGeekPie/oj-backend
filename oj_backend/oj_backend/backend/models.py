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


from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


def uuid1str():
    return uuid.uuid1().hex


class User(AbstractUser):
    uid = models.CharField(unique=True, max_length=32,
                           verbose_name="用户标识符", editable=False, default=uuid1str)
    #email = models.EmailField(verbose_name="电子邮箱")
    # email is specified in the AbstractUser class.
    name = models.CharField(max_length=255, verbose_name="姓名")
    rsa_pub_key = models.FileField(verbose_name="SSH 公钥")
    #disabled = models.BooleanField(verbose_name="禁用", default=False)
    # use the is_active attribute from AbstractUser.
    USERNAME_FIELD = 'email'


class Student(User):
    student_id = models.CharField(max_length=255, verbose_name="学号")
    nickname = models.CharField(max_length=255, verbose_name="昵称")

    class Meta:
        ordering = ['student_id']

    def __str__(self):
        return "{}[{}]‘{}’<{}>".format(self.name, self.student_id, self.nickname, self.email)


class Instructor(User):

    class Meta:
        ordering = ['uid']

    def __str__(self):
        return "{}<{}>".format(self.name, self.email)


class Course(models.Model):
    uid = models.CharField(unique=True, max_length=32,
                           verbose_name="课程唯一标识符", editable=False, default=uuid1str)
    code = models.CharField(max_length=255, verbose_name="课程代码")
    name = models.CharField(max_length=255, verbose_name="课程名称")
    year = models.IntegerField(verbose_name="学年")
    semaster = models.CharField(max_length=255, verbose_name="学期")
    homepage = models.URLField(max_length=512, verbose_name="课程主页")
    instructor = models.ManyToManyField(
        Instructor, verbose_name="教师", on_delete=models.SET_NULL)
    students = models.ManyToManyField(
        Student, verbose_name="学生", on_delete=models.SET_NULL)

    class Meta:
        ordering = ['code', 'year', 'semaster']

    def __str__(self):
        return "{}: {}({})".format(self.code, self.name, self.semaster)


class Assignment(models.Model):
    uid = models.CharField(unique=True, max_length=32,
                           verbose_name="唯一标识符", editable=False, default=uuid1str)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    name = models.CharField(max_length="名称")
    descr_link = models.URLField(max_length=512, verbose_name="作业描述链接")
    grade = models.FloatField(verbose_name="总成绩")
    deadline = models.DateTimeField(verbose_name="截止日期")
    release_date = models.DateTimeField(verbose_name="发布日期")

    class Meta:
        ordering = ['release_date', 'deadline']

    def __str__(self):
        return "{} - {} <{}>".format(self.course, self.name, self.descr_link)


class Record(models.Model):
    student = models.ForeignKey(
        Student, verbose_name="提交用户", on_delete=models.CASCADE)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    massage = models.FileField(verbose_name="返回消息")
    grade = models.IntegerField(verbose_name="成绩")
    git_commit_id = models.CharField(
        max_length=40, unique=True, verbose_name="git提交号码")
    grade_time = models.DateTimeField()

    class Meta:
        ordering = ['grade_time']

    def __str__(self):
        return "{} - {}".format(self.grade_time, self.git_commit_id)
