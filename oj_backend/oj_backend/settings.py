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

"""
Django settings for oj_backend project.

Generated by 'django-admin startproject' using Django 2.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/2.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.1/ref/settings/
"""

import os
import redis
from django.urls import reverse

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
        'djangodjango.request': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
        'djangodjango.server': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
        'backend.main': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
        },
    },
}

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# Deployment settings:
if os.environ.get('OJBN_STAGE', 'production').lower() == 'development':
    SECRET_KEY = 'mq-2-_&%i3ne(f=wwhfoc)hw5fvr)=+9elezs&cs!k+1^y^sf='
    DEBUG = True
else:
    SECRET_KEY = os.environ['OJBN_SECRET_KEY']
    DEBUG = False

ALLOWED_HOSTS = [os.environ['OJBN_HOSTNAME']]
OJBN_INTERNAL_HOSTNAME = os.environ.get('OJBN_INTERNAL_HOSTNAME')
if OJBN_INTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(OJBN_INTERNAL_HOSTNAME)

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'oidc_rp',
    'rest_framework',
    'corsheaders',
    'oj_database',
    'oj_backend.backend'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'oidc_rp.middleware.OIDCRefreshIDTokenMiddleware',
]

ROOT_URLCONF = 'oj_backend.urls'
CORS_ORIGIN_ALLOW_ALL = True

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'oidc_rp.context_processors.oidc',
            ],
        },
    },
]

WSGI_APPLICATION = 'oj_backend.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ['OJBN_DB_NAME'],
        'USER': os.environ['OJBN_DB_USER'],
        'PASSWORD': os.environ['OJBN_DB_PASSWD'],
        'HOST': os.environ['OJBN_DB_HOST'],
        'PORT': '3306',
    }
}


CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ['OJBN_REDIS_ADDR'],
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

redisConnectionPool = redis.ConnectionPool(
    connection_class=redis.Connection, max_connections=100, host=os.environ['OJBN_REDIS_HOST'], port=int(os.environ['OJBN_REDIS_PORT']), db=int(os.environ['OJBN_REDIS_DB']))


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

AUTHENTICATION_BACKENDS = (
    'oidc_rp.backends.OIDCAuthBackend',
)

AUTH_USER_MODEL = 'oj_database.User'

OIDC_RP_SIGN_ALGO = 'HS256'
OIDC_RP_CLIENT_ID = os.environ['OIDC_RP_CLIENT_ID']
OIDC_RP_CLIENT_SECRET = os.environ['OIDC_RP_CLIENT_SECRET']
OIDC_RP_SCOPES = "openid profile email identification identification_shanghaitech_realname identification_shanghaitech_id identification_shanghaitech_role"
OIDC_RP_PROVIDER_ENDPOINT = os.environ['OIDC_RP_PROVIDER_ENDPOINT']
OIDC_RP_USER_DETAILS_HANDLER = 'oj_backend.backend.users.oidc_user_update_handler'
OIDC_EXEMPT_URLS = ["/api/user/login/oauth/param", "/api/user/auth/oidc/param"]
LOGIN_REDIRECT_URL = "https://oj.geekpie.club/"
LOGOUT_REDIRECT_URL = "https://oj.geekpie.club/"

OJ_SUBMISSION_TOKEN = os.environ['OJ_SUBMISSION_TOKEN']

OJ_ENFORCE_HTTPS = True
#SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = 'zh-cn'

TIME_ZONE = 'Etc/UCT'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/

STATIC_URL = '/static/'

# override the auth mode.
