from django import template
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

register = template.Library()

from threadedcomments.models import ThreadedComment

from issues.models import Issue
from papers.models import Paper, PaperRevision
from summaries.models import Summary, SummaryRevision
from voting.models import Vote
from feedback.models import Feedback

### Get the icon name for a post ###
@register.simple_tag
def post_icon(post):
    """ Return the name of the icon to use depending on the type of post """
    icon = None
    if isinstance(post, Issue):
        icon = 'script'
    elif isinstance(post, Paper) or isinstance(post, PaperRevision):
        icon = 'report'
    elif isinstance(post, Summary) or isinstance(post, SummaryRevision):
        icon = 'newspaper'
    elif isinstance(post, Feedback):
        icon = 'bug'
    elif isinstance(post, ThreadedComment):
        icon = 'comment'
    
    return icon

### Get the author of a post ###
@register.simple_tag
def post_author(post):
    """ Return the author depending on the type of post """
    author = None
    if isinstance(post, Issue):
        author = post.creator
    elif isinstance(post, Paper) or isinstance(post, Summary):
        author = post.last_editor
    elif isinstance(post, PaperRevision) or isinstance(post, SummaryRevision):
        author = post.editor
    elif isinstance(post, Feedback):
        if not post.user or post.anonymous:
            author = 'anonymous'
        else:
            author = post.user
    elif isinstance(post, ThreadedComment):
        author = post.user
    
    return author

### Get the datetime for a post ###
@register.simple_tag
def post_datetime(post):
    """ Return the datetime depending on the type of post """
    datetime = None
    if isinstance(post, Issue):
        datetime = post.created
    elif isinstance(post, Paper) or isinstance(post, Summary):
        datetime = post.last_edited
    elif isinstance(post, PaperRevision) or isinstance(post, SummaryRevision):
        datetime = post.modified
    elif isinstance(post, Feedback):
        datetime = post.created
    elif isinstance(post, ThreadedComment):
        datetime = post.date_submitted
    
    return datetime

### Meta summary: votes; contrib, issues, wiki counts ###
@register.inclusion_tag("headquarters/meta_summary.html")
def post_meta_summary(post, show_author=True):
    contributor_count = the_user = comment_count = None    
    
    if isinstance(post, Issue):
        contributor_count = post.contributors.count()
        the_user = post.creator
        comment_count = True
    elif isinstance(post, Paper) or isinstance(post, Summary):
        the_user = post.creator
        comment_count = True
    elif isinstance(post, ThreadedComment):
        the_user = post.user
    
    return {'post': post, 'the_author': post_author(post), 'comment_count': comment_count,
        'contributor_count': contributor_count, 'show_author': show_author,
        'icon': post_icon(post), 'datetime': post_datetime(post)}

### Meta for a issue: voting, permalink, flag, bounty, and top contribs ###
@register.inclusion_tag("headquarters/meta.html", takes_context=True)
def post_meta(context, post):
    # get vote details
    post_type = ContentType.objects.get_for_model(post)
    try:
        previous_vote = Vote.objects.get(content_type=post_type, object_id=post.id, user=context['request'].user)
    except:
        previous_vote = None
    
    if isinstance(post, Issue):
        author_field = "creator"
        permalink = post.get_absolute_url()
        vote_url = 'issue_vote'
    elif isinstance(post, Paper):
        author_field = "creator"
        permalink = post.get_absolute_url()
        vote_url = 'paper_vote'
    elif isinstance(post, PaperRevision):
        author_field = "editor"
        permalink = post.get_absolute_url()
        vote_url = 'paper_revision_vote'
    elif isinstance(post, Summary):
        author_field = "creator"
        permalink = post.get_absolute_url()
        vote_url = 'summary_vote'
    elif isinstance(post, SummaryRevision):
        author_field = "editor"
        permalink = post.get_absolute_url()
        vote_url = 'summary_revision_vote'
    elif isinstance(post, Feedback):
        author_field = "user"
        permalink = post.get_absolute_url()
        vote_url = 'feedback_vote'
    elif isinstance(post, ThreadedComment):
        author_field = "user"
        permalink = comment_url(post)
        vote_url = 'comment_vote'
    
    previous_up = False
    previous_down = False
    if previous_vote is not None:
        if previous_vote.vote == 1:
            previous_up = True
            up_url = reverse(vote_url, args=[post.id, "clear"])
            down_url = reverse(vote_url, args=[post.id, "down"])
        elif previous_vote.vote == -1:
            previous_down = True
            up_url = reverse(vote_url, args=[post.id, "up"])
            down_url = reverse(vote_url, args=[post.id, "clear"])
    else:
        up_url = reverse(vote_url, args=[post.id, "up"])
        down_url = reverse(vote_url, args=[post.id, "down"])
    
    up_url += "?next="+context['request'].path
    down_url += "?next="+context['request'].path
    
    return {'post': post, 'request': context['request'], 'icon': post_icon(post),
        'the_author': post_author(post), 'datetime': post_datetime(post),
        'previous_up': previous_up, 'previous_down': previous_down,
        'up_url': up_url, 'down_url': down_url, 'author_field': author_field,
        'permalink': permalink, 'post_type': post_type}

### Shows a comment, to keep the full comment rendering in one file ###
@register.inclusion_tag("headquarters/comment_item.html", takes_context=True)
def show_comment(context, comment):
    return {'comment': comment, 'request': context['request']}

### Links to a specific comment's id ###
@register.simple_tag
def comment_url(comment):
    return comment.content_object.get_absolute_url()+"#comment-"+str(comment.id)

### List comments on a post ###
@register.inclusion_tag("headquarters/comments.html", takes_context=True)
def comment_list(context, post):
    sort_field = ''
    sort = context['request'].GET.get('sort', 'date_submitted')
    direction = context['request'].GET.get('dir', 'desc')
    
    if sort == 'date_submitted': # reverse direction for dates (intuition)
        if direction == 'desc':
            direction = 'asc'
        else:
            direction = 'desc'
    if direction == 'desc':
        sort_field += '-'
    sort_field += sort
    
    comments = ThreadedComment.public.get_tree(post, sort=sort_field)
    return {'comments': comments, 'comment_count': len(comments), 'post': post,
        'request': context['request']}

### Full preview of an update instance ###
@register.inclusion_tag("headquarters/update_preview.html", takes_context=True)
def update_preview(context, update):
    feed_object = update.feed.feed_object
    update_object = update.content_object
    feed_type = update.action.feed_type
    icon = object_content = None
    
    if isinstance(update_object, Issue):
        object_content = update_object.description
    elif isinstance(update_object, Paper) or isinstance(update_object, Summary):
        object_content = update_object.content
    elif isinstance(update_object, ThreadedComment):
        object_content = update_object.comment
    
    return {'update': update, 'update_user': update.user,
        'feed_object': feed_object, 'update_object': update_object,
        'object_content': object_content}
