from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.datastructures import SortedDict
from django.core.paginator import Paginator
from django.utils.translation import ugettext, ugettext_lazy as _

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType

from threadedcomments.models import ThreadedComment
from threadedcomments.forms import RichCommentForm
from tagging.models import Tag, TaggedItem

from issues.models import Issue, IssueContributor
from issues.forms import IssueForm, InviteContributorForm, ResolutionForm, PrivacyForm

from disciplines.models import Discipline
from papers.models import Paper

@login_required
def create(request, form_class=IssueForm, template_name="issues/create.html"):
    issue_form = form_class(request.POST or None, auto_id='new_issue_%s')
    
    if issue_form.is_valid():
        issue = issue_form.save(commit=False)
        issue.creator = request.user
        issue.save()
        issue_form.save_m2m() # to save disciplines after commit=False
        
        issue.register_action(request.user, 'create-issue', issue)
        
        issue_contributor = IssueContributor(issue=issue, user=request.user)
        issue.contributors.add(issue_contributor)
        issue_contributor.save()
        
        issue.feed.subscribe(request.user)
        
        return HttpResponseRedirect(issue.get_absolute_url())
    
    return render_to_response(template_name, {
        "issue_form": issue_form,
    }, context_instance=RequestContext(request))

@login_required
def edit(request, slug=None, form_class=IssueForm, template_name="issues/edit.html"):
    issue = get_object_or_404(Issue, slug=slug)
    
    if issue.creator != request.user:
        return render_to_response('issues/forbidden.html', {}, context_instance=RequestContext(request))
    
    issue_form = form_class(request.POST or None, instance=issue, auto_id='edit_issue_%s')
    
    if issue_form.is_valid():
        issue = issue_form.save()
        
        issue.register_action(request.user, 'edit-issue', issue)
        
        return HttpResponseRedirect(issue.get_absolute_url())
    
    return render_to_response(template_name, {
        'issue': issue,
        'issue_form': issue_form,
    }, context_instance=RequestContext(request))

@login_required
def delete(request, slug=None, redirect_url=None):
    issue = get_object_or_404(Issue, slug=slug)
    redirect_url = issue.get_absolute_url()
    
    if request.user == issue.creator:
        if not issue.papers.exists():
            if not ThreadedComment.objects.get_for_object(issue).exists():
                issue.feed.delete()
                issue.delete()
                messages.add_message(request, messages.SUCCESS,
                    _("Issue %s deleted.") % issue.title
                )
                redirect_url = reverse("issue_list")
            else:
                messages.add_message(request, messages.ERROR,
                    _("Please delete comments before deleting the issue.")
                )
        else:
            messages.add_message(request, messages.SUCCESS,
                _("Please delete papers before deleting the issue.")
            )
    else:
        messages.add_message(request, messages.SUCCESS,
            _("You are not the creator of this issue.")
        )
    
    return HttpResponseRedirect(redirect_url)

def issues(request, mine=False, template_name="issues/issues.html"):
    authenticated = request.user.is_authenticated()
    
    if authenticated and mine:
        issues = Issue.objects.filter(contributor_users=request.user)
    else:
        issues = Issue.objects.filter(private=False)
    
    search_terms = request.GET.get('search', '')
    if search_terms:
        issues = (issues.filter(title__icontains=search_terms) |
            issues.filter(description__icontains=search_terms))
    
    # Additional filtering
    sandbox = request.GET.get('sandbox', None)
    model_project = request.GET.get('model_project', None)
    discipline = request.GET.get('discipline', None)
    the_discipline = None
    tag = request.GET.get('tag', None)
    the_tag = None
    if not sandbox:
        issues = issues.filter(sandbox=False)
    if model_project:
        issues = issues.filter(model_project=True)
    if discipline:
        try:
            the_discipline = Discipline.objects.get(slug=discipline) # make sure the discpline exists
            issues = issues.filter(disciplines=the_discipline)
        except Discipline.DoesNotExist:
            messages.add_message(request, messages.ERROR, _("That discipline does not exist."))
    if tag:
        try:
            the_tag = Tag.objects.get(id=tag) # make sure the tag exists
            issues = TaggedItem.objects.get_by_model(issues, the_tag)
        except Tag.DoesNotExist:
            messages.add_message(request, messages.ERROR, _("That tag does not exist."))
    
    # get filter querysets
    if the_discipline:
        discipline_filters = the_discipline.get_children()[:10]
    else:
        discipline_filters = Discipline.tree.root_nodes()[:10]
    if the_tag:
        tag_filters = Tag.objects.related_for_model(the_tag, Issue)[:10]
    else:
        tag_filters = Tag.objects.usage_for_model(Issue)[:10]
    
    # Figure out sorting to replace the title
    list_title = ''
    if mine:
        list_title += 'My '
    
    sort = request.GET.get('sort', 'created')
    direction = request.GET.get('dir', 'desc')
    
    if sort == 'created' and direction == 'desc':
        list_title += 'Newest Issues'
        issues = issues.order_by('-created')
    if sort == 'created' and direction == 'asc':
        list_title += 'Oldest Issues'
        issues = issues.order_by('created')
    if sort == 'yeas' and direction == 'desc':
        list_title += 'Most Liked Issues'
        issues = issues.order_by('-yeas')
    if sort == 'yeas' and direction == 'asc':
        list_title += 'Least Liked Issues'
        issues = issues.order_by('yeas')
    if sort == 'nays' and direction == 'desc':
        list_title += 'Most Disliked Issues'
        issues = issues.order_by('-nays')
    if sort == 'nays' and direction == 'asc':
        list_title += 'Least Disliked Issues'
        issues = issues.order_by('nays')
    
    # Paginate the list
    paginator = Paginator(issues, 20) # Show 20 issues per page
    
    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    # If page is out of range, deliver last page of results.
    try:
        issues = paginator.page(page)
    except (EmptyPage, InvalidPage):
        issues = paginator.page(paginator.num_pages)
    
    return render_to_response(template_name, {
        'issues': issues,
        'mine': mine,
        'search_terms': search_terms, 'the_discipline': the_discipline,
        'discipline_filters': discipline_filters, 'tag_filters': tag_filters,
        'the_tag': the_tag, 'sandbox': sandbox, 'model_project': model_project,
        'sort': sort, 'direction': direction,
        'list_title': list_title,
    }, context_instance=RequestContext(request))

def issue(request, slug=None, template_name="issues/issue.html"):
    issue = get_object_or_404(Issue, slug=slug)
    
    # check if private
    if issue.private and not issue.user_can_read(request.user):
        return render_to_response('issues/forbidden.html', {}, context_instance=RequestContext(request))
    
    issue_type = ContentType.objects.get_for_model(issue)
    
    comment_form = RichCommentForm(auto_id='new_issue_comment_%s')
    
    privacy_form = None
    if request.user == issue.creator:
        privacy_form = PrivacyForm(request.POST or None, issue=issue)
    
    if privacy_form and privacy_form.is_valid():
        if privacy_form.cleaned_data["privacy"]:
            issue.private = not issue.private
            issue.save()
            if issue.private:
                messages.add_message(request, messages.SUCCESS,_("Issue now private"))
            else:
                messages.add_message(request, messages.SUCCESS,_("Issue now public"))
    
    return render_to_response(template_name, {
        'issue': issue,
        'following': issue.is_user_following(request.user),
        'comment_form': comment_form,
        'privacy_form': privacy_form
    }, context_instance=RequestContext(request))

@login_required
def resolve(request, slug=None, template_name="issues/resolve.html"):
    issue = get_object_or_404(Issue, slug=slug)
    
    has_papers = issue.papers.exists()
    
    resolution_form = ResolutionForm(request.POST or None, issue=issue)
    
    if resolution_form.is_valid():
        resolution_paper = resolution_form.cleaned_data['resolution']
        if issue.resolve(resolution_paper):
            issue.register_action(request.user, 'resolve-issue', resolution_paper)
        else:
            messages.add_message(request, messages.ERROR,
                _("Sorry, the paper you selected is not associated with this issue.")
            )
        return HttpResponseRedirect(issue.get_absolute_url())
    
    return render_to_response(template_name, {
        'issue': issue,
        'resolution_form': resolution_form,
        'has_papers': has_papers,
    }, context_instance=RequestContext(request))

@login_required
def invite(request, slug=None, form_class=InviteContributorForm, template_name="issues/invite.html"):
    issue = get_object_or_404(Issue, slug=slug)
    
    if issue.creator != request.user:
        return render_to_response('issues/forbidden.html', {}, context_instance=RequestContext(request))
    
    invite_form = form_class(request.POST or None, issue=issue)
    
    if invite_form.is_valid():
        recipients = invite_form.save()
        
        # issue.register_action(request.user, 'invite', issue)
        
        return HttpResponseRedirect(issue.get_absolute_url())
    
    return render_to_response(template_name, {
        'issue': issue,
        'invite_form': invite_form,
    }, context_instance=RequestContext(request))
