# -*- coding: utf-8 -*-
"""Python client for the Payline SOAP API"""

import base64
from datetime import datetime
from decimal import Decimal

from pysimplesoap.client import SoapClient, SoapFault


VERSION = "0.0.3"


class InvalidCurrencyError(Exception):
    pass


class PaylineError(Exception):
    pass


class PaylineClient(object):
    """Class for calling the payline services"""

    def __init__(
            self, merchant_id, access_key, contract_number, cache='WebPaymentAPI', trace=False, homologation=False
    ):
        """
        Init the SOAP by getting the WSDL of the service. It is recommeded to cache it

        :param merchant_id : Your Payline Merchant id
        :param access_key : Your Payline access key
        :param contract number : Your Payline contract number
        :param cache : Name of directory where to cache the WSDL file (recommended to do it). Cache is disabled if None
        :param trace : print some debug logs
        :param homologation : if True use the homologation host for test. If false, user the regular host
        """

        self.merchant_id, self.access_key, self.contract_number = merchant_id, access_key, contract_number

        # Create the header. last char of the base64 token is \n -> remove it
        authorization_token = base64.encodestring(u'{0}:{1}'.format(self.merchant_id, self.access_key))[:-1]
        self.http_headers = {
            u'Authorization': u'Basic {0}'.format(authorization_token),
        }

        if homologation:
            payline_host = 'https://homologation.payline.com'
        else:
            payline_host = 'https://services.payline.com'

        wsdl_url = payline_host + '/V4/services/WebPaymentAPI?wsdl'
        # Create the webservice client
        self.soap_client = SoapClient(
            wsdl=wsdl_url,
            http_headers=self.http_headers,
            cache=cache,
            trace=trace
        )
        # Patch the location with host

        # Patch location : The WSDL doesn't have the right location for the service
        location = self.soap_client.services['WebPaymentAPI']['ports']['WebPaymentAPI']['location']
        patched_location = location.replace('http://host', payline_host)
        self.soap_client.services['WebPaymentAPI']['ports']['WebPaymentAPI']['location'] = patched_location

    def do_web_payment(self, amount, currency, order_ref, return_url, cancel_url, payline_action=100):
        """
        Calls the Payline SOAP API for making a new payment

        :param amount: amount to pay
        :param currency: currency (currenttly supported EUR and USD)
        :param order_ref: The order refernce (in your shopping system) corresponding to the payment
        :param return_url: The Url to go after payment
        :param cancel_url: The Url to go if user cancels the payment
        :param payline_action: Payline code. Can be 100 (Autorisation) or 101 (Autorisation + validation)
            See Payline docs
        :return: Payline response as a dictionnary with the following keys
            - redirectURL : where to redirect the user
            - token = a token for the query
            - result as a dictionnary
                - code: '00000' if successfull
                - longMessage = long message
                - shortMessage
        :raise PaylineError if call to SOAP API fails or InvalidCurrencyError if currency value is not supported
        """

        # Check and convert params
        formatted_amount = int(amount * 100)

        currencies = {
            u'EUR': 978,
            u'USD': 840,
        }

        formatted_currency = currencies.get(currency, None)

        if formatted_currency is None:
            raise InvalidCurrencyError(u'{0} currency is not supported'.format(currency))

        # Call the doWebPaymentRequest webservice

        try:
            response = self.soap_client.doWebPayment(
                version="3",
                payment={
                    'amount': formatted_amount,
                    'currency': formatted_currency,
                    'action': payline_action,
                    'mode': 'CPT',  # TODO
                    'contractNumber': self.contract_number,
                    #'deferredActionDate': 'dd/mm/yy',
                },
                order={
                    'ref': order_ref,
                    'amount': formatted_amount,
                    'currency': formatted_currency,
                    'date': datetime.now().strftime('%d/%m/%Y %H:%M')

                },
                buyer={},
                owner={},
                recurring={},
                selectedContractList={},
                securityMode='SSL',
                returnURL=return_url,
                cancelURL=cancel_url
            )
        except SoapFault as err:
            raise PaylineError(unicode(err))

        return response


if __name__ == '__main__':
    dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

    try:
        from payline_secrets import MERCHANT_ID, ACCESS_KEY, CONTRACT_NUMBER
    except ImportError:
        print u"""
            You must create a payline_secrets.py in your path and defines 3 globals
            MERCHANT_ID = "1234567890"
            ACCESS_KEY = "DJMESHXYou6LmjQFdH"
            CONTRACT_NUMBER = "123456"
        """

    merchant_id, access_key, contrat_number = MERCHANT_ID, ACCESS_KEY, CONTRACT_NUMBER

    client = PaylineClient(
        merchant_id=merchant_id, access_key=access_key, contract_number=contrat_number, homologation=True, #cache=None
    )

    client.do_web_payment(
        amount=Decimal("12.50"), currency=u"EUR", order_ref=dummy_order_ref,
        return_url='http://freexian.com/success/', cancel_url='http://freexian.com/cancel/'
    )
