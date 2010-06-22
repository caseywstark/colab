from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse

from object_feeds.models import Feed, Subscription, Action

class SubscriptionForm(forms.Form):
    
    feed = forms.ModelChoiceField(queryset=Feed.objects.all(), required=False)
    user = forms.ModelChoiceField(queryset=User.objects.all(), required=False)
    actions = forms.ModelMultipleChoiceField(queryset=Action.objects.all(), required=False)
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.feed = kwargs.pop('feed', None)
        self.actions = kwargs.pop('actions', None)
        
        super(SubscriptionForm, self).__init__(*args, **kwargs)
        
        # see if a subscription exists
        try:
            self.subscription = Subscription.objects.get(feed=self.feed, user=self.user)
        except Subscription.DoesNotExist:
            self.subscription = None
        
        # hide the fields we don't need, but give them their data
        self.fields['feed'].widget = forms.HiddenInput()
        self.fields['user'].widget = forms.HiddenInput()
        actions = None
        if self.subscription:
            actions = self.subscription.actions
        self.fields['actions'].widget = forms.HiddenInput()
        self.fields['actions'].queryset = Action.objects.filter(feed_type=self.feed.feed_type)
        
        # create checkbox for each action
        for action in self.fields['actions'].queryset.all():
            action_field = forms.BooleanField(label=_("when %s is %s" % (self.feed.feed_type, action.description)),
                required=False)
            action_name = 'action_%s' % action.name
            self.fields[action_name] = action_field
            if self.subscription and action in self.subscription.actions.all():
                self.initial.update({action_name: True})
    
    def save(self):
        action_names = []
        for field_name, action_field in self.fields.items():
            if field_name.startswith('action_') and self.cleaned_data[field_name]: # one of the action checkboxes
                action_name = field_name.replace('action_', '') # should just take out the first 7, but I'm lazy
                action_names.append(action_name)
        
        actions = self.fields['actions'].queryset.filter(name__in=action_names)
        subscription, created = Subscription.objects.get_or_create(feed=self.cleaned_data['feed'], user=self.cleaned_data['user'])
        subscription.actions = actions
        subscription.save()
        return subscription
