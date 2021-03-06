import logging
from django.contrib.auth.models import User
from django import forms
from auth.models import RepeatUserName
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext_lazy as _
from combat.models import Contestant
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import password_validation
logger = logging.getLogger('myauth')


class DuplicateUserException(Exception):
    pass


class PasswordForm(PasswordChangeForm):
    # class Meta:
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(
            attrs={
                'autofocus': True,
                'class': 'form-control'
            }
        ),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control'
            }
        ),
    )
    old_password = forms.CharField(
        label=_("Old password"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'autofocus': True,
                'class': 'form-control'
            }
        ),
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Contestant
        fields = ('nickname', 'github', 'linkedin', 'facebook')
        widgets = {
            'nickname': forms.TextInput(
                attrs={
                    'style': 'width: 100%;',
                }
            ),
            'github': forms.URLInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Optional',
                }
            ),
            'linkedin': forms.URLInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Optional',
                }
            ),
            'facebook': forms.URLInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Optional',
                }
            )
        }

    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname')
        if (not bool(nickname)) or (not bool(nickname.strip())):
            raise forms.ValidationError('Nickname cannot be empty.')
        return nickname


class UserSignupForm(UserCreationForm):

    # error_css_class = 'error'

    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Email',
                'pattern': '[a-z,A-Z,0-9,_,\.]+@[a-z,A-Z,0-9,_,\.]+',
                'data-valid-min': '8',
            }
        )
    )

    nickname = forms.CharField(
        max_length=31,
        required=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'nickname',
            }
        )
    )

    password1 = forms.CharField(
        label='Password',
        required=True,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Password',
                'minlength': '8',
            }
        )
    )

    password2 = forms.CharField(
        label='Password confirmation',
        required=True,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Confirm password',
                'minlength': '8',
            }
        )
    )

    field_order = ['email', 'nickname', 'password1', 'password2']

    class Meta:
        model = User
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email has been taken.')
        return email

    def save(self, commit=True):
        instance = super(UserSignupForm, self).save(commit=False)
        email = instance.email
        name = email[: email.find('@')].replace('.', '').lower()
        try:
            repeat = RepeatUserName.objects.get(name=name)
            name += '.{}'.format(repeat.count + 1)
            if name and User.objects.filter(username=name).exists():
                raise DuplicateUserException

            repeat.count += 1
            repeat.save()

        except DuplicateUserException:
            raise('Duplicate Username, this should NEVER happened!')

        except RepeatUserName.DoesNotExist as err:
            logger.warning(err)
            RepeatUserName(name=name).save()
        except Exception as err:
            logger.warning(err)
            RepeatUserName(name=name).save()

        instance.username = name
        if commit:
            instance.save()
            nickname = self.cleaned_data.get('nickname') or name
            instance.contestant.nickname = nickname
            instance.contestant.save()

        return instance


class UserLoginForm(forms.Form):

    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Email',
                'pattern': '[a-z,A-Z,0-9,_,\.]+@[a-z,A-Z,0-9,_,\.]+',
                'data-valid-min': '8',
            }
        )
    )

    password = forms.CharField(
        label='Password',
        required=True,
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Password',
                'minlength': '8',
            }
        )
    )

    error_messages = {
        'invalid_login': _(
            "Please enter a correct email and password. Note that both "
            "fields may be case-sensitive."
        ),
        'inactive': _("This account is inactive."),
        'bang': "您的帳號已被禁用，請聯絡網站管理員"
    }

    def clean(self):
        email = self.cleaned_data.get('email')
        raw_password = self.cleaned_data.get('password')

        if email and raw_password:
            try:
                user = User.objects.get(email=email)
                if not user.is_active:
                    raise forms.ValidationError(self.error_messages['bang'])
                auth_user = authenticate(username=user.username, password=raw_password)
                if not auth_user:
                    raise forms.ValidationError(self.error_messages['invalid_login'])
                else:
                    self.cleaned_data['username'] = user.username
            except User.DoesNotExist:
                raise forms.ValidationError(self.error_messages['invalid_login'])
            # except Exception as err:
            #     logger.warning(err)
            #     raise forms.ValidationError(self.error_messages['invalid_login'])

        return self.cleaned_data
