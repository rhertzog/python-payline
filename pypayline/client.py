# -*- coding: utf-8 -*-
"""
Python client for the Payline SOAP API
client class
"""

from __future__ import print_function

import base64
from datetime import datetime
from decimal import Decimal

from pypayline.backends.soap import SoapBackend
from pypayline.exceptions import InvalidCurrencyError, ArgumentsError


class PaylineClient(object):
    """Class for calling the payline services"""
    backend_class = SoapBackend

    currencies = {
        u'EUR': 978,
        u'USD': 840,
    }

    def __init__(
            self, api_name, merchant_id, access_key, contract_number, cache=True, trace=False, homologation=False
    ):
        """
        Init the SOAP by getting the WSDL of the service. It is recommeded to cache it

        :param api_name : WSDL to get ('WebPaymentAPI' or 'DirectPaymentAPI')
        :param merchant_id : Your Payline Merchant id
        :param access_key : Your Payline access key
        :param contract number : Your Payline contract number
        :param cache : cache the WSDL file (recommended to do it). Cache is disabled if None
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
            payline_host = u'https://homologation.payline.com'
        else:
            payline_host = u'https://services.payline.com'

        wsdl_url = payline_host + u'/V4/services/{0}?wsdl'.format(api_name)
        # Create the webservice client
        self.backend = self.backend_class(
            wsdl=wsdl_url,
            http_headers=self.http_headers,
            cache=api_name if cache else None,
            trace=trace,
            api_name=api_name
        )

        # Patch location : The WSDL doesn't have the right location for the service
        location = self.backend.services[api_name]['ports'][api_name]['location']
        patched_location = location.replace(u'http://host', payline_host)
        self.backend.services[api_name]['ports'][api_name]['location'] = patched_location

    def do_web_payment(
            self, amount, currency, order_ref, return_url, cancel_url, recurring_times=None,
            recurring_period_in_months=None, payline_action=100, taxes=0, country='', buyer=None
            ):
        """
        Calls the Payline SOAP API for making a new payment

        :param amount: amount to pay
        :param currency: currency (currenttly supported EUR and USD)
        :param order_ref: The order refernce (in your shopping system) corresponding to the payment
        :param return_url: The Url to go after payment
        :param cancel_url: The Url to go if user cancels the payment
        :param recurring_times: number of payments
        :param recurring_period_in_months: Recurring period in months
        :param payline_action: Payline code. Can be 100 (Autorisation) or 101 (Autorisation + validation)
            See Payline docs
        :param taxes: amount of taxes (for info)
        :param country: country (for info)
        :param buyer: dictionnary with buyer info
        :return: Payline response as a dictionnary with the following keys
            - redirectURL : where to redirect the user
            - token = a token for the query
            - result as a dictionnary
                - code: '00000' if successfull
                - longMessage = long message
                - shortMessage
        :raise:
            - PaylineError if call to SOAP API fails
            - InvalidCurrencyError if currency value is not supported
            - ArgumentsError : if recurring is invalid
        """

        # Check and convert params
        formatted_amount = int(amount * 100)
        formatted_taxes = int(taxes * 100)

        formatted_currency = self.currencies.get(currency, None)

        if formatted_currency is None:
            raise InvalidCurrencyError(u'{0} currency is not supported'.format(currency))

        if recurring_times is None:
            payment_mode = u'CPT'
            recurring = {}
        else:
            payment_mode = u'NX'
            recurring_amount = formatted_amount // recurring_times
            first_amount = recurring_amount + (formatted_amount - recurring_times * recurring_amount)
            if recurring_period_in_months is None:
                raise ArgumentsError(u'The recurring_period_in_months argument should be set with interger values')

            recurring_periods_map = {
                1: 40,  # Monthly
                3: 60,  # Quarterly
                6: 70,  # Half-yearly
            }
            try:
                recurring_period = recurring_periods_map[int(recurring_period_in_months)]
            except ValueError:
                raise ArgumentsError(u'The recurring_period_in_months argument should be an interger value')
            except KeyError:
                raise ArgumentsError(u'The recurring_period_in_months argument should be in 1, 3 or 6 months')

            recurring = {
                'billingLeft': recurring_times,
                'firstAmount': first_amount,
                'amount': recurring_amount,
                'billingCycle': recurring_period,
            }

        redirect_url, token = self.backend.doWebPayment(
            version="3",
            payment={
                'amount': formatted_amount,
                'currency': formatted_currency,
                'action': payline_action,
                'mode': payment_mode,
                'contractNumber': self.contract_number,
                # 'deferredActionDate': 'dd/mm/yy',
            },
            order={
                'ref': order_ref,
                'amount': formatted_amount,
                'currency': formatted_currency,
                'date': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'taxes': formatted_taxes,
                'country': country,
            },
            buyer=buyer or {},
            owner={},
            recurring=recurring,
            selectedContractList={},
            securityMode='SSL',
            returnURL=return_url,
            cancelURL=cancel_url
        )
        return redirect_url, token

    def get_web_payment_details(self, token):
        """
        Get the status of a payment
        :param token: Th epayment token (returned by do_web_payment
        :return: tuple
         - result_code = the API result code
         - is_transaction_ok = no fraud detected
         - order_ref: the order id,
         - amount: the paid amount,
         - currency: the used currency
         - data: the raw data
        """
        data = self.backend.getWebPaymentDetails(
            version="3",
            token=token
        )

        try:
            is_transaction_ok = not int(data['transaction']['isPossibleFraud'])
        except (KeyError, TypeError):
            is_transaction_ok = None

        try:
            amount = int(data['payment']['amount'])
            amount_int, amout_decimal = amount // 100, amount % 100
            amount = Decimal('{0}.{1:02}'.format(amount_int, amout_decimal))
        except (KeyError, TypeError):
            amount = None

        try:
            currency_reverse = dict([(v, k) for (k, v) in self.currencies.items()])
            currency = currency_reverse[int(data['payment']['currency'])]
        except (KeyError, TypeError):
            currency = None

        try:
            order_ref = data['order']['ref']
        except (KeyError, TypeError):
            order_ref = None

        try:
            result_code = data['result']['code']
        except (KeyError, TypeError):
            result_code = ""

        return result_code, is_transaction_ok, order_ref, amount, currency, data

    def get_payment_record(self, contract_number, payment_record_id):
        """
        Get the status of a payment
        :param contract_number: Contract number
        :param payment_record_id: record identifier, Received by IPN
        :return: tuple
         - result_code = the API result code
         - is_transaction_ok = no fraud detected
         - order_ref: the order id,
         - amount: the paid amount,
         - data: the raw data
        """
        data = self.backend.getPaymentRecord(
            contractNumber=contract_number,
            paymentRecordId=payment_record_id
        )

        try:
            order_ref = data['order']['ref']
        except (TypeError, KeyError):
            order_ref = None

        try:
            amount = int(data['recurring']['amount'])
            amount_int, amout_decimal = amount // 100, amount % 100
            amount = Decimal('{0}.{1:02}'.format(amount_int, amout_decimal))
        except (TypeError, KeyError):
            amount = None

        try:
            result_code = data['result']['code']
        except (TypeError, KeyError):
            result_code = ""

        return result_code, order_ref, amount, data
