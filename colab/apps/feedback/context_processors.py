from feedback.forms import WidgetForm

def widget_feedback_form(request):
    """
    Allows the feedback form to be displayed on every page as a widget.
    
    """
    initial = {'page': request.path}
    if request.user.is_authenticated():
        initial.update({'user': request.user.id})
    feedback_form = WidgetForm(initial=initial)
    return {'widget_feedback_form': feedback_form}
