# -*- coding: utf-8 -*-
"""
Python client for the Payline SOAP API
Backend for unit testing
"""

from __future__ import print_function

from datetime import datetime
from decimal import Decimal
import re

from pypayline.exceptions import PaylineAuthError, PaylineApiError


TOKEN = u'3cXyapUchee8x645C6782541635718391'


class SoapMockBackend(object):
    """Mock the SOAP API client"""
    def __init__(self, *args, **kwargs):
        """
        Use dummy merchant_id = = u"12345678901234" and access_key = u"abCdeFgHiJKLmNoPqrst" in order to use this mock
        """
        self.http_headers = kwargs['http_headers']

        self.last_order = self.last_payment = None
        self.cancelled = False

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
            token = TOKEN
            host = u'https://homologation-webpayment.payline.com/webpayment/step2.do'
            return {
                'redirectURL': u'{0}?reqCode=prepareStep2&token={1}'.format(host, TOKEN),
                'token': token,
                'result': {
                    'code': u'00000',
                    'longMessage': u'Transaction approved',
                    'shortMessage': u'Transaction approved',
                }
            }

    def _handle_response(self, data):
        """return the response dict as close as possible to the real API"""

        if data['payment']['amount'] == 0:
            return self.get_response("Invalid field format : Payment Amount : Must not be null")

        if data['payment']['amount'] < 0:
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
        self.last_payment = None
        self.last_order = None
        response = self._handle_response(data)
        if response['result']['code'] == u'00000':
            self.last_payment = data['payment']
            self.last_order = data['order']
        else:
            raise PaylineApiError(response['result']['longMessage'])
        return response

    def getWebPaymentDetails(self, **data):
        """call the getWebPaymentDetails SOAP API"""
        if self.http_headers.get('Authorization', None) != u'Basic MTIzNDU2Nzg5MDEyMzQ6YWJDZGVGZ0hpSktMbU5vUHFyc3Q=':
            raise PaylineAuthError(u'Error while creating client. Err HTTP {0}'.format(401))

        # Minimalist response
        response = {
            'transaction': {
                'id': '1234567890',
                'date': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'isDuplicated': False,
                'isPossibleFraud': False,
                'fraudResult': '',
                'fraudResultDetails': '',
                'explanation': '',
                'score': 0,
                'threeDSecure': 'N',
                'externalWalletType': 'Me',
                'externalWalletCont ractNumber': '',
            },
            'payment': self.last_payment,
            'order': self.last_order,
            'result': {
                'code': u'00000',
                'longMessage': u'Transaction approved',
                'shortMessage': u'Transaction approved',
            }
        }

        if data['token'] != TOKEN:
            response = self.get_response(u"This token does not exist")

        if self.cancelled:
            response = self.get_response(u"Payment cancelled by the buyer")

        if self.last_payment is None:
            response = self.get_response(u"The consummer is not redirected on payment web pages")


        if response['result']['code'] == u'00000':
            return response
        else:
            raise PaylineApiError(response['result']['longMessage'])