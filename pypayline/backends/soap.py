# -*- coding: utf-8 -*-
"""
Python client for the Payline SOAP API
SOAP Backends : for real usage
"""

from __future__ import print_function

from urllib2 import HTTPError

from pysimplesoap.client import SoapClient, SoapFault

from pypayline.exceptions import PaylineAuthError, PaylineApiError


class SoapBackend(object):
    """
    Manage communication with Payline over SOAP API
    """

    def __init__(self, *args, **kwargs):
        """initialize the soap client and get wsdl file for service definition"""
        self.soap_client = SoapClient(*args, **kwargs)
        self.services = self.soap_client.services

    def doWebPayment(self, **data):
        """call the doWebPayment SOAP API"""
        try:
            response = self.soap_client.doWebPayment(**data)
            if response['result']['code'] != u"00000":
                raise PaylineApiError(response['result']['longMessage'])
            return response['redirectURL']
        except SoapFault as err:
            raise PaylineApiError(unicode(err))
        except HTTPError as err:
            raise PaylineAuthError(u'Error while creating client. Err HTTP {0}'.format(err.code))

