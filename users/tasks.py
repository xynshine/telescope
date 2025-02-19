from telescope.celery import app
from celery import shared_task
from django.core.mail import send_mail, BadHeaderError
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.conf import settings


@app.task
def send_password_reset_form_for_new_user(email):
    print('EMAIL', email)
    try:
    	user = User.objects.get(email=email)
    except User.DoesNotExist:
        print("ERROR: there isn't user with this email")
    subject = 'Активация аккаунта'
    email_from = settings.EMAIL_HOST_USER
    email_template_name = "password_reset_new_user.txt"
    c = {
        "email": user.email,
        'domain': 'chronos-system.ru',
        'site_name': 'Chronos',
        "uid": urlsafe_base64_encode(force_bytes(user.pk)),
        "user": user,
        'token': default_token_generator.make_token(user),
        'protocol': 'https',
    }
    email = render_to_string(email_template_name, c)
    try:
        send_mail(subject, email, email_from, [user.email], fail_silently=False)
    except BadHeaderError:
        print('ERROR: Invalid header found.')
