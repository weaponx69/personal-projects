"""
Django settings for ai_rater_project project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 1. BASE DIRECTORY
BASE_DIR = Path(__file__).resolve().parent.parent

# 2. LOAD ENVIRONMENT VARIABLES
# This will look for the .env file in the same directory as manage.py
load_dotenv(BASE_DIR / '.env')

# 3. CORE SECURITY SETTINGS
# Pulling from .env with fallbacks for safety
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-default-key-change-this-in-env')

# Note: os.getenv returns a string, so we compare it to 'True'
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# Split by comma to allow multiple hosts in .env: ALLOWED_HOSTS=localhost,127.0.0.1
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# 4. APPLICATION DEFINITION
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rater',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ai_rater_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'], # Added to allow global templates
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'ai_rater_project.wsgi.application'


# 5. DATABASE
# We're using SQLite as it's great for development and learning relationships
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# 6. PASSWORD VALIDATION
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# 7. INTERNATIONALIZATION
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# 8. STATIC FILES
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']


# 9. DEFAULT PRIMARY KEY FIELD TYPE
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# 10. PERPLEXITY API INTEGRATION
# This is where your custom automation key is stored
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")