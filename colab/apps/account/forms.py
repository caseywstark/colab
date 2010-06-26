import re

from django import forms
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _, ugettext
from django.utils.encoding import smart_unicode
from django.utils.hashcompat import sha_constructor
from django.utils.http import int_to_base36

from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site

from pinax.core.utils import get_send_mail
send_mail = get_send_mail()

from emailconfirmation.models import EmailAddress
from timezones.forms import TimeZoneField

from account.models import Account, PasswordReset
from account.models import OtherServiceInfo, other_service, update_other_services
from account.utils import user_display

from people.models import Researcher

alnum_re = re.compile(r"^\w+$")
name_re = re.compile(r"^[a-zA-Z\s'-.]+$")


# @@@ might want to find way to prevent settings access globally here.
REQUIRED_EMAIL = getattr(settings, "ACCOUNT_REQUIRED_EMAIL", False)
EMAIL_VERIFICATION = getattr(settings, "ACCOUNT_EMAIL_VERIFICATION", False)
EMAIL_AUTHENTICATION = getattr(settings, "ACCOUNT_EMAIL_AUTHENTICATION", False)
UNIQUE_EMAIL = getattr(settings, "ACCOUNT_UNIQUE_EMAIL", False)



class GroupForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        self.group = kwargs.pop("group", None)
        super(GroupForm, self).__init__(*args, **kwargs)


class LoginForm(GroupForm):
    
    password = forms.CharField(
        label = _("Password"),
        widget = forms.PasswordInput(render_value=False)
    )
    remember = forms.BooleanField(
        label = _("Remember Me"),
        help_text = _("If checked you will stay logged in for 3 weeks"),
        required = False
    )
    
    user = None
    
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        ordering = []
        if EMAIL_AUTHENTICATION:
            self.fields["email"] = forms.EmailField(
                label = ugettext("E-mail"),
            )
            ordering.append("email")
        else:
            self.fields["username"] = forms.CharField(
                label = ugettext("Username"),
                max_length = 30,
            )
            ordering.append("username")
        ordering.extend(["password", "remember"])
        self.fields.keyOrder = ordering
    
    def user_credentials(self):
        """
        Provides the credentials required to authenticate the user for
        login.
        """
        credentials = {}
        if EMAIL_AUTHENTICATION:
            credentials["email"] = self.cleaned_data["email"]
        else:
            credentials["username"] = self.cleaned_data["username"]
        credentials["password"] = self.cleaned_data["password"]
        return credentials
    
    def clean(self):
        if self._errors:
            return
        user = authenticate(**self.user_credentials())
        if user:
            if user.is_active:
                self.user = user
            else:
                raise forms.ValidationError(_("This account is currently inactive."))
        else:
            if EMAIL_AUTHENTICATION:
                error = _("The e-mail address and/or password you specified are not correct.")
            else:
                error = _("The username and/or password you specified are not correct.")
            raise forms.ValidationError(error)
        return self.cleaned_data
    
    def login(self, request):
        if self.is_valid():
            login(request, self.user)
            if self.cleaned_data["remember"]:
                request.session.set_expiry(60 * 60 * 24 * 7 * 3)
            else:
                request.session.set_expiry(0)
            return True
        return False


class SignupForm(GroupForm):
    
    name =  forms.CharField(
        label = _("Name"),
        max_length = 50,
        widget = forms.TextInput(),
        help_text = "your authorship name, as you want others to see it. Ex: John J. Smith.")
    username = forms.CharField(
        label = _("Username"),
        max_length = 30,
        widget = forms.TextInput(),
        help_text = "for your very own URL here on CoLab.")
    email = forms.EmailField(
        widget=forms.TextInput(),
        help_text = "for logging in and so we can contact you. Don't worry, this is kept private.")
    password1 = forms.CharField(
        label = _("Password"),
        widget = forms.PasswordInput(render_value=False))
    password2 = forms.CharField(
        label = _("Password (again)"),
        widget = forms.PasswordInput(render_value=False))
    confirmation_key = forms.CharField(
        max_length = 40,
        required = False,
        widget = forms.HiddenInput())
    
    def __init__(self, *args, **kwargs):
        super(SignupForm, self).__init__(*args, **kwargs)
        if REQUIRED_EMAIL or EMAIL_VERIFICATION or EMAIL_AUTHENTICATION:
            self.fields["email"].label = ugettext("E-mail")
            self.fields["email"].required = True
        else:
            self.fields["email"].label = ugettext("E-mail (optional)")
            self.fields["email"].required = False
    
    def clean_name(self):
        if not name_re.search(self.cleaned_data["name"]):
            raise forms.ValidationError(_("Names can only contain letters, periods, dashes, and apostrophes."))
        return self.cleaned_data["name"]
    
    def clean_username(self):
        if not alnum_re.search(self.cleaned_data["username"]):
            raise forms.ValidationError(_("Usernames can only contain letters, numbers and underscores."))
        try:
            user = User.objects.get(username__iexact=self.cleaned_data["username"])
        except User.DoesNotExist:
            return self.cleaned_data["username"]
        raise forms.ValidationError(_("This username is already taken. Please choose another."))
    
    def clean_email(self):
        value = self.cleaned_data["email"]
        if UNIQUE_EMAIL or EMAIL_AUTHENTICATION:
            try:
                User.objects.get(email__iexact=value)
            except User.DoesNotExist:
                return value
            raise forms.ValidationError(_("A user is registered with this e-mail address."))
        return value
    
    def clean(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data
    
    def create_user(self, username=None, commit=True):
        user = User()
        if username is None:
            raise NotImplementedError("SignupForm.create_user does not handle "
                "username=None case. You must override this method.")
        user.username = username
        user.email = self.cleaned_data["email"].strip().lower()
        password = self.cleaned_data["password1"]
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        if commit:
            user.save()
        return user
    
    def user_credentials(self):
        """
        Provides the credentials required to authenticate the user after
        sign-up is completed.
        """
        credentials = {}
        if EMAIL_AUTHENTICATION:
            credentials["email"] = self.cleaned_data["email"]
        else:
            credentials["username"] = self.cleaned_data["username"]
        credentials["password"] = self.cleaned_data["password1"]
        return credentials
    
    def save(self, request=None):
        # don"t assume a username is available. it is a common removal if
        # site developer wants to use e-mail authentication.
        username = self.cleaned_data.get("username")
        email = self.cleaned_data["email"]
        
        if self.cleaned_data["confirmation_key"]:
            from friends.models import JoinInvitation # @@@ temporary fix for issue 93
            try:
                join_invitation = JoinInvitation.objects.get(confirmation_key=self.cleaned_data["confirmation_key"])
                confirmed = True
            except JoinInvitation.DoesNotExist:
                confirmed = False
        else:
            confirmed = False
        
        # @@@ clean up some of the repetition below -- DRY!
        
        if confirmed:
            if email == join_invitation.contact.email:
                new_user = self.create_user(username)
                join_invitation.accept(new_user) # should go before creation of EmailAddress below
                if request:
                    messages.add_message(request, messages.INFO,
                        ugettext(u"Your email address has already been verified")
                    )
                # already verified so can just create
                EmailAddress(user=new_user, email=email, verified=True, primary=True).save()
            else:
                new_user = self.create_user(username)
                join_invitation.accept(new_user) # should go before creation of EmailAddress below
                if email:
                    if request:
                        messages.add_message(request, messages.INFO,
                            ugettext(u"Confirmation email sent to %(email)s") % {
                                "email": email,
                            }
                        )
                    EmailAddress.objects.add_email(new_user, email)
        else:
            new_user = self.create_user(username)
            if email:
                if request and not EMAIL_VERIFICATION:
                    messages.add_message(request, messages.INFO,
                        ugettext(u"Confirmation email sent to %(email)s") % {
                            "email": email,
                        }
                    )
                EmailAddress.objects.add_email(new_user, email)
        
        if EMAIL_VERIFICATION:
            new_user.is_active = False
            new_user.save()
        
        ### CoLab mods here ###
        name = self.cleaned_data["name"]
        new_researcher, created = Researcher.objects.get_or_create(user=new_user)
        new_researcher.name = name
        new_researcher.save()
        
        return self.user_credentials() # required for authenticate()


class OpenIDSignupForm(forms.Form):
    
    name =  forms.CharField(
        label = _("Name"),
        max_length = 50,
        widget = forms.TextInput(),
        help_text = "your authorship name, as you want others to see it. Ex: John J. Smith.")
    username = forms.CharField(
        label = _("Username"),
        max_length = 30,
        widget = forms.TextInput(),
        help_text = "for your very own URL here on CoLab.")
    email = forms.EmailField(
        widget=forms.TextInput(),
        help_text = "for logging in and so we can contact you. Don't worry, this is kept private.")
    
    def __init__(self, *args, **kwargs):
        # remember provided (validated!) OpenID to attach it to the new user
        # later.
        self.openid = kwargs.pop("openid", None)
        # pop these off since they are passed to this method but we can"t
        # pass them to forms.Form.__init__
        kwargs.pop("reserved_usernames", [])
        kwargs.pop("no_duplicate_emails", False)
        
        super(OpenIDSignupForm, self).__init__(*args, **kwargs)
        
        if REQUIRED_EMAIL or EMAIL_VERIFICATION or EMAIL_AUTHENTICATION:
            self.fields["email"].label = ugettext("E-mail")
            self.fields["email"].required = True
        else:
            self.fields["email"].label = ugettext("E-mail (optional)")
            self.fields["email"].required = False
    
    def clean_username(self):
        if not alnum_re.search(self.cleaned_data["username"]):
            raise forms.ValidationError(u"Usernames can only contain letters, numbers and underscores.")
        try:
            user = User.objects.get(username__iexact=self.cleaned_data["username"])
        except User.DoesNotExist:
            return self.cleaned_data["username"]
        raise forms.ValidationError(u"This username is already taken. Please choose another.")
    
    def clean_email(self):
        value = self.cleaned_data["email"]
        if UNIQUE_EMAIL or EMAIL_AUTHENTICATION:
            try:
                User.objects.get(email__iexact=value)
            except User.DoesNotExist:
                return value
            raise forms.ValidationError(_("A user is registered with this e-mail address."))
        return value
    
    def clean_name(self):
        if not name_re.search(self.cleaned_data["name"]):
            raise forms.ValidationError(_("Names can only contain letters, periods, dashes, and apostrophes."))
        return self.cleaned_data["name"]
    
    def save(self):
        new_user = super(OpenIDSignupForm, self).save(*args, **kwargs)
        
        ### CoLab mods here ###
        name = self.cleaned_data["name"]
        new_researcher, created = Researcher.objects.get_or_create(user=new_user)
        new_researcher.name = name
        new_researcher.save()
        
        return new_user

class UserForm(forms.Form):
    
    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super(UserForm, self).__init__(*args, **kwargs)


class AccountForm(UserForm):
    
    def __init__(self, *args, **kwargs):
        super(AccountForm, self).__init__(*args, **kwargs)
        try:
            self.account = Account.objects.get(user=self.user)
        except Account.DoesNotExist:
            self.account = Account(user=self.user)


class AddEmailForm(UserForm):
    
    email = forms.EmailField(
        label = _("Email"),
        required = True,
        widget = forms.TextInput(attrs={"size":"30"})
    )
    
    def clean_email(self):
        value = self.cleaned_data["email"]
        errors = {
            "this_account": _("This e-mail address already associated with this account."),
            "different_account": _("This e-mail address already associated with another account."),
        }
        if UNIQUE_EMAIL:
            try:
                email = EmailAddress.objects.get(email__iexact=value)
            except EmailAddress.DoesNotExist:
                return value
            if email.user == self.user:
                raise forms.ValidationError(errors["this_account"])
            raise forms.ValidationError(errors["different_account"])
        else:
            try:
                EmailAddress.objects.get(user=self.user, email__iexact=value)
            except EmailAddress.DoesNotExist:
                return value
            raise forms.ValidationError(errors["this_account"])
    
    def save(self):
        return EmailAddress.objects.add_email(self.user, self.cleaned_data["email"])


class ChangePasswordForm(UserForm):
    
    oldpassword = forms.CharField(
        label = _("Current Password"),
        widget = forms.PasswordInput(render_value=False)
    )
    password1 = forms.CharField(
        label = _("New Password"),
        widget = forms.PasswordInput(render_value=False)
    )
    password2 = forms.CharField(
        label = _("New Password (again)"),
        widget = forms.PasswordInput(render_value=False)
    )
    
    def clean_oldpassword(self):
        if not self.user.check_password(self.cleaned_data.get("oldpassword")):
            raise forms.ValidationError(_("Please type your current password."))
        return self.cleaned_data["oldpassword"]
    
    def clean_password2(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data["password2"]
    
    def save(self):
        self.user.set_password(self.cleaned_data["password1"])
        self.user.save()


class SetPasswordForm(UserForm):
    
    password1 = forms.CharField(
        label = _("Password"),
        widget = forms.PasswordInput(render_value=False)
    )
    password2 = forms.CharField(
        label = _("Password (again)"),
        widget = forms.PasswordInput(render_value=False)
    )
    
    def clean_password2(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data["password2"]
    
    def save(self):
        self.user.set_password(self.cleaned_data["password1"])
        self.user.save()


class ResetPasswordForm(forms.Form):
    
    email = forms.EmailField(
        label = _("Email"),
        required = True,
        widget = forms.TextInput(attrs={"size":"30"})
    )
    
    def clean_email(self):
        if EmailAddress.objects.filter(email__iexact=self.cleaned_data["email"], verified=True).count() == 0:
            raise forms.ValidationError(_("Email address not verified for any user account"))
        return self.cleaned_data["email"]
    
    def save(self, **kwargs):
        
        email = self.cleaned_data["email"]
        token_generator = kwargs.get("token_generator", default_token_generator)
        
        for user in User.objects.filter(email__iexact=email):
            
            temp_key = token_generator.make_token(user)
            
            # save it to the password reset model
            password_reset = PasswordReset(user=user, temp_key=temp_key)
            password_reset.save()
            
            current_site = Site.objects.get_current()
            domain = unicode(current_site.domain)
            
            # send the password reset email
            subject = _("Password reset email sent")
            message = render_to_string("account/password_reset_key_message.txt", {
                "user": user,
                "uid": int_to_base36(user.id),
                "temp_key": temp_key,
                "domain": domain,
            })
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], priority="high")
        return self.cleaned_data["email"]


class ResetPasswordKeyForm(forms.Form):
    
    password1 = forms.CharField(
        label = _("New Password"),
        widget = forms.PasswordInput(render_value=False)
    )
    password2 = forms.CharField(
        label = _("New Password (again)"),
        widget = forms.PasswordInput(render_value=False)
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user", None)
        self.temp_key = kwargs.pop("temp_key", None)
        super(ResetPasswordKeyForm, self).__init__(*args, **kwargs)
    
    def clean_password2(self):
        if "password1" in self.cleaned_data and "password2" in self.cleaned_data:
            if self.cleaned_data["password1"] != self.cleaned_data["password2"]:
                raise forms.ValidationError(_("You must type the same password each time."))
        return self.cleaned_data["password2"]
    
    def save(self):
        # set the new user password
        user = self.user
        user.set_password(self.cleaned_data["password1"])
        user.save()
        # mark password reset object as reset
        PasswordReset.objects.filter(temp_key=self.temp_key).update(reset=True)


class ChangeTimezoneForm(AccountForm):
    
    timezone = TimeZoneField(label=_("Timezone"), required=True)
    
    def __init__(self, *args, **kwargs):
        super(ChangeTimezoneForm, self).__init__(*args, **kwargs)
        self.initial.update({"timezone": self.account.timezone})
    
    def save(self):
        self.account.timezone = self.cleaned_data["timezone"]
        self.account.save()


class ChangeLanguageForm(AccountForm):
    
    language = forms.ChoiceField(
        label = _("Language"),
        required = True,
        choices = settings.LANGUAGES
    )
    
    def __init__(self, *args, **kwargs):
        super(ChangeLanguageForm, self).__init__(*args, **kwargs)
        self.initial.update({"language": self.account.language})
    
    def save(self):
        self.account.language = self.cleaned_data["language"]
        self.account.save()


class TwitterForm(UserForm):
    username = forms.CharField(label=_("Username"), required=True)
    password = forms.CharField(
        label = _("Password"),
        required = True,
        widget = forms.PasswordInput(render_value=False)
    )
    
    def __init__(self, *args, **kwargs):
        super(TwitterForm, self).__init__(*args, **kwargs)
        self.initial.update({"username": other_service(self.user, "twitter_user")})
    
    def save(self):
        from microblogging.utils import get_twitter_password
        update_other_services(self.user,
            twitter_user = self.cleaned_data["username"],
            twitter_password = get_twitter_password(settings.SECRET_KEY, self.cleaned_data["password"]),
        )
