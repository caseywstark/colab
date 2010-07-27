# -*- coding: utf-8 -*-
# Django settings for social pinax project.

import os.path
import posixpath
import pinax

PINAX_ROOT = os.path.abspath(os.path.dirname(pinax.__file__))
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# tells Pinax to use the default theme
PINAX_THEME = "default"

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# tells Pinax to serve media through the staticfiles app.
SERVE_MEDIA = DEBUG

INTERNAL_IPS = [
    "127.0.0.1",
]

ADMINS = [
    ("Casey Stark", "casey@thisiscolab.com"),
]

MANAGERS = ADMINS

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3", # Add "postgresql_psycopg2", "postgresql", "mysql", "sqlite3" or "oracle".
        "NAME": "dev.db",                       # Or path to database file if using sqlite3.
        "USER": "dev.db",                             # Not used with sqlite3.
        "PASSWORD": "",                         # Not used with sqlite3.
        "HOST": "",                             # Set to empty string for localhost. Not used with sqlite3.
        "PORT": "",                             # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# although not all variations may be possible on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = "US/Pacific"

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = "en"

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, "site_media", "media")

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = "/site_media/media/"

# Absolute path to the directory that holds static files like app media.
# Example: "/home/media/media.lawrence.com/apps/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, "site_media", "static")

# URL that handles the static files like app media.
# Example: "http://media.lawrence.com"
STATIC_URL = "/site_media/static/"

# Additional directories which hold static files
STATICFILES_DIRS = [
    os.path.join(PROJECT_ROOT, "media"),
    os.path.join(PINAX_ROOT, "media", PINAX_THEME),
]

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = posixpath.join(STATIC_URL, "admin/")

# Make this unique, and don"t share it with anybody.
SECRET_KEY = "*vrox!me3x6nk0%pe^*njyi0lwbzw-bd_t@ddjw4cu=rtvqm(1"

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = [
    "django.template.loaders.filesystem.load_template_source",
    "django.template.loaders.app_directories.load_template_source",
]

MIDDLEWARE_CLASSES = [
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_openid.consumer.SessionConsumer",
    "django.contrib.messages.middleware.MessageMiddleware",
    "account.middleware.LocaleMiddleware",
    "django.middleware.doc.XViewMiddleware",
    "pagination.middleware.PaginationMiddleware",
    "django_sorting.middleware.SortingMiddleware",
    "pinax.middleware.security.HideSensistiveFieldsMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.transaction.TransactionMiddleware",
]

ROOT_URLCONF = "colab.urls"

TEMPLATE_DIRS = [
    os.path.join(PROJECT_ROOT, "templates"),
    os.path.join(PINAX_ROOT, "templates", PINAX_THEME),
]

TEMPLATE_CONTEXT_PROCESSORS = [
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages",
    
    "pinax.core.context_processors.pinax_settings",
    
    #"notification.context_processors.notification",
    "announcements.context_processors.site_wide_announcements",
    "account.context_processors.openid",
    "account.context_processors.account",
    "messages.context_processors.inbox",
    #"friends_app.context_processors.invitations",
    "colab.context_processors.combined_inbox_count",
    "feedback.context_processors.widget_feedback_form",
]

COMBINED_INBOX_COUNT_SOURCES = [
    "messages.context_processors.inbox",
    #"friends_app.context_processors.invitations",
    #"notification.context_processors.notification",
]

INSTALLED_APPS = [
    # included
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.humanize",
    "django.contrib.markup",
    "pinax.templatetags",
    
    # external
    "notification", # must be first
    "django_openid",
    "emailconfirmation",
    "django_extensions",
    "mailer",
    "messages",
    "announcements",
    "oembed",
    "pagination",
    "groups",
    "threadedcomments",
    "threadedcomments_extras",
    "timezones",
    "voting",
    "voting_extras",
    "tagging",
    "bookmarks",
    "ajax_validation",
    "avatar",
    "flag",
    "uni_form",
    "django_sorting",
    "django_markup",
    "staticfiles",
    "debug_toolbar",
    
    # internal (for now)
    "analytics",
    "account",
    "signup_codes",
    
    # extra
    "django.contrib.comments",
    "mptt",
    "django_filters",
    "ajax_select",
    "tinymce",
    "oauth_access",
    "biblion",
    
    # custom
    "about",
    "object_feeds",
    "disciplines",
    "people",
    "issues",
    "papers",
    "dashboard",
    "feedback",
    
]

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

ABSOLUTE_URL_OVERRIDES = {
    "auth.user": lambda o: "/researchers/profile/%s/" % o.username,
}
ACCOUNT_USER_DISPLAY = lambda user: user.get_profile().name

MARKUP_FILTER_FALLBACK = "none"
MARKUP_CHOICES = [
    ("restructuredtext", u"reStructuredText"),
    ("textile", u"Textile"),
    ("markdown", u"Markdown"),
    ("creole", u"Creole"),
]

AUTH_PROFILE_MODULE = "people.Researcher"
NOTIFICATION_LANGUAGE_MODULE = "account.Account"

ACCOUNT_OPEN_SIGNUP = True
ACCOUNT_REQUIRED_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = False
ACCOUNT_EMAIL_AUTHENTICATION = True
ACCOUNT_UNIQUE_EMAIL = EMAIL_CONFIRMATION_UNIQUE_EMAIL = True

if ACCOUNT_EMAIL_AUTHENTICATION:
    AUTHENTICATION_BACKENDS = [
        "account.auth_backends.EmailModelBackend",
    ]
else:
    AUTHENTICATION_BACKENDS = [
        "django.contrib.auth.backends.ModelBackend",
    ]

EMAIL_CONFIRMATION_DAYS = 2
EMAIL_DEBUG = DEBUG
CONTACT_EMAIL = "casey@thisiscolab.com"
SITE_NAME = "CoLab"
LOGIN_URL = "/account/login/"
LOGIN_REDIRECT_URLNAME = "what_next"

ugettext = lambda s: s
LANGUAGES = [
    ("en", u"English"),
]

# URCHIN_ID = "ua-..."

YAHOO_MAPS_API_KEY = "..."

class NullStream(object):
    def write(*args, **kwargs):
        pass
    writeline = write
    writelines = write

RESTRUCTUREDTEXT_FILTER_SETTINGS = {
    "cloak_email_addresses": True,
    "file_insertion_enabled": False,
    "raw_enabled": False,
    "warning_stream": NullStream(),
    "strip_comments": True,
}

# if Django is running behind a proxy, we need to do things like use
# HTTP_X_FORWARDED_FOR instead of REMOTE_ADDR. This setting is used
# to inform apps of this fact
BEHIND_PROXY = False

FORCE_LOWERCASE_TAGS = True

# Uncomment this line after signing up for a Yahoo Maps API key at the
# following URL: https://developer.yahoo.com/wsregapp/
# YAHOO_MAPS_API_KEY = ""

DEBUG_TOOLBAR_CONFIG = {
    "INTERCEPT_REDIRECTS": False,
}

AJAX_LOOKUP_CHANNELS = {
    'discipline' : dict(model='disciplines.Discipline', search_field='name'),
    'researcher': dict(model='people.Researcher', search_field='name'),
    'institution' : dict(model='people.Institution', search_field='name'),
}

TINYMCE_JS_URL = STATIC_URL + "tiny_mce/tiny_mce.js"
TINYMCE_JS_ROOT = STATIC_URL + "tiny_mce"
TINYMCE_DEFAULT_CONFIG = {
    'theme': "advanced",
    'cleanup_on_startup': True,
    #'skin': "o2k7",
    #'skin_variant': "black",
    'plugins': "safari, spellchecker, table, advimage, advlink, iespell, inlinepopups, insertdatetime, preview, media, searchreplace, contextmenu, paste, directionality, fullscreen, noneditable, nonbreaking, xhtmlxtras, template",
    'theme_advanced_buttons1': "bold, italic, underline, strikethrough, |, bullist, numlist, outdent, indent, blockquote, |, link, unlink,",
    'theme_advanced_buttons2': "cut, copy, paste, pastetext, pasteword, |, search, replace, |, undo, redo, |, anchor, image, cleanup, help, |, insertdate, inserttime, preview,",
    'theme_advanced_buttons3': "tablecontrols, |, removeformat, visualaid, |, sub, sup, |, charmap, iespell, media, |, fullscreen",
    'theme_advanced_buttons4': "styleprops, spellchecker, |, cite, abbr, acronym, del, ins, attribs,",
    'theme_advanced_toolbar_location': "top",
    'theme_advanced_toolbar_align': "center",
    'theme_advanced_statusbar_location': "bottom",
    'theme_advanced_resizing': True,
}

# valid OAuth options
OAUTH_ACCESS_SETTINGS = {
    'facebook': {
        'request_token_url': "https://facebook.com/oauth/request_token",
    },
    'twitter': {
        'keys': {
            'KEY': 'key',
            'SECRET': '',
        },
        'endpoints': {
            'request_token': 'https://twitter.com/oauth/request_token',
            'access_token': 'https://twitter.com/oauth/access_token',
            'user_auth': 'http://twitter.com/oauth/authorize',
        },
    },
}

BIBLION_SECTIONS = [
    ['dear-scientists', 'Dear Scientists'],
    ['features', 'Features'],
]

# No credentials for you
try:
    from development import *
except ImportError:
    pass

try:
    from staging import *
except ImportError:
    pass
    
try:
    from production import *
except ImportError:
    pass
