from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.conf import settings
from django.core.paginator import Paginator

from account.forms import SignupForm
from threadedcomments.models import ThreadedComment
from voting.models import Vote

from object_feeds.models import Feed, Update, Subscription
from people.models import Researcher
from issues.models import Issue

from threadedcomments.forms import RichCommentForm

def homepage(request):
    """ 
    What the user sees when they go to http://www.colabscience.com
    
    If they are not logged in, a sign-up form and tutorial.
    
    If they are logged in, a redirect to the user's HQ.
    
    """
    
    form = SignupForm()
    
    return direct_to_template(request, 'homepage.html',
        extra_context={'signup_form': form})

def tutorial(request):
    """
    Page containing only the getting started guide.
    
    """
    return direct_to_template(request, 'tutorial.html')

def dashboard(request, mine=True, username=None):
    """
    User's HQ is where the user can get updates on the things that interest them
    and manage their creations.
    
    Not the same as the user's profile.
    
    """
    is_me = False
    if mine:
        if request.user.is_authenticated():
            the_user = request.user
            is_me = True
        else:
            return HttpResponseRedirect(settings.LOGIN_URL+'?next=%s' % request.path)
    else:
        the_user = get_object_or_404(User, username=username)
        if the_user == request.user:
            is_me = True
    
    subscriptions = Subscription.objects.filter(user=the_user)
    feeds = [sub.feed for sub in subscriptions]
    updates = Update.objects.filter(feed__in=feeds).order_by('-created')
    
    # Paginate the list
    paginator = Paginator(updates, 20) # Show 20 updates per page
    
    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page is out of range, deliver last page of results.
    try:
        updates = paginator.page(page)
    except (EmptyPage, InvalidPage):
        updates = paginator.page(paginator.num_pages)
    
    return render_to_response('dashboard/dashboard.html', {
        'the_user': the_user,
        'is_me': is_me,
        'subscriptions': subscriptions,
        'feeds': feeds,
        'updates': updates,
        }, context_instance=RequestContext(request)
    )

def posts(request, mine=True, username=None):
    is_me = False
    if mine:
        the_user = request.user
        is_me = True
    else:
        the_user = get_object_or_404(User, username=username)
        if the_user == request.user:
            is_me = True
    
    the_researcher = request.user.get_profile()
    
    post_updates = Update.objects.filter(user=the_user)
    
    return render_to_response('dashboard/posts.html', {
        'the_user': the_user,
        'is_me': is_me,
        'post_updates': post_updates,
        }, context_instance=RequestContext(request)
    )

def votes(request, mine=True, username=None):
    is_me = False
    if mine:
        the_user = request.user
        is_me = True
    else:
        the_user = get_object_or_404(User, username=username)
        if the_user == request.user:
            is_me = True
    
    the_researcher = request.user.get_profile()
    
    votes = Vote.objects.filter(user=request.user)
    
    return render_to_response('dashboard/votes.html', {
        'the_user': the_user,
        'is_me': is_me,
        'votes': votes,
        }, context_instance=RequestContext(request)
    )
@login_required
def comment_edit(request, comment_id=None, template_name="dashboard/comment_edit.html"):
    comment = get_object_or_404(ThreadedComment, id=comment_id)
    
    comment_form = RichCommentForm(instance=comment, auto_id='comment_edit_%s')
    
    return render_to_response(template_name, {
        'comment': comment,
        'comment_form': comment_form,
    }, context_instance=RequestContext(request))

@login_required
def comment_reply(request, comment_id=None, template_name="dashboard/comment_reply.html"):
    comment = get_object_or_404(ThreadedComment, id=comment_id)
    
    comment_form = RichCommentForm(auto_id='comment_reply_%s')
    
    return render_to_response(template_name, {
        'comment': comment,
        'comment_form': comment_form,
    }, context_instance=RequestContext(request))
