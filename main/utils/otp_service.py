import pyotp
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

OTP_EXPIRY_SECONDS = 300  # 5 minutes
MAX_ATTEMPTS = 5

def generate_otp(email):
    """
    Generate and store OTP with secret for validation.
    """
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)

    otp = totp.now()

    cache.set(f"otp_secret_{email}", secret, timeout=OTP_EXPIRY_SECONDS)
    cache.set(f"otp_attempts_{email}", 0, timeout=OTP_EXPIRY_SECONDS)

    return otp


def verify_otp(email, user_otp):
    """
    Verify OTP and enforce attempt limits.
    """
    secret = cache.get(f"otp_secret_{email}")
    attempts = cache.get(f"otp_attempts_{email}", 0)

    if not secret:
        return False, "OTP expired or not found"

    if attempts >= MAX_ATTEMPTS:
        return False, "Too many attempts. Try again later"

    totp = pyotp.TOTP(secret)
    valid = totp.verify(user_otp)

    if valid:
        # Clear OTP & attempts after success
        cache.delete(f"otp_secret_{email}")
        cache.delete(f"otp_attempts_{email}")
        return True, "OTP verified successfully"

    # Increase failed attempts
    cache.set(f"otp_attempts_{email}", attempts + 1, timeout=OTP_EXPIRY_SECONDS)
    return False, "Invalid OTP"


def can_resend_otp(email, cooldown_seconds=60):
    last_sent = cache.get(f"otp_last_send_{email}")

    if last_sent and timezone.now() < last_sent + timedelta(seconds=cooldown_seconds):
        remaining = (last_sent + timedelta(seconds=cooldown_seconds) - timezone.now()).seconds
        return False, remaining

    cache.set(f"otp_last_send_{email}", timezone.now(), timeout=OTP_EXPIRY_SECONDS)
    return True, 0
