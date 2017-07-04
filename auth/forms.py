from django.contrib.auth.models import User
from django import forms
from auth.models import RepeatUser
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import ugettext_lazy as _


class DuplicateUserException(Exception):
    pass


class UserSignupForm(UserCreationForm):

    # error_css_class = 'error'

    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Email',
                'pattern': '[a-z,A-Z,0-9,_]+@[a-z,A-Z]+\.[a-z,A-Z]+',
                'data-valid-min': '8',
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
        name = email[: email.find('@')]
        try:
            repeat = RepeatUser.objects.get(name=name)
            name += '.{}'.format(repeat.count + 1)
            if name and User.objects.filter(username=name).exists():
                raise DuplicateUserException

            repeat.count += 1
            repeat.save()

        except DuplicateUserException:
            raise('Duplicate Username, this should NEVER happened!')
        except RepeatUser.DoesNotExist as err:
            print('@@@@@', err)
            RepeatUser(name=name).save()
        except Exception as err:
            print(err)
            RepeatUser(name=name).save()

        instance.username = name
        if commit:
            instance.save()

        return instance


class UserLoginForm(forms.Form):
    email = forms.EmailField(
        max_length=254,
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Email',
                'pattern': '[a-z,A-Z,0-9,_]+@[a-z,A-Z]+\.[a-z,A-Z]+',
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
    }

    def clean(self):
        email = self.cleaned_data.get('email')
        raw_password = self.cleaned_data.get('password')
        # print(email, raw_password)

        if email and raw_password:
            try:
                user = User.objects.get(email=email)
                auth_user = authenticate(username=user.username, password=raw_password)
                if not auth_user:
                    raise forms.ValidationError(self.error_messages['invalid_login'])
                else:
                    self.cleaned_data['username'] = user.username
            except User.DoesNotExist:
                raise forms.ValidationError(self.error_messages['invalid_login'])
            except Exception as err:
                print(err)
                raise forms.ValidationError(self.error_messages['invalid_login'])

        return self.cleaned_data
