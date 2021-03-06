import difflib
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponseNotAllowed, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic.simple import redirect_to
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.core.paginator import Paginator, EmptyPage, InvalidPage

from django.contrib.contenttypes.models import ContentType
from django.contrib import messages

from papers.models import Paper, PaperRevision
from papers.forms import PaperForm, DeletePaperForm
from threadedcomments.forms import RichCommentForm

@login_required
def create(request, content_type=None, object_id=None, form_class=PaperForm, template_name="papers/edit.html"):

    # Get the parent object if passed one
    if content_type and object_id:
        object_type = get_object_or_404(ContentType, id=content_type)
        content_object = object_type.get_object_for_this_type(id=object_id)
    else:
        content_object = none
    
    form = form_class(request.POST or None, auto_id='paper_%s')
    
    if form.is_valid():
        form.editor = request.user
        form.content_object = content_object
        paper, revision = form.save(request)
        
        # Updates and messages
        paper.register_action(request.user, 'create-paper', revision)
        
        if hasattr(paper.content_object, 'feed'):
            paper.content_object.register_action(request.user, 'add-paper-issue', paper)
        
        user_message = u"Your paper was created successfully."
        request.user.message_set.create(message=user_message)
        
        return HttpResponseRedirect(paper.get_absolute_url())
    
    return render_to_response(template_name, {
        'content_object': content_object,
        'paper_form': form,
    }, context_instance=RequestContext(request))

@login_required
def edit(request, paper_id=None, slug=None, revision_number=None, form_class=PaperForm, paper_delete_form=DeletePaperForm, template_name='papers/edit.html'):
    
    paper = get_object_or_404(Paper, slug=slug)
    revision = paper.current
    initial = {'content': revision.content}
    
    if revision_number:
        # There is a specific revision, fetch this
        rev_specific = PaperRevision.objects.get(paper=paper, revision=revision_number) # shouldn't there be a way to do this with paper.revisions?
        if revision.pk != rev_specific.pk:
            revision = rev_specific
            revision.is_not_current = True
            initial = {'content': revision.content, 'comment': _('Reverted to #%d' % revision.revision)}

    form = form_class(request.POST or None, instance=paper, initial=initial, auto_id='paper_%s')
    
    if form.is_valid():
        form.editor = request.user
        paper, revision = form.save(request)
        
        paper.register_action(request.user, 'edit-paper', revision)
        
        user_message = u"Your paper was edited successfully."
        request.user.message_set.create(message=user_message)
        
        return HttpResponseRedirect(paper.get_absolute_url())

    return render_to_response(template_name, {
        'paper': paper,
        'revision': revision,
        'paper_form': form,
    }, context_instance=RequestContext(request))

@login_required
def delete(request, paper_id=None, slug=None, revision_number=None, template_name='papers/delete.html'):
    
    paper = get_object_or_404(Paper, slug=slug)
    revision = paper.current
    
    if revision_number:
        # user wants to delete a specific revision, not the paper
        rev_specific = PaperRevision.objects.get(paper=paper, revision=revision_number) # shouldn't there be a way to do this with paper.revisions?
        if revision.pk != rev_specific.pk:
            revision = rev_specific
            revision.is_not_current = True
        
        if request.method == 'POST' and request.POST.get('delete'):
            if request.user == revision.editor:
                revision.delete()
                messages.add_message(request, messages.SUCCESS,
                    _("Revision #%d deleted.") % revision.revision
                )
                redirect_url = paper.get_absolute_url()
            else:
                messages.add_message(request, messages.ERROR,
                    _("You are not the editor of this revision.")
                )
                redirect_url = revision.get_absolute_url()
            return HttpResponseRedirect(redirect_url)
    else:
        # user wants to delete entire paper
        if request.method == 'POST' and request.POST.get('delete'):
            if request.user == paper.creator:
                paper.feed.delete()
                paper.delete()
                messages.add_message(request, messages.SUCCESS,
                    _("Paper %s deleted.") % paper.title
                )
                redirect_url = paper.content_object.get_absolute_url()
            else:
                messages.add_message(request, messages.ERROR,
                    _("You are not the creator of this paper.")
                )
                redirect_url = paper.get_absolute_url()
            return HttpResponseRedirect(redirect_url)
    
    return render_to_response(template_name, {
        'paper': paper,
        'revision': revision,
        'revision_number': revision_number,
        'content_object': paper.content_object,
    }, context_instance=RequestContext(request))


def paper(request, paper_id=None, slug=None, revision_number=None, template_name='papers/paper.html'):

    paper = get_object_or_404(Paper, slug=slug)
    revision = paper.current
    
    if revision_number:
        new_revision = paper.revisions.get(revision=revision_number)
        if revision.pk != new_revision.pk:
            new_revision.is_not_current = True
        revision = new_revision

    comment_form = RichCommentForm(auto_id='paper_comment_%s')    
    
    return render_to_response(template_name, {
        'paper': paper,
        'revision': revision,
        'content_object': paper.content_object,
        'comment_form': comment_form,
    }, context_instance=RequestContext(request))


def history(request, paper_id=None, slug=None, template_name='papers/history.html'):

    paper = get_object_or_404(Paper, slug=slug)

    return render_to_response(template_name, {
        'paper': paper,
    }, context_instance=RequestContext(request))

def changes(request, paper_id=None, slug=None, template_name='papers/changes.html', extra_context=None):
    rev_number_a = request.GET.get('a', None)
    rev_number_b = request.GET.get('b', None)

    # Some stinky fingers manipulated the url
    if not rev_number_a or not rev_number_b:
        return HttpResponseBadRequest('Bad Request')
    
    paper = get_object_or_404(Paper, slug=slug)
    revision_a = PaperRevision.objects.get(paper=paper, revision=rev_number_a)
    revision_b = PaperRevision.objects.get(paper=paper, revision=rev_number_b)

    if revision_a.content != revision_b.content:
        d = difflib.unified_diff(revision_b.content.splitlines(),
                                 revision_a.content.splitlines(),
                                 'Original', 'Current', lineterm='')
        difftext = '\n'.join(d)
    else:
        difftext = _(u'No changes were made between this two files.')
    
    return render_to_response(template_name, {
        'paper': paper,
        'rev_number_a': rev_number_a,
        'rev_number_b': rev_number_b,
        'revision_a': revision_a,
        'revision_b': revision_b,
        'diff': difftext,
    }, context_instance=RequestContext(request))
