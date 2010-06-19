from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from avatar.templatetags.avatar_tags import avatar
from friends.forms import InviteFriendForm
from friends.models import FriendshipInvitation, Friendship
from microblogging.models import Following

if "notification" in settings.INSTALLED_APPS:
    from notification import models as notification
else:
    notification = None

from people.forms import ResearcherForm
from people.models import Researcher

def researchers(request, template_name="people/researchers.html"):
    researchers = Researcher.objects.all().order_by("-user__date_joined")
    
    search_terms = request.GET.get('search', '')
    if search_terms:
        researchers = researchers.filter(name__icontains=search_terms)
    
    sort = request.GET.get("sort", "date")
    direction = request.GET.get("dir", "desc")
    if sort == "date":
        if direction == "asc":
            researchers = researchers.order_by("user__date_joined")
        else:
            researchers = researchers.order_by("-user__date_joined")
    elif sort == "name":
        if direction == "asc":
            researchers = researchers.order_by("name")
        else:
            researchers = researchers.order_by("-name")
        
    return render_to_response(template_name, {
        "researchers": researchers,
        "search_terms": search_terms,
        "sort": sort,
    }, context_instance=RequestContext(request))


def researcher(request, username=None, myself=False, template_name="people/researcher.html", extra_context=None):
    
    is_me = False
    if myself:
        the_user = request.user
        is_me = True
    else:
        the_user = get_object_or_404(User, username=username)
        
        if request.user == the_user:
            is_me = True
    
    researcher = the_user.get_profile()
    
    return render_to_response(template_name, {
        "is_me": is_me,
        "the_user": the_user,
        "researcher": researcher,
    }, context_instance=RequestContext(request))


@login_required
def researcher_edit(request, form_class=ResearcherForm, **kwargs):
    
    template_name = kwargs.get("template_name", "people/researcher_edit.html")
    
    if request.is_ajax():
        template_name = kwargs.get(
            "template_name_facebox",
            "people/researcher_edit_facebox.html"
        )
    
    researcher = request.user.get_profile()
    
    if request.method == "POST":
        researcher_form = form_class(request.POST, instance=researcher)
        if researcher_form.is_valid():
            researcher = researcher_form.save(commit=False)
            researcher.user = request.user
            researcher.save()
            messages.add_message(request, messages.SUCCESS, ugettext("Your profile has been updated."))
            return HttpResponseRedirect(reverse("researcher_detail", args=[request.user.username]))
    else:
        researcher_form = form_class(instance=researcher)
    
    return render_to_response(template_name, {
        "researcher": researcher,
        'the_user': researcher.user,
        "researcher_form": researcher_form,
    }, context_instance=RequestContext(request))
