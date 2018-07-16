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

LAST_DATA = {

}

LAST_PAYMENT_DATA = {

}

class SoapMockBackend(object):
    """Mock the SOAP API client"""

    def __init__(self, *args, **kwargs):
        """
        Use dummy merchant_id = = u"12345678901234" and access_key = u"abCdeFgHiJKLmNoPqrst" in order to use this mock
        """
        self.http_headers = kwargs['http_headers']
        self.cancelled = False
        self.api_name = kwargs.pop('api_name')
        # Only the required data
        self.services = {
            self.api_name: {
                u'ports': {
                    self.api_name: {
                        u'location': u'http://host/V4/services/{0}'.format(self.api_name),
                    }
                }
            }
        }
        self.doWebPaymentData = LAST_PAYMENT_DATA

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
        LAST_PAYMENT_DATA.clear()
        LAST_PAYMENT_DATA.update(**data)
        LAST_DATA.clear()
        response = self._handle_response(data)
        if response['result']['code'] == u'00000':
            LAST_DATA['last_payment'] = data['payment']
            LAST_DATA['last_order'] = data['order']
        else:
            raise PaylineApiError(response['result']['longMessage'])
        return response['redirectURL'], response['token']

    def getWebPaymentDetails(self, **data):
        """call the getWebPaymentDetails SOAP API"""
        if self.http_headers.get('Authorization', None) != u'Basic MTIzNDU2Nzg5MDEyMzQ6YWJDZGVGZ0hpSktMbU5vUHFyc3Q=':
            raise PaylineAuthError(u'Error while creating client. Err HTTP {0}'.format(401))

        is_possible_fraud = False
        if LAST_DATA['last_payment']["amount"] >= 1000000:
            is_possible_fraud = True

        card_country = u'FRA'
        ret_code = '00000'  # Approved
        transaction_id = '1234567890'
        no_card_data = False
        paypal_data = ''

        if LAST_DATA and LAST_DATA['last_payment']["amount"] == 1001:
            ret_code = '01001'  # Approved
        elif LAST_DATA and LAST_DATA['last_payment']["amount"] == 2500:
            ret_code = '02500'    # Approved
        elif LAST_DATA and LAST_DATA['last_payment']["amount"] == 2501:
            ret_code = '02501'  # Approved
        elif LAST_DATA and LAST_DATA['last_payment']["amount"] == 12345:
            LAST_DATA['contractNumber'] = None
            LAST_DATA['last_payment'] = None
            ret_code = '01100'  # Error
        elif LAST_DATA and LAST_DATA['last_payment']["amount"] == 23456:
            card_country = u'ZZZ'
        elif LAST_DATA and LAST_DATA['last_payment']["amount"] == 23457:
            # will fallback to analyze partner data
            no_card_data = True
            paypal_data = '''{
                "login": "paypal_customer@example.com",
                "accountCountryCode": "BE",
                "referenceID": "%s"
            }''' % transaction_id
        elif LAST_DATA and LAST_DATA['last_payment']["amount"] == 23458:
            # will cause error with Paypal mock
            transaction_id = u"9876543210"
            no_card_data = True

        # Minimalist response
        response = {
            'transaction': {
                'id': transaction_id,
                'date': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'isDuplicated': False,
                'isPossibleFraud': is_possible_fraud,
                'fraudResult': '',
                'fraudResultDetails': '',
                'explanation': '',
                'score': 0,
                'threeDSecure': 'N',
                'externalWalletType': 'Me',
                'externalWalletContractNumber': '',
                'partnerAdditionalData': paypal_data,
            },
            'payment': LAST_DATA.get('last_payment', None),
            'order': LAST_DATA.get('last_order', None),
            'result': {
                'code': ret_code,
                'longMessage': u'Transaction approved',
                'shortMessage': u'Transaction approved',
            },
            'card': {
                'type': u'CB',
                'number': u'12345XXXXXXXX',
                'expirationDate': u'1217'
            },
            'numberOfAttempt': u'1',
            'privateDataList': None,
            'media': u'Computer',
            'extendedCard': {
                'product': u'SUPERCARD CARD',
                'network': u'SUPERCARD',
                'country': card_country,
                'isCvd': None,
                'type': u'SUPERCARD',
                'bank': u'1234 - THE BANK'
            },
            'authentication3DSecure': {
                'md': None, 'xid': None, 'eci': None, 'cavvAlgorithm': None, 'cavv': None, 'vadsResult': None
            },
            'authorization': {'date': u'10/06/2016 10:21', 'number': u'AB12'}
        }

        if no_card_data:
            response.pop('extendedCard')

        if data['token'] != TOKEN:
            response = self.get_response(u"This token does not exist")

        if self.cancelled:
            response = self.get_response(u"Payment cancelled by the buyer")

        if 'last_payment' not in LAST_DATA:
            response = self.get_response(u"The consummer is not redirected on payment web pages")

        return response

    def getPaymentRecord(self, **data):
        """call the doWebPayment SOAP API"""

        payment_record_id = data['paymentRecordId']

        response = {
            'result': {
                'code': u'00000',
                'longMessage': u'Transaction approved',
                'shortMessage': u'Transaction approved',
            },
            'recurring': {
                'firstAmount': 1000,
                'amount': 1000,
                'billingCycle': 40,
                'startDate': '06/06/2016',
                'billingLeft': 3,
                'billingDay': '01',
            },
            'isDisabled': 0,
            'disabledDate': '',
            'billingRecordList': [
                {
                    'date': u"06/06/2016",
                    'amount': 1000,
                    'status': 0,
                    'return': {
                        'code': '00000',
                        'longMessage': u'Transaction approved',
                        'shortMessage': u'Transaction approved',
                    },
                    'transaction': {
                        'id': '123456789',
                        'isPossibleFraud': False,
                        'isDuplicated': False,
                        'date': u"06/06/2016",
                    },
                    'authorization': {
                        'number': '123456789',
                        'date': u"06/06/2016",
                    }
                }
            ],
            'order': {
                'ref': payment_record_id,  # for something simple return the paymentRecordId arg
            },
            'privateDataList': {},
            'walletId': '',
        }

        return response
