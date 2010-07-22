import difflib
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
from summaries.forms import SummaryForm, DeleteSummaryForm
from threadedcomments.forms import RichCommentForm

@login_required
def create(request, content_type=None, object_id=None, form_class=SummaryForm, template_name="summaries/edit.html"):

    # Get the parent object if passed one
    if content_type and object_id:
        object_type = get_object_or_404(ContentType, id=content_type)
        content_object = object_type.get_object_for_this_type(id=object_id)
    else:
        content_object = none
    
    form = form_class(request.POST or None, auto_id='summary_%s')
    
    if form.is_valid():
        form.editor = request.user
        form.content_object = content_object
        summary, revision = form.save(request)
        
        # Updates and messages
        summary.register_action(request.user, 'create', revision)
        
        if hasattr(summary.content_object, 'feed'):
            summary.content_object.register_action(request.user, 'add summary', summary)
        
        user_message = u"Your summary was created successfully."
        request.user.message_set.create(message=user_message)
        
        return HttpResponseRedirect(summary.get_absolute_url())
    
    return render_to_response(template_name, {
        'content_object': content_object,
        'summary_form': form,
    }, context_instance=RequestContext(request))

@login_required
def edit(request, summary_id=None, slug=None, revision_number=None, form_class=SummaryForm, summary_delete_form=DeleteSummaryForm, template_name='summaries/edit.html'):
    
    summary = get_object_or_404(Summary, slug=slug)
    revision = summary.current
    initial = {'content': revision.content}
    
    if revision_number:
        # There is a specific revision, fetch this
        rev_specific = SummaryRevision.objects.get(summary=summary, revision=revision_number) # shouldn't there be a way to do this with summary.revisions?
        if revision.pk != rev_specific.pk:
            revision = rev_specific
            revision.is_not_current = True
            initial = {'content': revision.content, 'comment': _('Reverted to #%d' % revision.revision)}

    form = form_class(request.POST or None, instance=summary, initial=initial, auto_id='summary_%s')
    
    if form.is_valid():
        form.editor = request.user
        summary, revision = form.save(request)
        
        summary.register_action(request.user, 'edit', revision)
        
        user_message = u"Your summary was edited successfully."
        request.user.message_set.create(message=user_message)
        
        return HttpResponseRedirect(summary.get_absolute_url())

    return render_to_response(template_name, {
        'summary': summary,
        'revision': revision,
        'summary_form': form,
    }, context_instance=RequestContext(request))

@login_required
def delete(request, summary_id=None, slug=None, revision_number=None, template_name='summaries/delete.html'):
    
    summary = get_object_or_404(Summary, slug=slug)
    revision = summary.current
    
    if revision_number:
        # user wants to delete a specific revision, not the summary
        rev_specific = SummaryRevision.objects.get(summary=summary, revision=revision_number) # shouldn't there be a way to do this with summary.revisions?
        if revision.pk != rev_specific.pk:
            revision = rev_specific
            revision.is_not_current = True
        
        if request.method == 'POST' and request.POST.get('delete'):
            if request.user == revision.editor:
                revision.delete()
                messages.add_message(request, messages.SUCCESS,
                    _("Revision #%d deleted.") % revision.revision
                )
                redirect_url = summary.get_absolute_url()
            else:
                messages.add_message(request, messages.ERROR,
                    _("You are not the editor of this revision.")
                )
                redirect_url = revision.get_absolute_url()
            return HttpResponseRedirect(redirect_url)
    else:
        # user wants to delete entire summary
        if request.method == 'POST' and request.POST.get('delete'):
            if request.user == summary.creator:
                summary.feed.delete()
                summary.delete()
                messages.add_message(request, messages.SUCCESS,
                    _("Summary %s deleted.") % summary.title
                )
                redirect_url = summary.content_object.get_absolute_url()
            else:
                messages.add_message(request, messages.ERROR,
                    _("You are not the creator of this summary.")
                )
                redirect_url = summary.get_absolute_url()
            return HttpResponseRedirect(redirect_url)
    
    return render_to_response(template_name, {
        'summary': summary,
        'revision': revision,
        'revision_number': revision_number,
        'content_object': summary.content_object,
    }, context_instance=RequestContext(request))


def summary(request, summary_id=None, slug=None, revision_number=None, template_name='summaries/summary.html'):

    summary = get_object_or_404(Summary, slug=slug)
    revision = summary.current
    
    if revision_number:
        new_revision = summary.revisions.get(revision=revision_number)
        if revision.pk != new_revision.pk:
            new_revision.is_not_current = True
        revision = new_revision

    comment_form = RichCommentForm(auto_id='summary_comment_%s')    
    
    return render_to_response(template_name, {
        'summary': summary,
        'revision': revision,
        'content_object': summary.content_object,
        'comment_form': comment_form,
    }, context_instance=RequestContext(request))


def history(request, summary_id=None, slug=None, template_name='summaries/history.html'):

    summary = get_object_or_404(Summary, slug=slug)

    return render_to_response(template_name, {
        'summary': summary,
    }, context_instance=RequestContext(request))

def changes(request, summary_id=None, slug=None, template_name='summaries/changes.html', extra_context=None):
    rev_number_a = request.GET.get('a', None)
    rev_number_b = request.GET.get('b', None)

    # Some stinky fingers manipulated the url
    if not rev_number_a or not rev_number_b:
        return HttpResponseBadRequest('Bad Request')
    
    summary = get_object_or_404(Summary, slug=slug)
    revision_a = SummaryRevision.objects.get(summary=summary, revision=rev_number_a)
    revision_b = SummaryRevision.objects.get(summary=summary, revision=rev_number_b)

    if revision_a.content != revision_b.content:
        d = difflib.unified_diff(revision_b.content.splitlines(),
                                 revision_a.content.splitlines(),
                                 'Original', 'Current', lineterm='')
        difftext = '\n'.join(d)
    else:
        difftext = _(u'No changes were made between this two files.')
    
    return render_to_response(template_name, {
        'summary': summary,
        'rev_number_a': rev_number_a,
        'rev_number_b': rev_number_b,
        'revision_a': revision_a,
        'revision_b': revision_b,
        'diff': difftext,
    }, context_instance=RequestContext(request))
