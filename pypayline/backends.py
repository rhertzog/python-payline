# -*- coding: utf-8 -*-
"""Python client for the Payline SOAP API"""

from __future__ import print_function

from pysimplesoap.client import SoapClient, SoapFault

from pypayline.exceptions import PaylineError


class SoapMockBackend(object):
    """Mock the SOAP API client"""
    do_web_payment_exception = None

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.do_web_payment_kwargs = None

        token = u'3cXyapUchee8x645C6782541635718391'
        host = u'https://homologation-webpayment.payline.com/webpayment/step2.do'

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

    def doWebPayment(self, **kwargs):
        """call the doWebPayment SOAP API"""
        self.do_web_payment_kwargs = kwargs
        if self.do_web_payment_exception:
            raise self.do_web_payment_exception
        return self.result


class SoapBackend(object):
    def __init__(self, *args, **kwargs):
        """initialize the soap client and get wsdl file for service definition"""
        self.soap_client = SoapClient(*args, **kwargs)

    def doWebPayment(self, **kwargs):
        """call the doWebPayment SOAP API"""
        try:
            return self.soap_client.doWebPayment(**kwargs)
        except SoapFault as err:
            raise PaylineError(unicode(err))
