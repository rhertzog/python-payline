# -*- coding: utf-8 -*-
"""
Python client for the Payline SOAP API
Exceptions
"""


class InvalidCurrencyError(Exception):
    """This exception is raised when the given currency is not supported"""
    pass


class PaylineApiError(Exception):
    """This exception is raised when Payline SOAP API raises an error"""
    pass


PaylineAuthError = PaylineApiError


class ArgumentsError(Exception):
    """The api is called with wrong arguments"""
    pass