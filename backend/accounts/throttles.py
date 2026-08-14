from rest_framework.throttling import AnonRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    """Tighter throttle for register/login — the two endpoints most worth
    slowing down against credential-stuffing and brute-force attempts."""

    scope = "auth"
