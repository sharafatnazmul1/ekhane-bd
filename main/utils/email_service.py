from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import re
from disposable_email_domains import blocklist
import dns.resolver

DEFAULT_FROM = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@yourdomain.com")

def send_email(subject, to, template_name, context):
    """
    Send HTML email with plain text fallback.
    """
    html_message = render_to_string(template_name, context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        DEFAULT_FROM,
        [to],
        html_message=html_message,
    )


def send_otp_email(email, otp):
    """
    Shortcut specifically for OTP email.
    """
    return send_email(
        subject="Verify Your Email",
        to=email,
        template_name="emails/otp_email.html",
        context={"otp": otp},
    )





def is_valid_email_format(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


def domain_has_mx(domain):
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except Exception:
        return False


def is_disposable_email(email):
    domain = email.split("@")[-1].lower()
    return domain in blocklist


def is_real_email(email):
    # basic pattern check
    if not is_valid_email_format(email):
        return False, "Invalid email format"

    # block disposable emails
    if is_disposable_email(email):
        return False, "Disposable email not allowed"

    domain = email.split("@")[-1]

    # MX record check
    if not domain_has_mx(domain):
        return False, "Email domain has no mail server (invalid email)"

    # Deep validation (optional but heavy — keep off for now)
    # if not validate_email(email, verify=True):
    #     return False, "Mailbox does not exist"

    return True, ""

