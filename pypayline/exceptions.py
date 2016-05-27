# -*- coding: utf-8 -*-
"""Python client for the Payline SOAP API"""


class InvalidCurrencyError(Exception):
    """This exception is raised when the given currency is not supported"""
    pass


class PaylineError(Exception):
    """This exception is raised when Payline SOAP APi raises an error"""
    pass
