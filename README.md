# GeekPie OJ Project: Backend Part

**⚠️ 建设中**

This part provides a RESTful API of user management, course/assignment details for the GeekPie OJ Project. This project is devleloped using `Python 3.x`, ` Django 2.1.3` , `Django RESTful Framework` and `Django OIDC RP`.

## Deploy

This project use `MySQL` as its database. Before installing, make sure you has an accessiable `MySQL` server. Also, this project is designed to work with other micro-service to provide a git-based online programming homework grading system.

Deploying using `Docker` is recommended. Make sure you set the following environment variables correctly before staring the service.


environment variable | description | example
---|---|---
`OJBN_DB_HOST` | the host where the database is hosted. | `localhost`
`OJBN_DB_NAME` | the database name. | `ojdb`
`OJBN_DB_USER` | the user used to acssess the database. | `geekpie`
`OJBN_DB_PASSWD` | the database password for the given user. | `gouliguojiashengsiyi`
`OJBN_HOSTNAME` | the `host` header allowed in a HTTP request. | `oj.geekpie.club`
`OJBN_INTERNAL_HOSTNAME` (optional) | another `host` header allowed in a HTTP request, used for internal submission interface | `backend`
`OJBN_GITLAB_ADDR` | the address where the gitlab middleware is hosted. | `http://localhost:8080`
<del>`OJBN_OAUTH_URL`</del> | <del>the URL of the OAuth service this service is using</del> | <del>`https://gauth.geekpie.club/oauth/login`</del>
`OJBN_REDIS_ADDR` | the address of redis server. Follows the schema of `redis-py` | `redis://[:password]@localhost:6379/0`
`OJ_SUBMISSION_TOKEN` | token for auth betwwen `oj-*-middleware` and `oj-backend` for submission | `woshitoken`
`OJBN_STAGE` |the server is whether a test or a production server. When setted to `production`, the server will try to get the secret key from the environment variable. |`development` or `production`
`OJBN_SECRET_KEY` |the secret key. See https://docs.djangoproject.com/en/2.1/ref/settings/#std:setting-SECRET_KEY | `imarandomstring`
`OIDC_RP_CLIENT_ID` | OpenID client ID | see https://django-oidc-rp.readthedocs.io/en/stable/ for the following varibles
`OIDC_RP_PROVIDER_ENDPOINT` | OpenID RP Provider Endpoint |
`OIDC_RP_CLIENT_SECRET` | OpenID client secret |
`OIDC_OP_AUTHORIZATION_ENDPOINT` | OpenID Authorization Endpoint |
`OIDC_OP_TOKEN_ENDPOINT` | OpenID Token Endpoint |
`OIDC_OP_USER_ENDPOINT`  | OpenID User Endpoint |

## API Schema

The input/output below is for `GET` and `DELETE`. When creating/updating an object using `POST`, the `uid` filed could be omitted.

### For all users


#### Login parameters

Supported method: `GET`

Registered at `/user/auth/oidc/param`

```json
{
    "login_url": "https://oj.geekpie.club/oidc/auth/request/",
    "logout_url": "https://oj.geekpie.club/oidc/end-session/"
}
```

In this example, frontend shall redirect user to `https://gauth.geekpie.club/oauth/login` for login .

#### User's role

Supported method: `GET`

Registered at `/user/role`

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "is_student": true,
    "is_insturctor": false
}
```

#### Claiming identity

See https://github.com/ShanghaitechGeekPie/oj-backend/issues/11 for background.

Location: `/user/<str:user_id>/instructor`

Supported method:

- `GET`: get the instructor associated with this user. The format is the same as what `/course/<str:course_id>/instructor/<str:user_id>` gives. It will return `null` with status code `404` when the user has not instructor associated with;
- `POST`: claim "I'm TA". Post the `enroll_email`(same as `email`) and `name` of this user into this interface will make the backend create a new instructor object in database for this user.

```json
{
    "uid": "2080083a-382c-11e9-ac7b-029eb86a7f02",
    "name": "Wei DaTa",
    "enroll_email": "huashuita@shanghaitech.edu.cn"
}
```

Location: `/user/<str:user_id>/student`

A similar API will also be provided as a fallback for students at `/user/<str:user_id>/student` in case the data from GAuth is faulty.

The format is the same as what `/course/<str:course_id>/students/<str:user_id>` gives.

```json
{
    "uid": "2080083a-382c-11e9-ac7b-029eb86a7f02",
    "name": "Wang Dachui",
    "enroll_email": "wangdch@shanghaitech.edu.cn",
    "nickname": "hammerWang"
}
```

The newly added student/instructor is linked with no existing courses.

### For student

#### Student's Basic Information

Supported method: `POST`, `GET`

* `POST`: motify one’s own identity;
* `GET`: retrive one’s own identity.

Registered at `/student/<str:uid>/` where id is the uid of the student in the database.

It will return the student's basic information, inluding `uid`, `name`, `email` and `student_id` in the following format.

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "name": "王大锤",
    "nickname": "hammerWang",
    "email": "wangdch@shanghaitech.edu.cn",
    "student_id": "19260817",
    "rsa_pub_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDwnExnO3zHIE16iR00SlZXSX468auyeGG7Vp2U5NRVdxXeeE1/Nn7HAWDzgB0Q8XNqcgkiobpBiCVvRO/H4tFi...."
}
```

#### Student's Courses List

Supported method: `GET`

Registered at `/student/<str:uid>/course/`.

It will return the courses in which the student with this `uid` enrolled in in the following format.

```json
[
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "name": "Introduction to Computer Science",
        "code": "SI 100C",
        "semaster": "Fall",
        "year": 2017,
        "homepage": "https://shtech.org/course/si100c/17f/",
        "instructor":["b3b17c00f16511e8b3dfdca9047a0f14", "b3b17c00f16511e8b3dfdca9047a0f14"]
    }
]
```

#### Student's submission history

This API is accessiable by instructor.

Supported method: `GET`

Registered at `/student/<str:student_id>/course/<str:course_id>/assignment/<str:assignment_id>/history/`.

It provides student's submission history under an assignment.

`state` describes status of records.

state    | integer
:-:|:-:
PLACEHOLD  |    0
PENDING   |    1
JUDGED    |    2
INVALID   |    3

```json
[
    {
        "state": 2,
        "commit_tag": "b3b17c00f16511e8b3dfdca9047a0f14",
        "message": "1. Accepted\n",
        "score": 10,
        "overall_score": 10,
        "submission_time": "2019-01-23 19:07:08",
        "delta": 0
    }
]
```

#### Student's submission history

This API is accessiable by instructor.

Supported method: `GET`

Registered at `/student/<str:student_id>/course/<str:course_id>/assignment/<str:assignment_id>/history/<str:commit_id>`.

It provides student's one specific submission under an assignment.

```json
    {
        "git_commit_id": "b3b17c00f16511e8b3dfdca9047a0f14",
        "course_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "message": "1. Accepted\n",
        "score": 10,
        "overall_score": 10,
        "submission_time": "2019-01-23 19:07:08",
        "delta": 0
    }
```

#### Student's Assignment Scoreboard

Supported method: `GET`

Registerd at `/student/<str:student_id>/course/<str:course_id>/assignment/<str:assignment_id>/scores/`

```json
[
    {
        "nickname": "hammerWang",
        "score": 10,
        "overall_score": 10,
        "submission_time": "2019-01-23 19:07:08",
        "delta": 0,
        "submission_count": 0
    }
]
```

### For Course

#### Course's Assignment List

Supported method: `GET`

Registered at `/student/<str:student_id>/course/<str:course_id>/assignment/`.

`overall_score` is the score the student get in his/she last commit.

```json
[
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "course_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "name": "Homework1: Postfix Calculator",
        "short_name": "hw1",
        "deadline":  "2019-01-23 19:07:08",
        "release_date": "2019-01-23 19:07:08",
        "descr_link": "https://shtech.org/course/si100c/17f/hw/1",
        "score": 3.14,
        "overall_score": 10.0
    }
]
```

#### Pending assignment list

Supported method: `GET`.

Registerd at `/course/<str:course_id>/assignment/<str:assignment_id>/queue`.

```json
[
    {
        "git_commit_id": "b3b17c00f16511e8b3dfdca9047a0f14",
        "course_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "submission_time": "2019-01-23 19:07:08",
        "submitter": "hammerWang"
    }
]

```

#### Intructor's basic information

Supported method: `GET`

Registered at `/course/<str:course_id>/instructor/<str:instr_email>/`

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "name": "Keyi Yuan",
    "email": "weidaxz@shanghaitech.edu.cn"
}
```


### For Instructor

NOTE: this part has not been fully implmented yet.

#### Instructor's Information

Supported method: `POST`, `GET`

- `POST`: motify one’s own identity;
- `GET`: retrive one’s own identity.

Registered at `/instructor/<str:uid>/` where id is the uid of the student in the database.

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "name": "王大锤",
    "email": "wangdch@shanghaitech.edu.cn",
    "rsa_pub_key": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDwnExnO3zHIE16iR00SlZXSX468auyeGG7Vp2U5NRVdxXeeE1/Nn7HAWDzgB0Q8XNqcgkiobpBiCVvRO/H4tFi...."
}
```

#### Instructor's Course list

Supported method: `POST`, `GET`

- `POST`: create a new course, with this user as one of the instructor;
- `GET`: retrive course list

Registered at `/instructor/<str:uid>/course/`.

```json
[
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "name": "Introduction to Computer Science",
        "code": "SI 100C",
        "semaster": "Fall",
        "year": 2017,
        "homepage": "https://shtech.org/course/si100c/17f/",
        "instructor":["weidaxz@shanghaitech.edu.cn", "huashuita@shanghaitech.edu.cn"]
    }
]
```


#### Course basic information

Supported method: `POST`, `GET`, `DELETE`

- `POST`: motify a course. Only the `name` and `homepage` filed are allowed to be changed;
- `GET`: retrive course’s information;
- `DELETE`: delete one course.

Registered at `/course/<str:uid>`.

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "name": "Introduction to Computer Science",
    "code": "SI 100C",
    "semaster": "Fall",
    "year": 2017,
    "homepage": "https://shtech.org/course/si100c/17f/",
    "instructor":["weidaxz@shanghaitech.edu.cn", "huashuita@shanghaitech.edu.cn"]
}
```

#### Course students list

Supported method: `POST`, `GET`

* `POST`: add a student to a course;
* `GET`: get the student list for the course.

Registered at `/course/<str:uid>/students/`.

```json
[
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "name": "王大锤",
        "enroll_email": "wangdch@shanghaitech.edu.cn",
        "student_id": "19260817",
    }
]
```
Caution: `name`, `student_id` and `uid` fileds may be omitted because we do not know those information before the user registered.

#### Course student

Supported method: `POST`, `GET`, `DELETE`

- <del>`POST`: add astudent to a course;</del>
- `GET`: get the student’s basic information if this student is in the course;
- `DELETE`: delete a student from a course, removing all his repo on the git server.

Registered at `/course/<str:uid>/students/<id:student_email>`.

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "name": "王大锤",
    "enroll_email": "wangdch@shanghaitech.edu.cn",
    "student_id": "19260817",
}
```
Caution: `name`, `student_id` and `uid` fileds may be omitted because we do not know those information before the user registered.

#### Course instrctors list

Supported method: `POST`, `GET`

- `POST`: add a instructor to a course;
- `GET`: get the student list for the course.

Registered at `/course/<str:course_id>/instructor/`

```json
[
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "name": "Keyi Yuan",
        "enroll_email": "weidaxz@shanghaitech.edu.cn"
    }
]
```
Caution: `name` and `uid` fileds may be omitted because we do not know those information before the user registered.

#### Course instructor

Supported method: `GET`, `POST`, `DELETE`

- <del>`POST`: add astudent to a course;</del>
- `GET`: get the student list for the course;
- `DELETE`: delete a student from a course, removing all his repo on the git server.

Registered at `/course/<str:course_id>/instructor/<str:instr_email>`

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "name": "Keyi Yuan",
    "enroll_email": "weidaxz@shanghaitech.edu.cn"
}
```
Caution: `name` and `uid` fileds may be omitted because we do not know those information before the user registered.

#### Course assignments list

Supported method: `GET`, `POST`

- `POST`: add an assignment to a course;
- `GET`: get the assignment list for the course.

Registered at `/course/<str:uid>/assignment/`

```json
[
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "course_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "name": "Homework1: Postfix Calculator",
        "short_name": "HW1",
        "deadline":  "2019-01-23 19:07:08",
        "release_date": "2019-01-23 19:07:08",
        "grade": 100,
        "descr_link": "https://shtech.org/course/si100c/17f/hw/1"
    }
]
```

When creating a new assignment, an additional field `ssh_url_to_repo` is added to the response indicating the repo to the grading script.

TODO: export all assignments.

#### Course assignment

Supported method: `GET`, `POST`, `DELETE`

- `POST`:  modify an assignment;
- `GET`: get the assignment infer;
- `DELETE`: delete an assignment from a course, removing all his repo on the git server.

Registered at `/course/<str:course_id>/assignment/<str:assignment_id>`

Please be notified: the `short_name` will be used in the path of the git repo and **SHALL ONLY** contain numbers, ANSI characters (excluding blank and control characters).

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "course_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "name": "Homework1: Postfix Calculator",
    "short_name": "HW1",
    "deadline":  "2019-01-23 19:07:08",
    "release_date": "2019-01-23 19:07:08",
    "grade": 100,
    "descr_link": "https://shtech.org/course/si100c/17f/hw/1"
}
```

#### Assignment Export script

Supported method: `GET`;

Get the script for downloading all student submission repos. See #25 for more details.

Registered at `/course/<str:course_id>/assignment/<str:assignment_id>/export`

```json
{
    "guidance": "<p>Desciption of how to use the script.</p>",
    "script": "#!/bin/sh\ngit clone git@oj.geekpie.club:/cs100-2019fall/hw0/wangdch.git"
}
```

#### Assignment Scoreboard

Supported method: `GET`

Registerd at `/course/<str:course_id>/assignment/<str:assignment_id>/scores/`

```json
[
    {
        "nickname": "hammerWang",
        "name": "王大锤",
        "student_id": "19260817",
        "score": 10,
        "overall_score": 10,
        "submission_time": "2019-01-23 19:07:08",
        "delta": 0,
        "submission_count": 0
    }
]
```

#### Course's default judges list

Supported method: `GET`, `POST`

Registered at `/course/<str:uid>/judge/`

```json
[
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    }
]
```

#### Course's default judge

Supported method: `GET`, `POST`, `DELETE`

Registered at `/course/<str:course_id>/judge/<str:judge_id>`

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
}
```

#### Assignment judges list

Supported method: `GET`, `POST`

* `GET`: get the judge’s `uid` list for the assignment
* `POST`: add an judge with the given `uid` to the judge list of this assignment.

Registered at `/course/<str:course_id>/assignment/<str:assignment_id>/judge/`

```json
[
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    }
]
```

#### Assignment's judge

Supported method: `GET`, `POST`, `DELETE`

* `DELETE`: remove an judge with the given `uid` to the judge list of this assignment.

Registered at `/course/<str:course_id>/assignment/<str:assignment_id>/judge/<str:judge_id>`

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
}
```

#### Judge List

Suppoerted method: `GET`, `POST`

- `GET`: get the judge list for this instructor.
- `POST`: add an new judge.

**NOTE**: This interface **WILL ONLY** return judge list for the login user/instructor. Throw a request to this interface and the interface below will result in a 404 response.

Registered at `/judge/`

```json
[
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "host": "10.19.171.56:443",
        "client_cert": "thisisthecert",
        "cert_ca": "thisisthecert",
        "client_key": "thisisthekey",
        "max_job": 4
    }
]
```

#### Judge

Supported method: `GET`, `POST`, `DELETE`

- `GET`: get the judge for this instructor with the given `uid`;
- `POST`: modify the given judge;
- `DELETE`: delete the given judge.

Registered at `/judge/<str:uid>`

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "host": "10.19.171.56:443",
    "client_cert": "thisisthecert",
    "cert_ca": "thisisthecert",
    "client_key": "thisisthekey",
    "max_job": 4
}
```

## Interface for internal communication

### Interface with `oj-middleware*`

Supported method: `POST`

Registered at `/internal/subbmission`.

Authorization: Using a token located in the http header `Authorization`. The token shall be specified in the envrionmental variable `OJ_SUBMISSION_TOKEN` (discussed in the “Deploy" section).

```json
{
    "assignment_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "course_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "upstream": "git@git.oj.geekpie.club/si100c-17f/hw1-diaozh.git",
    "additional_data": "this is additional data, put what you what."
}
```



## Lisence

```
Licensed under the Apache License, Version 2.0 (the "License"); you may
not use this file except in compliance with the License. You may obtain
a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.
```
