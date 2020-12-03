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
