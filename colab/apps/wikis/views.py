from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import Http404, HttpResponseRedirect, HttpResponseNotAllowed, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, render_to_response
from django.views.generic.simple import redirect_to
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib import messages

from threadedcomments.models import ThreadedComment

from wikis.models import Wiki, ChangeSet
from wikis.forms import WikiForm, PaperForm, PageForm, SummaryForm

from headquarters.forms import WmdCommentForm

@login_required
def create(request, content_type=None, object_id=None, wiki_type=None, form_class=WikiForm, template_name="wikis/create.html"):

    # Get the parent object if passed one
    if content_type and object_id:
        object_type = get_object_or_404(ContentType, id=content_type)
        content_object = object_type.get_object_for_this_type(id=object_id)
    else:
        content_object = none
    
    if wiki_type == 'paper':
        form_class = PaperForm
    elif wiki_type == 'page':
        form_class = PageForm
    elif wiki_type == 'summary':
        form_class = SummaryForm
    form = form_class(request.POST or None)
    
    if form.is_valid():
        form.editor = request.user
        form.content_object = content_object

        wiki, changeset = form.save()
        
        wiki.register_action(request.user, 'create', changeset)
        
        if hasattr(wiki.content_object, 'feed'):
            wiki.content_object.register_action(request.user, 'add wiki', wiki)
        
        user_message = u"Your wiki was created successfully."
        request.user.message_set.create(message=user_message)
        
        return HttpResponseRedirect(wiki.get_absolute_url())

    form = form_class(request.POST or None, wiki_type=wiki_type)
    
    return render_to_response(template_name, {
        'content_object': content_object,
        'wiki_form': form,
        'wiki_type': wiki_type,
    }, context_instance=RequestContext(request))

@login_required
def edit(request, wiki_id=None, form_class=WikiForm, template_name='wikis/edit.html'):
    
    wiki = get_object_or_404(Wiki, id=wiki_id)

    form = form_class(request.POST or None, instance=wiki)

    if form.is_valid():
        form.editor = request.user
        wiki, changeset = form.save()
        
        wiki.register_action(request.user, 'edit', changeset)
        
        user_message = u"Your wiki was edited successfully."
        request.user.message_set.create(message=user_message)
        
        return HttpResponseRedirect(wiki.get_absolute_url())

    return render_to_response(template_name, {
        'wiki': wiki,
        'wiki_form': form,
    }, context_instance=RequestContext(request))

@login_required
def delete(request, wiki_id=None, template_name='wikis/delete.html'):
    
    wiki = get_object_or_404(Wiki, id=wiki_id)

    redirect_url = wiki.get_absolute_url()
    
    if request.user == wiki.creator:
        if not ThreadedComment.objects.all_for_object(wiki).exists():
            wiki.feed.delete()
            wiki.delete()
            messages.add_message(request, messages.SUCCESS,
                _("Wiki %s deleted.") % wiki.title
            )
            redirect_url = wiki.content_object.get_absolute_url()
        else:
            messages.add_message(request, messages.ERROR,
                _("Please delete comments before deleting the wiki.")
            )
    else:
        messages.add_message(request, messages.SUCCESS,
            _("You are not the creator of this wiki.")
        )
    
    return HttpResponseRedirect(redirect_url)


def wiki(request, wiki_id=None, template_name='wikis/wiki.html'):

    wiki = get_object_or_404(Wiki, id=wiki_id)

    comment_form = WmdCommentForm(extra_id='wiki_comment')    
    
    return render_to_response(template_name, {
        'wiki': wiki,
        'content_object': wiki.content_object,
        'comment_form': comment_form,
    }, context_instance=RequestContext(request))


def changeset(request, wiki_id=None, revision=1, template_name='wikis/changeset.html'):
    
    wiki = get_object_or_404(Wiki, id=wiki_id)
    changeset = get_object_or_404(wiki.changeset_set, revision=int(revision))
    
    comment_form = WmdCommentForm(extra_id='changeset_comment')
    
    return render_to_response(template_name, {
        'wiki': wiki,
        'changeset': changeset,
        'comment_form': comment_form,
    }, context_instance=RequestContext(request))


def history(request, wiki_id=None, template_name='wikis/history.html'):

    wiki = get_object_or_404(Wiki, id=wiki_id)
    changes = wiki.changeset_set.all().order_by('-revision')

    return render_to_response(template_name, {
        'wiki': wiki,
        'changes': changes,
    }, context_instance=RequestContext(request))

@login_required
def revert(request, wiki_id=None, revision=1, template_name='wikis/revert.html'):
    
    wiki = get_object_or_404(Wiki, id=wiki_id)
    changeset = get_object_or_404(wiki.changeset_set, revision=int(revision))
    
    if request.method == 'POST':
        # revert the document
        wiki.revert_to(revision, request.user)
        
        wiki.register_action(request.user, 'revert', changeset)
        
        redirect_to = reverse("wiki_history", kwargs={'wiki_id': wiki_id})
        return HttpResponseRedirect(redirect_to)
    
    return render_to_response(template_name, {
        'wiki': wiki,
        'changeset': changeset,
        'revision': revision,
    }, context_instance=RequestContext(request))
    


