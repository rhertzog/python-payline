# -*- coding: utf-8 -*-
"""
Python client for the Payline SOAP API
SOAP Backends : for real usage
"""

from __future__ import print_function

import logging
from urllib2 import HTTPError

from pysimplesoap.client import SoapClient, SoapFault

from pypayline.exceptions import PaylineAuthError, PaylineApiError


logger = logging.getLogger(u'pypayline')


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
            logger.debug('> {0}'.format(data))
            response = self.soap_client.doWebPayment(**data)
            logger.debug('< {0}'.format(response))
            if response['result']['code'] != u"00000":
                raise PaylineApiError(response['result']['longMessage'])
            return response['redirectURL'], response['token']
        except SoapFault as err:
            raise PaylineApiError(unicode(err))
        except HTTPError as err:
            raise PaylineAuthError(u'Error while creating client. Err HTTP {0}'.format(err.code))

    def getWebPaymentDetails(self, **data):
        """call the getWebPaymentDetails SOAP API"""
        try:
            response = self.soap_client.getWebPaymentDetails(**data)
            return response
        except SoapFault as err:
            raise PaylineApiError(unicode(err))
        except HTTPError as err:
            raise PaylineAuthError(u'Error while creating client. Err HTTP {0}'.format(err.code))

