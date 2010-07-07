from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponseNotAllowed, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic.simple import redirect_to
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages

from papers.models import Paper, PaperRevision
from papers.forms import PaperForm
from threadedcomments.forms import RichCommentForm

@login_required
def create(request, content_type=None, object_id=None, form_class=PaperForm, template_name="papers/create.html"):

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

        paper, revision = form.save()
        
        paper.register_action(request.user, 'create', revision)
        
        if hasattr(paper.content_object, 'feed'):
            paper.content_object.register_action(request.user, 'add paper', paper)
        
        user_message = u"Your paper was created successfully."
        request.user.message_set.create(message=user_message)
        
        return HttpResponseRedirect(paper.get_absolute_url())
    
    return render_to_response(template_name, {
        'content_object': content_object,
        'paper_form': form,
    }, context_instance=RequestContext(request))

@login_required
def edit(request, paper_id=None, form_class=PaperForm, template_name='papers/edit.html'):
    
    paper = get_object_or_404(Paper, id=paper_id)

    form = form_class(request.POST or None, instance=paper)

    if form.is_valid():
        form.editor = request.user
        paper, revision = form.save()
        
        paper.register_action(request.user, 'edit', revision)
        
        user_message = u"Your paper was edited successfully."
        request.user.message_set.create(message=user_message)
        
        return HttpResponseRedirect(paper.get_absolute_url())

    return render_to_response(template_name, {
        'paper': paper,
        'paper_form': form,
    }, context_instance=RequestContext(request))

@login_required
def delete(request, paper_id=None, template_name='papers/delete.html'):
    
    paper = get_object_or_404(Paper, id=paper_id)

    redirect_url = paper.get_absolute_url()
    
    if request.user == paper.creator:
        if not ThreadedComment.objects.all_for_object(paper).exists():
            paper.feed.delete()
            paper.delete()
            messages.add_message(request, messages.SUCCESS,
                _("Paper %s deleted.") % paper.title
            )
            redirect_url = paper.content_object.get_absolute_url()
        else:
            messages.add_message(request, messages.ERROR,
                _("Please delete comments before deleting the paper.")
            )
    else:
        messages.add_message(request, messages.SUCCESS,
            _("You are not the creator of this paper.")
        )
    
    return HttpResponseRedirect(redirect_url)


def paper(request, paper_id=None, template_name='papers/paper.html'):

    paper = get_object_or_404(Paper, id=paper_id)

    comment_form = WmdCommentForm(extra_id='paper_comment')    
    
    return render_to_response(template_name, {
        'paper': paper,
        'content_object': paper.content_object,
        'comment_form': comment_form,
    }, context_instance=RequestContext(request))


def revision(request, paper_id=None, revision=1, template_name='papers/revision.html'):
    
    paper = get_object_or_404(Paper, id=paper_id)
    revision = get_object_or_404(paper.paperrevision_set, revision=int(revision))
    
    comment_form = WmdCommentForm(extra_id='revision_comment')
    
    return render_to_response(template_name, {
        'paper': paper,
        'revision': revision,
        'comment_form': comment_form,
    }, context_instance=RequestContext(request))


def history(request, paper_id=None, template_name='papers/history.html'):

    paper = get_object_or_404(Paper, id=paper_id)
    changes = paper.revision_set.all().order_by('-revision')

    return render_to_response(template_name, {
        'paper': paper,
        'changes': changes,
    }, context_instance=RequestContext(request))

@login_required
def revert(request, paper_id=None, revision=1, template_name='papers/revert.html'):
    
    paper = get_object_or_404(Paper, id=paper_id)
    revision = get_object_or_404(paper.revision_set, revision=int(revision))
    
    if request.method == 'POST':
        # revert the document
        paper.revert_to(revision, request.user)
        
        paper.register_action(request.user, 'revert', revision)
        
        redirect_to = reverse("paper_history", kwargs={'paper_id': paper_id})
        return HttpResponseRedirect(redirect_to)
    
    return render_to_response(template_name, {
        'paper': paper,
        'revision': revision,
        'revision': revision,
    }, context_instance=RequestContext(request))
    


