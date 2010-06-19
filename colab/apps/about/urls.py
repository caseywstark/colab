from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns("",
    url(r"^$", direct_to_template, {"template": "about/about.html"}, name="about"),
    url(r'^faq/$', direct_to_template, {"template": "about/faq.html"}, name="faq"),
    url(r'^contact/$', direct_to_template, {"template": "about/contact.html"}, name="contact"),
    url(r'^contribute/$', direct_to_template, {"template": "about/contribute.html"}, name="contribute"),
    
    url(r"^terms/$", direct_to_template, {"template": "about/terms.html"}, name="terms"),
    url(r"^privacy/$", direct_to_template, {"template": "about/privacy.html"}, name="privacy"),
    url(r"^dmca/$", direct_to_template, {"template": "about/dmca.html"}, name="dmca"),
    
    url(r"^what_next/$", direct_to_template, {"template": "about/what_next.html"}, name="what_next"),
)
