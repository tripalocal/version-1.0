from allauth.account import app_settings
from allauth.account.adapter import DefaultAccountAdapter
from django import forms

class AccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        return '/'

    def clean_password(self, value):
        min_length = app_settings.PASSWORD_MIN_LENGTH
        if len(value) < min_length:
            raise forms.ValidationError(_("Password must be a minimum of {0} "
                                          "characters.").format(min_length))
        return value
