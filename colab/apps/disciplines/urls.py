from django.conf.urls.defaults import *

from disciplines.models import Discipline

urlpatterns = patterns('disciplines.views',
    url(r'^$', 'disciplines', name='discipline_list'),
    url(r'^my_expertise/$', 'my_expertise', name="my_expertise"),
    url(r'^discipline/(?P<slug>[-\w]+)/$', 'discipline', name="discipline_detail"),
)
