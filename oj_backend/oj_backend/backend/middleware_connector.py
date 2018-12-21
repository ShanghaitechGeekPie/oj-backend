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

# TODO: implement this part accordding to interfaces provided by
# `oj-gitlab-middleware`.
import requests
import os

def get_gitlab_student_repo(student, course, assignment):
        return "{}/{}/{}-{}".format("https://oj.geekpie.club", course, assignment, student)

OJBN_GITLAB_ADDR = os.environ['OJBN_GITLAB_ADDR']

def update_user(email=None, ssh_pub_key=None, uid=None):
    """
    `update_user(email=None, ssh_pub_key=None, uid=None)`

    This function provides interfaces for creating/updating
    student/insturctor's account in GitLab.
    """
    global OJBN_GITLAB_ADDR
    pass

def create_repo(user=None, course=None, assignment=None):
    """
    `create_repo(user=None, course=None, assignment=None)`

    This function provides interfaces for creating new repos for user(s),
    returning URL to the created repo(s)
    """
    global OJBN_GITLAB_ADDR
    if isinstance(user, str):
        user = [user]
    return user

def create_course(course=None, instr=None):
    """
    `create_course(course=None, instr=None)`

    This function provides interfaces for creating new project for a course.
    """
    global OJBN_GITLAB_ADDR
    if isinstance(instr, str):
        instr = [instr]


def get_repo(user=None, course=None, assignemnt=None):
    """
    `get_repo(user=None, course=None, assignemnt=None)`

    TBD
    """
    pass
