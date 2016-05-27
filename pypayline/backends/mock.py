# -*- coding: utf-8 -*-
"""
Python client for the Payline SOAP API
Backend for unit testing
"""

from __future__ import print_function

from decimal import Decimal
import re

from pypayline.exceptions import PaylineAuthError, PaylineApiError


class SoapMockBackend(object):
    """Mock the SOAP API client"""
    def __init__(self, *args, **kwargs):
        """
        Use dummy merchant_id = = u"12345678901234" and access_key = u"abCdeFgHiJKLmNoPqrst" in order to use this mock
        """
        self.http_headers = kwargs['http_headers']

        # Only the required data
        self.services = {
            u'WebPaymentAPI': {
                u'ports': {
                    u'WebPaymentAPI': {
                        u'location': u'http://host/V4/services/WebPaymentAPI',
                    }
                }
            }
        }

    def get_response(self, error=None):
        if self.http_headers.get('Authorization', None) != u'Basic MTIzNDU2Nzg5MDEyMzQ6YWJDZGVGZ0hpSktMbU5vUHFyc3Q=':
            raise PaylineAuthError(u'Error while creating client. Err HTTP {0}'.format(401))

        if error:
            return {
                'redirectURL': None,
                'token': None,
                'result': {
                    'code': u'02305',
                    'longMessage': error,
                    'shortMessage': u"Invalid Transaction",
                }
            }
        else:
            token = u'3cXyapUchee8x645C6782541635718391'
            host = u'https://homologation-webpayment.payline.com/webpayment/step2.do'
            return {
                'redirectURL': u'{0}?reqCode=prepareStep2&token={1}'.format(host, token),
                'token': token,
                'result': {
                    'code': u'00000',
                    'longMessage': u'Transaction approved',
                    'shortMessage': u'Transaction approved',
                }
            }

    def _handle_response(self, data):
        """return the response dict as close as possible to the real API"""
        if data['payment']['amount'] == Decimal("0"):
            return self.get_response("Invalid field format : Payment Amount : Must not be null")

        if data['payment']['amount'] < Decimal("0"):
            return self.get_response("Invalid field format : Payment Amount : Must be numeric(12), ex : 15078")

        if data['payment']['contractNumber'] == "" or len(data['payment']['contractNumber']) > 50:
            return self.get_response("Invalid field format : Order Reference : Max length 50 characters")

        if data['returnURL'] == "" or not re.match('https?://', data['returnURL']):
            return self.get_response("Invalid field format : Return URL : Must be an https:// or http:// url (max length : 255)")

        if data['cancelURL'] == "" or not re.match('https?://', data['cancelURL']):
            return self.get_response(
                "Invalid field format : Cancel URL : Must be an https:// or http:// url (max length : 255)")

        return self.get_response(error=None)

    def doWebPayment(self, **data):
        """call the doWebPayment SOAP API"""
        response = self._handle_response(data)

        if response['result']['code'] != u"00000":
            raise PaylineApiError(response['result']['longMessage'])
        return response['redirectURL']
