from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.models import User
from django.utils import simplejson
from django.contrib import messages
from django.utils.translation import ugettext, ugettext_lazy as _
from django.core.urlresolvers import reverse

from threadedcomments.models import ThreadedComment
from threadedcomments.forms import RichCommentForm

from feedback.models import Feedback
from feedback.forms import FeedbackForm, WidgetForm
from papers.models import Paper

def list(request, list="open", type="all", status="all", mine=False, template_name="feedback/list.html"):
    feedbacks = Feedback.objects.all().order_by('-created')
    
    if mine:
      feedbacks = feedbacks.filter(user=request.user)
      list_title = "My Feedback"
    
    if list == "all":
        list_title = "All Feedback"
    elif list == "open":
        list_title = "Open Feedback"
        feedbacks = feedbacks.filter(status__status='open')
    elif list == "closed":
        list_title = "Closed Feedback"
        feedbacks = feedbacks.filter(status__status='closed')
    elif list == "mine":
        list_title = "My Feedback"
        feedbacks = feedbacks.filter(user=request.user)
    
    if type != "all":
        feedbacks = feedbacks.filter(type__slug=type)
    
    if status != "all":
        feedbacks = feedbacks.filter(status__slug=status)
    
    if not request.user.is_staff:
        feedbacks = feedbacks.filter(private=False)
    
    return render_to_response(template_name, {
        'feedbacks': feedbacks, 'list': list, 'status': status, 'type': type,
        'list_title': list_title,
        }, context_instance=RequestContext(request))

def detail(request, object_id, template_name="feedback/detail.html"):
    feedback = get_object_or_404(Feedback, pk=object_id)
    
    if feedback.private == True:
        if not request.user.is_staff and request.user != feedback.user:
            raise Http404
    
    comment_form = RichCommentForm(auto_id='new_comment_form_%s')
    
    return render_to_response(template_name, {
        'feedback': feedback,
        'comment_form': comment_form,
        }, context_instance=RequestContext(request))

def submit(request, form_class=FeedbackForm, template_name="feedback/submit.html"):
    form = form_class(request.POST or None)
    
    if form.is_valid():
        feedback = form.save(commit=False)
        if request.user.is_authenticated:
            feedback.user = request.user
        feedback.save()
        
        feedback.register_action(request.user, 'create', feedback)
        
        return HttpResponseRedirect(feedback.get_absolute_url())
    
    return render_to_response(template_name, {
        "form": form,
    }, context_instance=RequestContext(request))

@login_required
def edit(request, object_id=None, form_class=FeedbackForm, template_name="feedback/edit.html"):
    feedback = Feedback.objects.get(id=object_id)
    
    if feedback.user != request.user and not request.user.is_staff:
        return render_to_response('feedback/forbidden.html', {}, context_instance=RequestContext(request))
    
    form = form_class(request.POST or None, instance=feedback)
    
    if form.is_valid():
        feedback = form.save()
        
        feedback.register_action(request.user, 'edit', feedback)
        
        return HttpResponseRedirect(feedback.get_absolute_url())
    
    return render_to_response(template_name, {
        'feedback': feedback,
        'form': form,
    }, context_instance=RequestContext(request))

@login_required
def delete(request, object_id=None, template_name="feedback/delete.html"):
    feedback = Feedback.objects.get(id=object_id)
    redirect_url = feedback.get_absolute_url()
    
    if request.user == feedback.user:
        if not Paper.objects.get_for_object(feedback).exists():
            if not ThreadedComment.objects.get_for_object(feedback).exists():
                feedback.feed.delete()
                feedback.delete()
                messages.add_message(request, messages.SUCCESS,
                    _("Feedback %s deleted.") % feedback.title
                )
                redirect_url = reverse("feedback_list")
            else:
                messages.add_message(request, messages.ERROR,
                    _("Please delete comments before deleting the feedback.")
                )
        else:
            messages.add_message(request, messages.SUCCESS,
                _("Please delete papers before deleting the feedback.")
            )
    else:
        messages.add_message(request, messages.SUCCESS,
            _("You are not the creator of this feedback.")
        )
    
    return HttpResponseRedirect(redirect_url)

def widget(request, form_class=WidgetForm, template_name="feedback/widget.html"):
    form = form_class(request.POST or None)
    
    if form.is_valid():
        feedback = form.save(commit=False)
        if not form.cleaned_data['anonymous']:
            feedback.creator = u
        feedback.save()
        
        feedback.register_action(request.user, 'create', feedback)
        
        data = simplejson.dumps({'url':feedback.get_absolute_url(), 'errors': False})
    else:
        data = simplejson.dumps({'errors': True})
    
    return HttpResponse(data, mimetype='application/json')

def leave_feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save()
            
            if feedback.user:
                request.user.message_set.create(message="Your feedback has been saved successfully.")
            return HttpResponseRedirect(request.POST.get('next', request.META.get('HTTP_REFERER', '/')))
    else:
        form = FeedbackForm(request.GET)
    return render_to_response('feedback/feedback_form.html', {'form': form}, context_instance=RequestContext(request))
