from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.datastructures import SortedDict
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson
from django.conf import settings

from disciplines.models import Discipline
from people.models import Researcher
from issues.models import Issue

def disciplines(request, template_name="disciplines/disciplines.html"):
    disciplines = Discipline.objects.all()
    
    search_terms = request.GET.get('search', '')
    if search_terms:
        disciplines = (disciplines.filter(name__icontains=search_terms) |
            disciplines.filter(description__icontains=search_terms))
    
    return render_to_response(template_name, {
        'disciplines': disciplines,
        'search_terms': search_terms,
    }, context_instance=RequestContext(request))

@login_required
def my_expertise(request):
    researcher = request.user.get_profile()
    expertise = researcher.expertise
    
    if expertise:
        return discipline(request, slug=expertise.slug)
    else:
        # researcher has no set expertise, make him choose one
        messages.add_message(request, messages.ERROR,
            _("Please set an expertise first.")
        )
        
        redirect_url = reverse('researcher_edit')
        return HttpResponseRedirect(redirect_url)
    
    return render_to_response(template_name, {
        "disciplines": disciplines,
    }, context_instance=RequestContext(request))

def discipline(request, slug=None, template_name="disciplines/discipline.html"):

    discipline = get_object_or_404(Discipline, slug=slug)
    
    researchers = Researcher.objects.filter(expertise=discipline)
    active_issues = Issue.objects.filter(disciplines=discipline, resolved=False)
    
    return render_to_response(template_name, {
        'discipline': discipline,
        'researchers': researchers,
        'active_issues': active_issues,
    }, context_instance=RequestContext(request))


