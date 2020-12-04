"""
Gemeaux specific exceptions
"""


class ImproperlyConfigured(Exception):
    """
    When the configuration is a problem
    """


class TemplateError(Exception):
    """
    When there's an issue with templating
    """


class BadRequestException(Exception):
    """
    When the client sends a bad request.
    """


class TimeoutException(Exception):
    """
    When the server needs to close the connection without returning a response.
    """


class ProxyRequestRefusedException(Exception):
    """
    When you refuse a proxy request.
    """
