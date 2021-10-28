# -*- coding: utf-8 -*-
"""
Python client for the Payline SOAP API
unit tests
python tests.py [+soap]
if +soap -> Use the real SOAP API
"""

from datetime import datetime
from decimal import Decimal
import logging
import re
import sys
import unittest

from pypayline.backends.mock import SoapMockBackend
from pypayline.client import WebPaymentAPI as WebPaymentAPIBase, DirectPaymentAPI as DirectPaymentAPIBase
from pypayline.exceptions import InvalidCurrencyError, PaylineApiError, PaylineAuthError


logger = logging.getLogger('pypayline')
logger.addHandler(logging.StreamHandler())


def use_mock():
    """if +soap option is given in command line activate this mode"""
    soap_option = '+soap'
    if soap_option in sys.argv:
        # remove it from command line for regular unit test options
        sys.argv.remove(soap_option)
        return False
    return True


USE_MOCK = use_mock()


class WebPaymentAPI(WebPaymentAPIBase):
    """Class for calling the payline services"""
    backend_class = SoapMockBackend if USE_MOCK else WebPaymentAPIBase.backend_class


class DirectPaymentAPI(DirectPaymentAPIBase):
    """Class for calling the payline services"""
    backend_class = SoapMockBackend if USE_MOCK else DirectPaymentAPIBase.backend_class


class SoapApiTestCase(unittest.TestCase):

    def setUp(self):
        """initialize mocks"""
        logger.setLevel(logging.INFO)

        if USE_MOCK:
            self.merchant_id, self.access_key, self.contract_number = u"12345678901234", u"abCdeFgHiJKLmNoPqrst", u"1234567"
        else:
            try:
                from payline_secrets import MERCHANT_ID, ACCESS_KEY, CONTRACT_NUMBER
                self.merchant_id, self.access_key, self.contract_number = MERCHANT_ID, ACCESS_KEY, CONTRACT_NUMBER
            except ImportError:
                print(u"""
                    You must create a payline_secrets.py in your path and defines 3 globals
                    MERCHANT_ID = "1234567890"
                    ACCESS_KEY = "DJMESHXYou6LmjQFdH"
                    CONTRACT_NUMBER = "123456"
                """)
                raise

    def tearDown(self):
        """clean"""
        self.merchant_id, self.access_key, self.contract_number = u"12345678901234", u"abCdeFgHiJKLmNoPqrst", u"1234567"

    @staticmethod
    def get_buyer():
        return {
            'lastName': 'Doe',
            'firstName': 'John',
            'email': 'john.doe@apidev.fr',
        }

    def test_header(self):
        """check the authorization header is filled"""
        client = WebPaymentAPI(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )
        self.assertTrue(u'Authorization' in client.http_headers)
        self.assertTrue(re.match("Basic [\w=]+", client.http_headers[u'Authorization']))

    def test_call_api_eur(self):
        """check call API in EUR"""

        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = WebPaymentAPI(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )

        try:
            redirect_url, token = client.do_web_payment(
                amount=Decimal("12.50"), currency=u"EUR", order_ref=dummy_order_ref, country="FR",
                return_url='https://apidev.fr/success/', cancel_url='https://apidev.fr/cancel/',
                notification_url='https://apidev.fr/notify/', buyer=self.get_buyer()
            )
        except Exception as err:
            self.assertEqual(err, '')
        self.assertNotEqual(redirect_url, None)

        if USE_MOCK:
            res_code, is_transaction_ok, order_ref, amount, currency, raw_data = client.get_web_payment_details(token)
            self.assertEqual(res_code, "00000")
            self.assertEqual(is_transaction_ok, True)
            self.assertEqual(amount, Decimal("12.50"))
            self.assertEqual(currency, u"EUR")
            self.assertEqual(order_ref, dummy_order_ref)
            self.assertEqual(type(raw_data), dict)

    def test_call_api_usd(self):
        """check call API in USD"""

        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = WebPaymentAPI(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )

        redirect_url, token = client.do_web_payment(
            amount=Decimal("12.50"), currency=u"USD", order_ref=dummy_order_ref,
            return_url='http://freexian.com/success/', cancel_url='http://freexian.com/cancel/',
            buyer=self.get_buyer()
        )
        self.assertNotEqual(redirect_url, None)

        if USE_MOCK:
            res_code, is_transaction_ok, order_ref, amount, currency, raw_data = client.get_web_payment_details(token)
            self.assertEqual(res_code, "00000")
            self.assertEqual(is_transaction_ok, True)
            self.assertEqual(amount, Decimal("12.50"))
            self.assertEqual(currency, u"USD")
            self.assertEqual(order_ref, dummy_order_ref)
            self.assertEqual(type(raw_data), dict)

    def test_call_api_cache(self):
        """check call API with cache set"""

        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = WebPaymentAPI(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True, cache=u"WebPaymentAPI"
        )

        redirect_url, token = client.do_web_payment(
            amount=Decimal("12.50"), currency=u"EUR", order_ref=dummy_order_ref,
            return_url='http://freexian.com/success/', cancel_url='http://freexian.com/cancel/',
            buyer=self.get_buyer()
        )
        self.assertNotEqual(redirect_url, None)

    def test_call_api_recurring(self):
        """check call API with recurring"""
        logger.setLevel(logging.DEBUG)
        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = WebPaymentAPI(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )

        redirect_url, token = client.do_web_payment(
            amount=Decimal("12.50"), currency=u"USD", order_ref=dummy_order_ref,
            recurring_period_in_months=3, recurring_times=4, buyer=self.get_buyer(),
            return_url='http://freexian.com/success/', cancel_url='http://freexian.com/cancel/'
        )
        self.assertNotEqual(redirect_url, None)

        if USE_MOCK:
            res_code, is_transaction_ok, order_ref, amount, currency, raw_data = client.get_web_payment_details(token)
            self.assertEqual(res_code, '00000')
            self.assertEqual(is_transaction_ok, True)
            self.assertEqual(amount, Decimal("12.50"))
            self.assertEqual(currency, u"USD")
            self.assertEqual(order_ref, dummy_order_ref)
            self.assertEqual(type(raw_data), dict)

    def test_call_api_invalid_amount(self):
        """Check error if wrong value"""
        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = WebPaymentAPI(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )

        self.assertRaises(PaylineApiError, client.do_web_payment,
            amount=Decimal("0.00"), currency=u"EUR", order_ref=dummy_order_ref, buyer=self.get_buyer(),
            return_url='http://freexian.com/success/', cancel_url='http://freexian.com/cancel/'
        )

    def test_call_api_negative_amount(self):
        """Check error if wrong value"""
        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = WebPaymentAPI(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )

        self.assertRaises(PaylineApiError, client.do_web_payment,
            amount=Decimal("-10.00"), currency=u"EUR", order_ref=dummy_order_ref, buyer=self.get_buyer(),
            return_url='http://freexian.com/success/', cancel_url='http://freexian.com/cancel/'
        )

    def test_call_api_invalid_currency(self):
        """Check error if wrong currency"""
        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = WebPaymentAPI(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )

        self.assertRaises(
            InvalidCurrencyError, client.do_web_payment,
            amount=Decimal("10.00"), currency=u"BRA", order_ref=dummy_order_ref,
            return_url='http://freexian.com/success/', cancel_url='http://freexian.com/cancel/'
        )

    def test_call_api_invalid_order_ref(self):
        """Check error if wrong order_ref"""
        dummy_order_ref = u''

        client = WebPaymentAPI(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )

        self.assertRaises(
            PaylineApiError, client.do_web_payment,
            amount=Decimal("-10.00"), currency=u"EUR", order_ref=dummy_order_ref, buyer=self.get_buyer(),
            return_url='http://freexian.com/success/', cancel_url='http://freexian.com/cancel/'
        )

    def test_call_api_invalid_return_url(self):
        """Check error if wrong return url"""
        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = WebPaymentAPI(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )

        self.assertRaises(
            PaylineApiError, client.do_web_payment,
            amount=Decimal("-10.00"), currency=u"EUR", order_ref=dummy_order_ref, buyer=self.get_buyer(),
            return_url='', cancel_url='http://freexian.com/cancel/'
        )

    def test_call_api_invalid_cancel_url(self):
        """Check error if wrong cancel url"""
        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = WebPaymentAPI(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )

        self.assertRaises(
            PaylineApiError, client.do_web_payment,
            amount=Decimal("-10.00"), currency=u"EUR", order_ref=dummy_order_ref, buyer=self.get_buyer(),
            return_url='http://freexian.com/success/', cancel_url='/cancel/'
        )

    def test_invalid_contract(self):
        """Check error if Invalid contract"""
        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = WebPaymentAPI(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number='',
            homologation=True, cache=False
        )

        self.assertRaises(
            PaylineApiError, client.do_web_payment,
            amount=Decimal("-10.00"), currency=u"EUR", order_ref=dummy_order_ref, buyer=self.get_buyer(),
            return_url='http://freexian.com/success/', cancel_url='/cancel/'
        )

    def test_invalid_merchant(self):
        """Check error if Invalid merchant Id"""
        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = WebPaymentAPI(
            merchant_id=u"1234", access_key=self.access_key, contract_number=self.contract_number,
            homologation=True, cache=False
        )

        self.assertRaises(
            PaylineAuthError, client.do_web_payment,
            amount=Decimal("-10.00"), currency=u"EUR", order_ref=dummy_order_ref,
            return_url='http://freexian.com/success/', cancel_url='/cancel/', buyer=self.get_buyer()
        )

    def test_invalid_access_key(self):
        """Check error if Invalid access key"""
        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')
        client = WebPaymentAPI(
            merchant_id=self.merchant_id, access_key=u"abcd", contract_number=self.contract_number,
            homologation=True, cache=False
        )

        self.assertRaises(
            PaylineAuthError, client.do_web_payment,
            amount=Decimal("-10.00"), currency=u"EUR", order_ref=dummy_order_ref,
            return_url='http://freexian.com/success/', cancel_url='/cancel/', buyer=self.get_buyer()
        )

    def test_call_api_eur_not_visited(self):
        """check call API in EUR get_web_payment_details should fail if not visited"""

        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = WebPaymentAPI(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )

        redirect_url, token = client.do_web_payment(
            amount=Decimal("12.50"), currency=u"EUR", order_ref=dummy_order_ref, buyer=self.get_buyer(),
            return_url='http://freexian.com/success/', cancel_url='http://freexian.com/cancel/'
        )
        self.assertNotEqual(redirect_url, None)

        if USE_MOCK:
            client.backend.cancelled = True

        returned_values = client.get_web_payment_details(token + "AAA")
        self.assertNotEqual(returned_values[0], '00000')

    def test_call_api_wrong_token(self):
        """check call API in EUR get_web_payment_details should fail if wrong token"""

        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = WebPaymentAPI(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )

        redirect_url, token = client.do_web_payment(
            amount=Decimal("12.50"), currency=u"EUR", order_ref=dummy_order_ref, buyer=self.get_buyer(),
            return_url='http://freexian.com/success/', cancel_url='http://freexian.com/cancel/'
        )
        self.assertNotEqual(redirect_url, None)

        returned_values = client.get_web_payment_details(token + "AAA")
        self.assertNotEqual(returned_values[0], '00000')

    def test_call_api_payment_record(self):
        """check call API with recurring"""
        logger.setLevel(logging.DEBUG)

        if USE_MOCK:
            client = DirectPaymentAPI(
                merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
                homologation=True
            )

            result_code, order_ref, amount, data = client.get_payment_record(
                self.contract_number, '12345'
            )

            self.assertTrue(result_code, '00000')
            self.assertTrue(amount, Decimal(10))
            self.assertTrue(order_ref, '1')
            self.assertTrue(type(data) is dict)


if __name__ == '__main__':
    unittest.main()
