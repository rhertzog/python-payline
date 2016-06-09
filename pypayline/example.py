# -*- coding: utf-8 -*-
"""Python client for the Payline SOAP API"""

from __future__ import print_function

from datetime import datetime
from decimal import Decimal
import sys

from pypayline.client import PaylineClient
from pypayline.exceptions import PaylineApiError, PaylineAuthError


def ask_input(prompt=''):
    """ask input to the user"""
    try:
        return raw_input(prompt)
    except:
        return input(prompt)


def web_payment_example():
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
            api_name='WebPaymentAPI',
            merchant_id=merchant_id, access_key=access_key, contract_number=contract_number, homologation=True,
            # cache=None
        )
    except PaylineAuthError as err:
        print("#AUTH ERR:", err)

    try:
        currency = u"EUR"
        amount = ask_input(u'> Amount? (Prefix with $ to use this currency)')
        if amount[0] == u'$':
            amount = amount[1:]
            currency = u"USD"
        amount = Decimal(amount)
    except ValueError:
        print("Invalid value")
        raise

    recurring_times = None
    recurring_in_months = None
    recurring = ask_input(u'> Recurring in months? (Enter or 1, 3 or 6 months)')
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

        ask_input('Press Enter to get payment details')

        result_code, is_transaction_ok, order_ref, amount, currency, raw_data = client.get_web_payment_details(
            token
        )
        print('> OK?', result_code, is_transaction_ok)
        print('> Order', order_ref, ":", amount, currency)
        print("********\n", raw_data, '\n*******')

    except PaylineApiError as err:
        print("#API ERR:", err)


def direct_payment_example():
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
            api_name='DirectPaymentAPI',
            merchant_id=merchant_id, access_key=access_key, contract_number=contract_number, homologation=True,
            # cache=None
        )
    except PaylineAuthError as err:
        print("#AUTH ERR:", err)

    try:
        payment_record_id = ask_input('Press Enter Payment record id? ')

        print('payment_record_id: ', payment_record_id)

        result_code, order_ref, amount, raw_data = client.get_payment_record(
            CONTRACT_NUMBER, int(payment_record_id)
        )
        print('> OK?', result_code, order_ref)
        print('> Order', order_ref, ":", amount)
        print("********\n", raw_data, '\n*******')

    except PaylineApiError as err:
        print("#API ERR:", err)


def quit():
    sys.exit(0)


def main_example():
    menu = [quit, web_payment_example, direct_payment_example]

    while True:
        for index, menu_item in enumerate(menu):
            print(index, ':', menu_item.__name__)

        choice = ask_input('Choice?')

        try:
            callback_fct = menu[int(choice)]
        except (IndexError, ValueError):
            callback_fct = None

        if callback_fct:
            callback_fct()


main_example()