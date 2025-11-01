import re
from .profanity_checker import has_profanity

RESERVED_SUBDOMAINS = {
    "admin","root","owner","support","help","secure","login",
    "accounts","auth","dashboard","system","internal",
    "api","cdn","store","shop","checkout","billing","payment",
    "home","www","ftp","email","mail","test","demo","beta",
    "facebook","google","amazon","daraz","bangladesh","microsoft",
}

def is_valid_subdomain(value: str):
    value = value.strip().lower()

    if len(value) < 3 or len(value) > 50:
        return False, "Subdomain must be 3 to 50 characters"

    if has_profanity(value):
        return False, "Subdomain contains inappropriate words"

    if value in RESERVED_SUBDOMAINS:
        return False, "This subdomain is reserved"

    if value.startswith("-") or value.endswith("-"):
        return False, "Subdomain cannot start or end with hyphen"

    if "--" in value:
        return False, "Subdomain cannot contain consecutive hyphens"

    if not re.match(r"^[a-z0-9-]+$", value):
        return False, "Only lowercase letters, numbers, hyphens allowed"

    if value.isdigit():
        return False, "Subdomain cannot be only numbers"

    if len(set(value)) == 1:
        return False, "Subdomain cannot be repetitive characters"

    return True, ""
