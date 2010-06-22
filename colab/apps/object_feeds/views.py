from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from object_feeds.models import Feed, Subscription, Update
from object_feeds.forms import SubscriptionForm

def feed(request, feed_id=None, content_type=None, object_id=None, template_name='feeds/detail.html'):
    
    if feed_id: # feed_id takes priority (fastest)
        feed = get_object_or_404(Feed, pk=feed_id)
    elif content_type and object_id:
        object_type = get_object_or_404(ContentType, id=content_type)
        content_object = object_type.get_object_for_this_type(id=object_id)
    else:
        raise Http404
    
    return render_to_response(template_name, {
        'feed': feed,
        }, context_instance=RequestContext(request)
    )

def feeds(request, mine=True, username=None, template_name='feeds/feeds.html'):
    
    if mine:
        feeds = request.user.feeds
    else:
        the_user = get_object_or_404(User, username=username)
        feeds = the_user.feeds_set
    
    return render_to_response(template_name, {
        'feeds': feeds,
        }, context_instance=RequestContext(request)
    )

@login_required
def subscription(request, feed_id=None, content_type=None, object_id=None, template_name='feeds/subscription.html'):
    
    if feed_id: # feed_id takes priority (fastest)
        feed = get_object_or_404(Feed, pk=feed_id)
    elif content_type and object_id:
        object_type = get_object_or_404(ContentType, id=content_type)
        content_object = object_type.get_object_for_this_type(id=object_id)
        feed = content_object.feed
    else:
        raise Http404
    
    subscription = None
    actions = None
    try:
        subscription = Subscription.objects.get(feed=feed, user=request.user)
        actions = subscription.actions
        following = True
    except Subscription.DoesNotExist:
        following = False
    
    subscription_form = SubscriptionForm(
        {'feed': feed.id, 'user': request.user.id, 'actions': actions},
        feed=feed, user=request.user, actions=actions)
    
    # figure out which form was submitted
    unfollow_form = request.POST.get('unfollow', False)
    follow_form = request.POST.get('follow', False)
    if unfollow_form and following:
        subscription.delete()
        return HttpResponseRedirect(feed.feed_object.get_absolute_url())
        
    if follow_form and subscription_form.is_valid():
        subscription = subscription_form.save()
        
        user_message = u"Your subscription was updated."
        request.user.message_set.create(message=user_message)
        
        return HttpResponseRedirect(feed.feed_object.get_absolute_url())
    else:
        print "Errors: %s %s" % (str(subscription_form.is_bound), subscription_form.errors)
    
    return render_to_response(template_name, {
        'feed': feed,
        'subscription_form': subscription_form,
        'following': following,
        'subscription': subscription,
        }, context_instance=RequestContext(request)
    )

