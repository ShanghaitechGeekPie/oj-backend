# GeekPie OJ Project: Backend Part

**⚠️ 建设中**

This part provides a RESTful API of user management, course/assignment details for the GeekPie OJ Project. This project is devleloped using `Python 3.7`, ` Django 2.1.3` and also the latest version of `Django RESTful Framework` directly cloned from GitHub.

## Deploy

This project use `MySQL` as its database. Before installing, make sure you has an accessiable `MySQL` server. Also, this project is designed to work with other micro-service to provide a git-based online programming homework grading system.

Deploying using `Docker` is recommended. Make sure you set the following environment variables correctly before staring the service.


environment variable | description | example
---|---|---|
`OJBN_DB_HOST` | the host where the database is hosted. | `localhost`
`OJBN_DB_NAME` | the database name. | `ojdb`
`OJBN_DB_USER` | the user used to acssess the database. | `geekpie`
`OJBN_DB_PASSWD` | the database password for the given user. | `gouliguojiashengsiyi`
`OJBN_HOSTNAME` | the `host` header allowed in a HTTP request. | `oj.geekpie.club`
`OJBN_GITLAB_ADDR` | the address where the gitlab middleware is hosted. | `localhost:8080`
`OJBN_OAUTH_URL` | the URL of the OAuth service this service is using | `https://gauth.geekpie.club/oauth/login`
`OJBN_REDIS_ADDR` | the address of redis server. Follows the schema of `redis-py` | `redis://[:password]@localhost:6379/0`
`OJ_SUBMISSION_TOKEN` | token for auth betwwen `oj-*-middleware` and `oj-backend` for submission | `woshitoken` |
`OIDC_RP_CLIENT_ID` | OpenID client ID | |
`OIDC_RP_CLIENT_SECRET` | OpenID client secret | |
`OIDC_OP_AUTHORIZATION_ENDPOINT` |  | |
`OIDC_OP_TOKEN_ENDPOINT` |  | |
`OIDC_OP_USER_ENDPOINT`  |  | |


## API Schema

### For all users

#### User Login/Logout

Registered at `/oidc/callback/`. Users are required to login in order to access any API.


#### Login parameters

Supported method: `GET`

Registered at `/user/login/oauth/param`

```json
{
    "login_url": "https://gauth.geekpie.club/oauth/login",
}
```

In this example, frontend shall redirect user to `https://gauth.geekpie.club/oauth/login`.

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

### For student

#### Student's Basic Information

Supported method: `POST`, `GET`

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

```json
[
    {
        "git_commit_id": "b3b17c00f16511e8b3dfdca9047a0f14",
        "course_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "message": "1. Accepted\n",
        "score": 10,
        "overall_score": 10,
        "submission_time": 1548241628,
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
        "submission_time": 1548241628,
        "delta": 0
    }
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
        "deadline":  1548241628,
        "release_date": 1548241628,
        "descr_link": "https://shtech.org/course/si100c/17f/hw/1",
        "score": 3.14,
        "overall_score": 10.0
    }
]
```

#### Assignment Detail

Supported method: `GET`

Registered at `/course/<str:course_id>/assignment/<str:assignment_id>/`

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "course_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "name": "Homework1: Postfix Calculator",
    "deadline":  1548241628,
    "release_date": 1548241628,
    "descr_link": "https://shtech.org/course/si100c/17f/hw/1",
    "score": 3.14,
    "overall_score": 10.0
}
```

#### Assignment Scoreboard

Supported method: `GET`

Registerd at `/course/<str:course_id>/assignment/<str:assignment_id>/scores/`

```json
[
    {
        "nickname": "hammerWang",
        "score": 10,
        "overall_score": 10,
        "submission_time": 1548241628,
        "delta": 0
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
        "submission_time": 1548241628,
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
        "instructor":["b3b17c00f16511e8b3dfdca9047a0f14", "b3b17c00f16511e8b3dfdca9047a0f14"]
    }
]
```


#### Course basic information

Supported method: `POST`, `GET`, `DELETE`

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

Registered at `/course/<str:uid>/assignment/`

```json
[
    {
        "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "course_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
        "name": "Homework1: Postfix Calculator",
        "short_name": "HW1",
        "deadline":  1548241628,
        "release_date": 1548241628,
        "descr_link": "https://shtech.org/course/si100c/17f/hw/1"
    }
]
```

When creating a new assignment, an additional field `ssh_url_to_repo` is added to the response indicating the repo to the grading script.

TODO: export all assignments.

#### Course assignment

Supported method: `GET`, `POST`, `DELETE`

Registered at `/course/<str:course_id>/assignment/<str:assignment_id>`

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "course_uid": "b3b17c00f16511e8b3dfdca9047a0f14",
    "name": "Homework1: Postfix Calculator",
    "short_name": "HW1",
    "deadline":  1548241628,
    "release_date": 1548241628,
    "descr_link": "https://shtech.org/course/si100c/17f/hw/1"
}
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

Registered at `/course/<str:course_id>/assignment/<str:assignment_id>/judge/<str:judge_id>`

```json
{
    "uid": "b3b17c00f16511e8b3dfdca9047a0f14",
}
```

#### Judge List

Suppoerted method: `GET`, `POST`

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

Authorization: TBD

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
