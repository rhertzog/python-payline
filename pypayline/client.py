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
from pypayline.exceptions import InvalidCurrencyError, PaylineApiError, PaylineAuthError, ArgumentsError


class PaylineClient(object):
    """Class for calling the payline services"""
    backend_class = SoapBackend

    currencies = {
        u'EUR': 978,
        u'USD': 840,
    }

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
            payline_host = u'https://homologation.payline.com'
        else:
            payline_host = u'https://services.payline.com'

        wsdl_url = payline_host + u'/V4/services/WebPaymentAPI?wsdl'
        # Create the webservice client
        self.backend = self.backend_class(
            wsdl=wsdl_url,
            http_headers=self.http_headers,
            cache=cache,
            trace=trace
        )

        # Patch location : The WSDL doesn't have the right location for the service
        location = self.backend.services['WebPaymentAPI']['ports']['WebPaymentAPI']['location']
        patched_location = location.replace(u'http://host', payline_host)
        self.backend.services['WebPaymentAPI']['ports']['WebPaymentAPI']['location'] = patched_location

    def do_web_payment(
            self, amount, currency, order_ref, return_url, cancel_url, recurring_times=None,
            recurring_period_in_months=None, payline_action=100
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
                'date': datetime.now().strftime('%d/%m/%Y %H:%M')

            },
            buyer={},
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

        is_transaction_ok = not int(data['transaction']['isPossibleFraud'])
        amount = int(data['payment']['amount'])
        amount_int, amout_decimal = amount // 100, amount % 100
        amount = Decimal('{0}.{1:02}'.format(amount_int, amout_decimal))

        currency_reverse = dict([(v, k) for (k, v) in self.currencies.items()])
        currency = currency_reverse[int(data['payment']['currency'])]

        order_ref = data['order']['ref']
        result_code = data['result']['code']

        return result_code, is_transaction_ok, order_ref, amount, currency, data


if __name__ == '__main__':

    def main_example():
        dummy_order_ref = datetime.now().strftime('%Y%m%d%H%M')

        try:
            from payline_secrets import MERCHANT_ID, ACCESS_KEY, CONTRACT_NUMBER
        except ImportError:
            print(u"""
                You must create a payline_secrets.py in your path and defines 3 globals
                MERCHANT_ID = "1234567890"
                ACCESS_KEY = "DJMESHXYou6LmjQFdH"
                CONTRACT_NUMBER = "123456"
            """)

        merchant_id, access_key, contract_number = MERCHANT_ID, ACCESS_KEY, CONTRACT_NUMBER

        try:
            client = PaylineClient(
                merchant_id=merchant_id, access_key=access_key, contract_number=contract_number, homologation=True,
                #cache=None
            )
        except PaylineAuthError as err:
            print("#AUTH ERR:", err)

        try:
            currency = u"EUR"
            amount = raw_input(u'> Amount? (Prefix with $ to use this currency)')
            if amount[0] == u'$':
                amount = amount[1:]
                currency = u"USD"
            amount = Decimal(amount)
        except ValueError:
            print("Invalid value")
            raise

        recurring_times = None
        recurring_in_months = None
        recurring = raw_input(u'> Recurring in months? (Enter or 1, 3 or 6 months)')
        if recurring.isdigit():
            recurring = int(recurring)
            if recurring in (1, 3, 6):
                recurring_times = 12 // recurring
                recurring_in_months = recurring

        try:
            redirect_url, token = client.do_web_payment(
                amount=amount, currency=currency, order_ref=dummy_order_ref,
                recurring_period_in_months=recurring_in_months, recurring_times=recurring_times,
                return_url='http://freexian.com/success/', cancel_url='http://freexian.com/cancel/'
            )
            print("Redirect to", redirect_url)
            print("Token", token)

            try:
                raw_input('Press Enter to get payment details')
            except:
                input('Press Enter to get payment details')

            result_code, is_transaction_ok, order_ref, amount, currency, raw_data = client.get_web_payment_details(
                token
            )
            print('> OK?', result_code, is_transaction_ok)
            print('> Order', order_ref, ":", amount, currency)
            print("********\n", raw_data, '\n*******')

        except PaylineApiError as err:
            print("#API ERR:", err)


    main_example()
