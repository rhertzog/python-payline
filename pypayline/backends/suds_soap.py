# -*- coding: utf-8 -*-
"""
Python client for the Payline SOAP API
SOAP Backends : for real usage
"""

import logging

from suds.client import Client

from pypayline.exceptions import PaylineApiError

APIError = Exception

logger = logging.getLogger(u'pypayline')


class SoapBackend(object):
    """
    Manage communication with Payline over SOAP API
    """

    def __init__(self, location='', wsdl='', http_headers=None, **kwargs):
        """initialize the soap client and get wsdl file for service definition"""
        # logging.getLogger('suds.transport').setLevel(logging.INFO)
        # logger = logging.getLogger()
        # logger.root.setLevel(logging.INFO)
        # logger.root.addHandler(logging.StreamHandler(sys.stdout))
        self.client = Client(url=wsdl, location=location, headers=http_headers)
        self.soap_client = self.client.service

    def doWebPayment(self, **data):
        """call the doWebPayment SOAP API"""
        try:
            logger.debug('> {0}'.format(data))
            response = self.soap_client.doWebPayment(**data)
            logger.debug('< {0}'.format(response))
            if response['result']['code'] != u"00000":
                raise PaylineApiError(response['result']['longMessage'])
            return response['redirectURL'], response['token']
        except APIError as err:
            raise PaylineApiError('Error: {0}: {1} -> {2}'.format(err, data, response))

    def getWebPaymentDetails(self, **data):
        """call the getWebPaymentDetails SOAP API"""
        try:
            response = self.soap_client.getWebPaymentDetails(**data)
            return response
        except APIError as err:
            raise PaylineApiError(u'Error: {0}'.format(err))

    def getPaymentRecord(self, **data):
        """call the getPaymentRecord SOAP API"""
        try:
            response = self.soap_client.getPaymentRecord(**data)
            return response
        except APIError as err:
            raise PaylineApiError('Error: {0}'.format(err))
