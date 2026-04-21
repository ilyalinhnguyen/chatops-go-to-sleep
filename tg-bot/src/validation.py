"""Input validation for bot commands (K8s-style names, integers)."""

import re

# RFC 1123 DNS label (namespace, deployment name, etc.)
_K8S_DNS_LABEL = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$")
_MAX_DNS_LABEL_LEN = 63


def is_valid_k8s_dns_label(s: str) -> bool:
    if not s or len(s) > _MAX_DNS_LABEL_LEN:
        return False
    return bool(_K8S_DNS_LABEL.match(s))


def parse_nonneg_int_digits_only(text: str | None) -> int | None:
    """Non-negative integer: ASCII digits only, no words, no decimals, no spaces inside."""
    if text is None:
        return None
    s = text.strip()
    if not s:
        return None
    if not s.isdigit():
        return None
    return int(s)


def parse_nonneg_int_for_command_token(token: str) -> int | None:
    """Same as parse_nonneg_int_digits_only but for a single token (e.g. /scale ... 2)."""
    return parse_nonneg_int_digits_only(token)
