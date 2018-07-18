# -*- coding: utf-8 -*-
"""
Python client for the Payline SOAP API
"""

from datetime import datetime
from decimal import Decimal
import logging
import re
import sys
import unittest
import os

from pypayline.client import PaylineBaseAPI, WebPaymentAPI, DirectPaymentAPI
from pypayline.exceptions import InvalidCurrencyError, PaylineApiError, PaylineAuthError


logger = logging.getLogger('pypayline')
logger.addHandler(logging.StreamHandler())

logger_pysimplesoap = logging.getLogger('pysimplesoap')
logger_pysimplesoap.addHandler(logging.StreamHandler())
logger_pysimplesoap.setLevel(logging.DEBUG)

class PaylineBaseAPITestCase(unittest.TestCase):

    def setUp(self):
        self.api = PaylineBaseAPI()

    def test_init_default(self):
        api = PaylineBaseAPI()
        self.assertIsNone(api.merchant_id)
        self.assertIsNone(api.access_key)
        self.assertFalse(api.sandbox)

    def test_init_with_args(self):
        api = PaylineBaseAPI('1234', 'ABCD', 'contract1')
        self.assertEqual(api.merchant_id, '1234')
        self.assertEqual(api.access_key, 'ABCD')
        self.assertEqual(api.contract_number, 'contract1')

    def test_init_with_kwargs(self):
        api = PaylineBaseAPI(merchant_id='1234', access_key='ABCD',
                             contract_number='contract1',
                             homologation=True)
        self.assertEqual(api.merchant_id, '1234')
        self.assertEqual(api.access_key, 'ABCD')
        self.assertEqual(api.contract_number, 'contract1')
        self.assertTrue(api.sandbox)

    def test_soap_url_production(self):
        self.api.api_name = 'SampleAPI'
        self.assertEqual(self.api.soap_url,
                         'https://services.payline.com/V4/services/SampleAPI')

    def test_soap_url_sandbox(self):
        self.api.api_name = 'SampleAPI'
        self.api.sandbox = True
        self.assertEqual(
            self.api.soap_url,
            'https://homologation.payline.com/V4/services/SampleAPI'
        )

    def test_soap_wsdl_url_is_local(self):
        url = self.api.soap_wsdl_url
        self.assertTrue(url.startswith('file://'))

    def test_soap_wsdl_url_is_valid_path(self):
        # Use a real API name so that the file exists
        self.api.api_name = 'WebPaymentAPI'

        path = self.api.soap_wsdl_url[7:]

        self.assertEqual(path[0], '/')  ## Absolute path
        self.assertTrue(os.path.exists(path))

    def test_soap_wsdl_url_ends_with_api_name(self):
        path = self.api.soap_wsdl_url[7:]

        self.assertEqual(os.path.basename(path), 'PaylineBaseAPI.wsdl')


class WebPaymentAPITestCase(unittest.TestCase):

    def setUp(self):
        self.api = WebPaymentAPI('1234', 'ABCD', 'contract1,contract2')
        # Ensure we don't make any network call
        self.api.backend.soap_client.location = 'test'

    def test_soap_url(self):
        self.assertEqual(os.path.basename(self.api.soap_url), 'WebPaymentAPI')

    def test_soap_wsdl_url(self):
        self.assertEqual(os.path.basename(self.api.soap_wsdl_url),
                         'WebPaymentAPI.wsdl')

    def test_do_web_payment(self):
        self.api.do_web_payment(
            amount=Decimal("12.50"), currency=u"EUR", order_ref='ref1',
            return_url='http://freexian.com/success/',
            cancel_url='http://freexian.com/cancel/',
        )

class DirectPaymentAPITestCase(unittest.TestCase):

    def setUp(self):
        self.api = DirectPaymentAPI('1234', 'ABCD', 'contract1')
        # Ensure we don't make any network call
        self.api.backend.soap_client.location = 'test'

    def test_soap_url(self):
        self.assertEqual(os.path.basename(self.api.soap_url),
                         'DirectPaymentAPI')

    def test_soap_wsdl_url(self):
        self.assertEqual(os.path.basename(self.api.soap_wsdl_url),
                         'DirectPaymentAPI.wsdl')


if __name__ == '__main__':
    unittest.main()
