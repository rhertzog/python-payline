# -*- coding: utf-8 -*-
"""
Python client for the Payline SOAP API
unit tests
python tests.py [soap]
if soap -> Use the real SOAP API
"""

from datetime import datetime
from decimal import Decimal
import re
import sys
import unittest

from pypayline.backends.mock import SoapMockBackend
from pypayline.client import PaylineClient as PaylineClientBase
from pypayline.exceptions import InvalidCurrencyError, PaylineApiError, PaylineAuthError


def use_mock():
    """if +soap option is given in command line activate this mode"""
    soap_option = '+soap'
    if soap_option in sys.argv:
        # remove it from command line for regular unit test options
        sys.argv.remove(soap_option)
        return False
    return True


USE_MOCK = use_mock()


class PaylineClient(PaylineClientBase):
    """Class for calling the payline services"""
    backend_class = SoapMockBackend if USE_MOCK else PaylineClientBase.backend_class


class SoapApiTestCase(unittest.TestCase):

    def setUp(self):
        """initialize mocks"""
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

    def test_wsdl(self):
        """check the wsdl is patched correctly"""
        client = PaylineClient(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )
        location = u'https://homologation.payline.com'
        self.assertTrue(
            client.backend.services['WebPaymentAPI']['ports']['WebPaymentAPI']['location'].find(location) == 0
        )

    def test_wsdl_service(self):
        """check the service wsdl is patched correctly"""
        client = PaylineClient(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=False, cache=None
        )
        location = u'https://services.payline.com'
        self.assertTrue(
            client.backend.services['WebPaymentAPI']['ports']['WebPaymentAPI']['location'].find(location) == 0
        )

    def test_wsdl_cache(self):
        """check the service wsdl is patched correctly"""
        merchant_id, access_key, contract_number = u"12345678901234", u"abCdeFgHiJKLmNoPqrst", u"1234567"
        client = PaylineClient(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True, cache=u"WebPaymentAPI"
        )
        location = u'https://homologation.payline.com'
        self.assertTrue(
            client.backend.services['WebPaymentAPI']['ports']['WebPaymentAPI']['location'].find(location) == 0
        )

    def test_header(self):
        """check the authorization header is filled"""
        client = PaylineClient(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )
        self.assertTrue(u'Authorization' in client.http_headers)
        self.assertTrue(re.match("Basic [\w=]+", client.http_headers[u'Authorization']))

    def test_call_api_eur(self):
        """check call API in EUR"""

        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = PaylineClient(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )

        redirect_url = client.do_web_payment(
            amount=Decimal("12.50"), currency=u"EUR", order_ref=dummy_order_ref,
            return_url='http://freexian.com/success/', cancel_url='http://freexian.com/cancel/'
        )
        self.assertNotEqual(redirect_url, None)

    def test_call_api_usd(self):
        """check call API in USD"""

        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = PaylineClient(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )

        redirect_url = client.do_web_payment(
            amount=Decimal("12.50"), currency=u"USD", order_ref=dummy_order_ref,
            return_url='http://freexian.com/success/', cancel_url='http://freexian.com/cancel/'
        )
        self.assertNotEqual(redirect_url, None)

    def test_call_api_cache(self):
        """check call API with cache set"""

        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = PaylineClient(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True, cache=u"WebPaymentAPI"
        )

        redirect_url = client.do_web_payment(
            amount=Decimal("12.50"), currency=u"EUR", order_ref=dummy_order_ref,
            return_url='http://freexian.com/success/', cancel_url='http://freexian.com/cancel/'
        )
        self.assertNotEqual(redirect_url, None)

    def test_call_api_invalid_amount(self):
        """Check error if wrong value"""
        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = PaylineClient(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )

        self.assertRaises(PaylineApiError, client.do_web_payment,
            amount=Decimal("0.00"), currency=u"EUR", order_ref=dummy_order_ref,
            return_url='http://freexian.com/success/', cancel_url='http://freexian.com/cancel/'
        )

    def test_call_api_negative_amount(self):
        """Check error if wrong value"""
        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = PaylineClient(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )

        self.assertRaises(PaylineApiError, client.do_web_payment,
            amount=Decimal("-10.00"), currency=u"EUR", order_ref=dummy_order_ref,
            return_url='http://freexian.com/success/', cancel_url='http://freexian.com/cancel/'
        )

    def test_call_api_invalid_currency(self):
        """Check error if wrong currency"""
        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = PaylineClient(
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

        client = PaylineClient(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )

        self.assertRaises(
            PaylineApiError, client.do_web_payment,
            amount=Decimal("-10.00"), currency=u"EUR", order_ref=dummy_order_ref,
            return_url='http://freexian.com/success/', cancel_url='http://freexian.com/cancel/'
        )

    def test_call_api_invalid_return_url(self):
        """Check error if wrong return url"""
        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = PaylineClient(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )

        self.assertRaises(
            PaylineApiError, client.do_web_payment,
            amount=Decimal("-10.00"), currency=u"EUR", order_ref=dummy_order_ref,
            return_url='', cancel_url='http://freexian.com/cancel/'
        )

    def test_call_api_invalid_cancel_url(self):
        """Check error if wrong cancel url"""
        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = PaylineClient(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number=self.contract_number,
            homologation=True
        )

        self.assertRaises(
            PaylineApiError, client.do_web_payment,
            amount=Decimal("-10.00"), currency=u"EUR", order_ref=dummy_order_ref,
            return_url='http://freexian.com/success/', cancel_url='/cancel/'
        )

    def test_invalid_contract(self):
        """Check error if Invalid contract"""
        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = PaylineClient(
            merchant_id=self.merchant_id, access_key=self.access_key, contract_number='',
            homologation=True, cache=False
        )

        self.assertRaises(
            PaylineApiError, client.do_web_payment,
            amount=Decimal("-10.00"), currency=u"EUR", order_ref=dummy_order_ref,
            return_url='http://freexian.com/success/', cancel_url='/cancel/'
        )

    def test_invalid_merchant(self):
        """Check error if Invalid merchant Id"""
        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        client = PaylineClient(
            merchant_id=u"1234", access_key=self.access_key, contract_number=self.contract_number,
            homologation=True, cache=False
        )

        self.assertRaises(
            PaylineAuthError, client.do_web_payment,
            amount=Decimal("-10.00"), currency=u"EUR", order_ref=dummy_order_ref,
            return_url='http://freexian.com/success/', cancel_url='/cancel/'
        )

    def test_invalid_access_key(self):
        """Check error if Invalid access key"""
        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')
        client = PaylineClient(
            merchant_id=self.merchant_id, access_key=u"abcd", contract_number=self.contract_number,
            homologation=True, cache=False
        )

        self.assertRaises(
            PaylineAuthError, client.do_web_payment,
            amount=Decimal("-10.00"), currency=u"EUR", order_ref=dummy_order_ref,
            return_url='http://freexian.com/success/', cancel_url='/cancel/'
        )


if __name__ == '__main__':
    unittest.main()