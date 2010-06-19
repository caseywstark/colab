from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponseNotAllowed, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic.simple import redirect_to
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages

from summaries.models import Summary, SummaryRevision
from summaries.forms import SummaryForm
from threadedcomments.forms import RichCommentForm

@login_required
def create(request, content_type=None, object_id=None, form_class=SummaryForm, template_name="summaries/create.html"):

    # Get the parent object if passed one
    if content_type and object_id:
        object_type = get_object_or_404(ContentType, id=content_type)
        content_object = object_type.get_object_for_this_type(id=object_id)
    else:
        content_object = none
    
    form = form_class(request.POST or None)
    
    if form.is_valid():
        form.editor = request.user
        form.content_object = content_object

        summary, revision = form.save()
        
        summary.register_action(request.user, 'create', revision)
        
        if hasattr(summary.content_object, 'feed'):
            summary.content_object.register_action(request.user, 'add summary', summary)
        
        user_message = u"Your summary was created successfully."
        request.user.message_set.create(message=user_message)
        
        return HttpResponseRedirect(summary.get_absolute_url())

    form = form_class(request.POST or None, summary_type=summary_type)
    
    return render_to_response(template_name, {
        'content_object': content_object,
        'summary_form': form,
        'summary_type': summary_type,
    }, context_instance=RequestContext(request))

@login_required
def edit(request, summary_id=None, form_class=SummaryForm, template_name='summaries/edit.html'):
    
    summary = get_object_or_404(Summary, id=summary_id)

    form = form_class(request.POST or None, instance=summary)

    if form.is_valid():
        form.editor = request.user
        summary, revision = form.save()
        
        summary.register_action(request.user, 'edit', revision)
        
        user_message = u"Your summary was edited successfully."
        request.user.message_set.create(message=user_message)
        
        return HttpResponseRedirect(summary.get_absolute_url())

    return render_to_response(template_name, {
        'summary': summary,
        'summary_form': form,
    }, context_instance=RequestContext(request))

@login_required
def delete(request, summary_id=None, template_name='summaries/delete.html'):
    
    summary = get_object_or_404(Summary, id=summary_id)

    redirect_url = summary.get_absolute_url()
    
    if request.user == summary.creator:
        if not ThreadedComment.objects.all_for_object(summary).exists():
            summary.feed.delete()
            summary.delete()
            messages.add_message(request, messages.SUCCESS,
                _("Summary %s deleted.") % summary.title
            )
            redirect_url = summary.content_object.get_absolute_url()
        else:
            messages.add_message(request, messages.ERROR,
                _("Please delete comments before deleting the summary.")
            )
    else:
        messages.add_message(request, messages.SUCCESS,
            _("You are not the creator of this summary.")
        )
    
    return HttpResponseRedirect(redirect_url)


def summary(request, summary_id=None, template_name='summaries/summary.html'):

    summary = get_object_or_404(Summary, id=summary_id)

    comment_form = WmdCommentForm(extra_id='summary_comment')    
    
    return render_to_response(template_name, {
        'summary': summary,
        'content_object': summary.content_object,
        'comment_form': comment_form,
    }, context_instance=RequestContext(request))


def revision(request, summary_id=None, revision=1, template_name='summaries/revision.html'):
    
    summary = get_object_or_404(Summary, id=summary_id)
    revision = get_object_or_404(summary.summaryrevision_set, revision=int(revision))
    
    comment_form = WmdCommentForm(extra_id='revision_comment')
    
    return render_to_response(template_name, {
        'summary': summary,
        'revision': revision,
        'comment_form': comment_form,
    }, context_instance=RequestContext(request))


def history(request, summary_id=None, template_name='summaries/history.html'):

    summary = get_object_or_404(Summary, id=summary_id)
    changes = summary.revision_set.all().order_by('-revision')

    return render_to_response(template_name, {
        'summary': summary,
        'changes': changes,
    }, context_instance=RequestContext(request))

@login_required
def revert(request, summary_id=None, revision=1, template_name='summaries/revert.html'):
    
    summary = get_object_or_404(Summary, id=summary_id)
    revision = get_object_or_404(summary.revision_set, revision=int(revision))
    
    if request.method == 'POST':
        # revert the document
        summary.revert_to(revision, request.user)
        
        summary.register_action(request.user, 'revert', revision)
        
        redirect_to = reverse("summary_history", kwargs={'summary_id': summary_id})
        return HttpResponseRedirect(redirect_to)
    
    return render_to_response(template_name, {
        'summary': summary,
        'revision': revision,
        'revision': revision,
    }, context_instance=RequestContext(request))
    


