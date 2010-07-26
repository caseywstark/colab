from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from django.core.paginator import Paginator

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

from disciplines.models import Discipline
from tagging.models import Tag, TaggedItem

def researchers(request, template_name="people/researchers.html"):
    researchers = Researcher.objects.all().order_by("-user__date_joined")
    
    search_terms = request.GET.get('search', '')
    if search_terms:
        researchers = researchers.filter(name__icontains=search_terms)
    
    # Additional filtering
    discipline = request.GET.get('discipline', None)
    the_discipline = None
    tag = request.GET.get('tag', None)
    the_tag = None
    if discipline:
        try:
            the_discipline = Discipline.objects.get(slug=discipline) # make sure the discpline exists
            researchers = researchers.filter(expertise=the_discipline)
        except Discipline.DoesNotExist:
            messages.add_message(request, messages.ERROR, _("That discipline does not exist."))
    if tag:
        try:
            the_tag = Tag.objects.get(id=tag) # make sure the tag exists
            researchers = TaggedItem.objects.get_by_model(researchers, the_tag)
        except Tag.DoesNotExist:
            messages.add_message(request, messages.ERROR, _("That tag does not exist."))
    
    # get filter querysets
    if the_discipline:
        discipline_filters = the_discipline.get_children()
    else:
        discipline_filters = Discipline.tree.root_nodes()
    if the_tag:
        tag_filters = Tag.objects.related_for_model(the_tag, Researcher)
    else:
        tag_filters = Tag.objects.usage_for_model(Researcher)
    
    # Figure out sorting to replace the title
    list_title = 'Researchers'
    
    sort = request.GET.get('sort', 'date')
    direction = request.GET.get('dir', 'desc')
    
    if sort == 'date':
        if direction == "asc":
            researchers = researchers.order_by("user__date_joined")
            list_title = "Oldest Researchers"
        else:
            researchers = researchers.order_by("-user__date_joined")
            list_title = "Newest Researchers"
    if sort == 'name':
        if direction == "asc":
            researchers = researchers.order_by("name")
            list_title = "Researchers (A to Z)"
        else:
            researchers = researchers.order_by("-name")
            list_title = "Researchers (Z to A)"
    if sort == 'contributions':
        if direction == "asc":
            researchers = researchers.order_by("contributions")
            list_title = "Least Active Researchers"
        else:
            researchers = researchers.order_by("-contributions")
            list_title = "Most Active Researchers"
    
    # Paginate the list
    paginator = Paginator(researchers, 20) # Show 20 researchers per page
    
    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page is out of range, deliver last page of results.
    try:
        researchers = paginator.page(page)
    except (EmptyPage, InvalidPage):
        researchers = paginator.page(paginator.num_pages)    
    
    return render_to_response(template_name, {
        "researchers": researchers,
        "search_terms": search_terms,'the_discipline': the_discipline,
        'discipline_filters': discipline_filters, 'tag_filters': tag_filters,
        'sort': sort, 'direction': direction,
        'list_title': list_title,
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
