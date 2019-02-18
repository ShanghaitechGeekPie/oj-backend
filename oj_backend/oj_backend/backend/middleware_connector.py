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

# TODO: implement this part accordding to interfaces provided by `oj-gitlab-middleware`.

import os
import simplejson
from secrets import choice
from string import ascii_letters, digits
from requests import post
from urllib.parse import quote
from requests.exceptions import RequestException, ConnectionError, HTTPError, Timeout

OJBN_GITLAB_ADDR = os.environ['OJBN_GITLAB_ADDR']


def get_course_project_name(code, year, semaster):
    return "{}-{}{}".format(code, year, semaster)


class MiddlewareError(BaseException):

    '''
    Base exception class for middleware error.
    '''

    def __init__(self, cause="Unkown Error."):
        self.__cause__ = cause


class MWUpdateError(MiddlewareError):

    '''
    Exception for the middleware failed to update a user's information, because of bad parameters.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class baseMiddlewareAdopter:
    '''
    This is the base adopter for web interface provided by oj-middleware.
    '''

    def __init__(self, api_server=None, interface=None, payload=None):
        self.api_server = api_server
        self.interface = interface
        self._send_request(payload)

    def _send_request(self, payload):
        api_url = "{}/{}".format(self.api_server, self.interface)
        try:
            request = post(api_url, json=payload)
            request.raise_for_status()
        except (ConnectionError, Timeout):
            raise MiddlewareError(
                cause='The connection to middleware server is either broken or timeout.')
        except HTTPError:
            cause = request.json().get('cuase') if request.json().get(
                'cuase') else "Middleware server returns with an unexplianed status code {}.".format(request.status_code)
            raise MWUpdateError(cause=cause)

    @staticmethod
    def gen_passwd():
        dict = ascii_letters + digits
        return ''.join(choice(dict) for _ in range(16))


class MWUpdateUser(baseMiddlewareAdopter):

    def __init__(self, user_email, api_server=OJBN_GITLAB_ADDR):
        payload = {'email': user_email,
                   'password': baseMiddlewareAdopter.gen_passwd()}
        super().__init__(api_server=api_server, interface='/users', payload=payload)


class MWUpdateUserKey(baseMiddlewareAdopter):

    def __init__(self, user_email, user_key, api_server=OJBN_GITLAB_ADDR):
        payload = {'key': user_key}
        interface = '/users/{}/key'.format(quote(user_email))
        super().__init__(api_server=api_server, interface=interface, payload=payload)


class MWUpdateCourse(baseMiddlewareAdopter):

    def __init__(self, course_name, course_uid, api_server=OJBN_GITLAB_ADDR):
        payload = {"name": course_name, "uuid": course_uid}
        super().__init__(api_server=api_server, interface='/courses', payload=payload)


class MWCourseAddInstr(baseMiddlewareAdopter):

    def __init__(self, course_uid, instr_email, api_server=OJBN_GITLAB_ADDR):
        payload = {"instructor_name": instr_email}
        interface = '/courses/{}/instructors'
        super().__init__(api_server=api_server, interface=interface, payload=payload)


class MWCourseAddAssignment(baseMiddlewareAdopter):

    def __init__(self, course_uid, assignment_name, assignment_uid, api_server=OJBN_GITLAB_ADDR):
        payload = {'name': assignment_name, 'uuid': assignment_uid}
        interface = '/courses/{}/assignments'.format(course_uid)
        super().__init__(api_server=api_server, interface=interface, payload=payload)


class MWCourseAddStudent(baseMiddlewareAdopter):
    def __init__(self, course_uid, assignment_uid, student_email, api_server=OJBN_GITLAB_ADDR):
        interface = "/courses/{}/assignments/{}/repos".format(
            course_uid, assignment_uid)
        if not isinstance(student_email, list):
            repo_name = student_email.split('@')[0]
            student_email = [student_email]
        else:
            repo_name = 'group_' + \
                "_".join(user.split('@')[0] for user in student_email)
        payload = {'owner_email': student_email, 'repo_name': repo_name}
        super().__init__(api_server=api_server, interface=interface, payload=payload)

# TODO:
# Write adopters for downloading a user's repo and get its commit history.
# This function requries the backend to act like a reserve proxy between user and middleware.
