from rest_framework import serializers

from .base import AbstractProcessor
from core_payments.utils import assign_if_not_none, validate_keys_in_dict

from core_payments.models import (
    RESULT_APPROVED,
    RESULT_DECLINED,
    RESULT_ERROR,
    MODE_LIVE,
)

from ..models import (
    PROCESSOR_STRIPE,
    ACH_ACCOUNT_TYPE_INDIVIDUAL,
    ACH_ACCOUNT_TYPE_COMPANY,
    TENDER_TYPE_ACH,
    TENDER_TYPE_CREDIT_CARD,
    TRANSACTION_TYPE_CAPTURE,
    TRANSACTION_TYPE_VOID,
    TRANSACTION_TYPE_AUTHORIZE,
    TRANSACTION_TYPE_SALE,
    TRANSACTION_TYPE_REFUND,
)

from requests import request


TOKENS_API_URL_STRIPE = "/tokens"
CHARGES_API_URL_STRIPE = "/charges"
CHARGES_REFUNDS_API_URL_STRIPE = "/refunds"
CUSTOMER_API_URL_STRIPE = "/customers"

# {charge_id}
CHARGES_CAPTURE_API_URL_STRIPE = CHARGES_API_URL_STRIPE + "/{}/capture"

# {customer_id}
CREATE_BANK_ACCOUNT_API_URL_STRIPE = "/customers/{}/sources"

# {bank_account_id} use this url in sequence with CREATE_BANK_ACCOUNT_API_URL_STRIPE
VERIFY_BANK_ACCOUNT_API_URL_STRIPE = "/{}/verify"


class StripeProcessor(AbstractProcessor):
    name = PROCESSOR_STRIPE
    version = "v1"
    api_key = None

    # a map betweeb Stripe's transaction status and our API's values
    api_decision_map = {
        # Indicates a charge was declined
        "failed": RESULT_DECLINED,
        "succeeded": RESULT_APPROVED,
        # Indicates a charge was approved and is going to be applied 1-7 bussined days later
        "pending": RESULT_APPROVED,
        "error": RESULT_ERROR,
    }

    def _set_credentials(self):
        """Setups credentials fields according to request mode.
        Stripe provides us two types of secret api key,one for test mode and other for live mode.
        """
        self.api_key = self.transaction_request.credentials["api_key"]
        self.request_header = {"Authorization": "Bearer {}".format(self.api_key)}

    def _set_endpoint(self):
        """Setups api endpoint (stripe uses the same endpoint to test and live mode"""
        self.api_url = "https://api.stripe.com/{}".format(self.version)

    def _validate_card_cvc(self):
        """Validates if the card cvc coming in the request is valid
        The card's cvc must be a string conformed by digits only"""
        self.transaction_request.card_verification_value = str(
            self.transaction_request.card_verification_value
        )

        if not self.transaction_request.card_verification_value.isdigit():
            raise serializers.ValidationError(
                "Credit card verification value must be conformed by digits only."
            )

    def _validate_field_list(self, field_list, tender_type):
        """Takes a field list to verify if each field is present in the request"""
        for field in field_list:
            if not getattr(self.transaction_request, field):
                raise serializers.ValidationError(
                    "{} is required for {} transactions in the provided processor ({}).".format(
                        field, tender_type, self.name
                    )
                )

    def _validate_request(self):
        """Validates required and valid/invalid options in the request"""
        required_field_list = (
            ["card_expiry_month", "card_expiry_year", "card_verification_value"]
            if self.transaction_request.tender_type == TENDER_TYPE_CREDIT_CARD
            else [
                "bill_to_first_name",
                "bill_to_last_name",
                "ach_account_type",
                "ach_name_on_account",
            ]
        )

        # validate processor credentials here
        credentials = ["api_key"]
        validate_keys_in_dict(credentials, self.transaction_request.credentials)

        if self.transaction_request.invoice_number:
            raise serializers.ValidationError(
                "invoice_number is not supported in the provided processor ({}).".format(
                    self.name
                )
            )

        # original_transaction_id is required for capture, void and refund operations in stripe
        if (
            self.transaction_request.transaction_type
            in (
                TRANSACTION_TYPE_CAPTURE,
                TRANSACTION_TYPE_VOID,
                TRANSACTION_TYPE_REFUND,
            )
            and not self.transaction_request.original_transaction_id
        ):
            raise serializers.ValidationError(
                "original_transaction_id is required for void, capture and refund transactions in the provided processor ({}).".format(
                    self.name
                )
            )

        # Payments with CC in stripe need the card_account_number, card_expiry_month, card_expiry_year and card_verification_value
        # The card number is already verified by the serializer before to execute this method
        if (
            self.transaction_request.tender_type == TENDER_TYPE_CREDIT_CARD
            and self.transaction_request.transaction_type
            in (TRANSACTION_TYPE_SALE, TRANSACTION_TYPE_AUTHORIZE)
        ):
            self._validate_field_list(required_field_list, "CC")
            # At this point card_expiry_month, card_expiry_year and card_verification_value are in the request, so validate the cvc
            self._validate_card_cvc()

        elif self.transaction_request.tender_type == TENDER_TYPE_ACH:
            self._validate_field_list(required_field_list, "ACH")

            if self.transaction_request.ach_account_type not in (
                ACH_ACCOUNT_TYPE_COMPANY,
                ACH_ACCOUNT_TYPE_INDIVIDUAL,
            ):
                raise serializers.ValidationError(
                    "ach_account_type must be individual or company in the provided processor ({}).".format(
                        self.name
                    )
                )

    def _get_error_message(self, api_response):
        """Returns an error message according to the api response"""
        json_response = api_response.json()
        return "HTTP {} - Stripe error: {}".format(
            api_response.status_code, json_response["error"]["message"]
        )

    def _send_request(self, operation_api_url, payload):
        """Makes the request to Stripe and retuns the response."""
        api_url = self.api_url + operation_api_url
        api_response = request(
            method="POST", url=api_url, data=payload, headers=self.request_header
        )
        return api_response

    def _extract_object_id(self, api_response):
        """Gets the object id from the api_response if the status code is 200, otherwise raises an error"""
        id = None
        if api_response.status_code == 200:
            id = api_response.json()["id"]
        else:
            raise serializers.ValidationError(
                self._get_error_message(api_response), code=api_response.status_code
            )
        return id

    def _get_card_token(self):
        """Gets the card token that is going to be used in the charge request for CC payments"""
        card_token = None
        card_token_payload = dict()
        card_token_payload[
            "card[number]"
        ] = self.transaction_request.card_account_number
        card_token_payload[
            "card[exp_month]"
        ] = self.transaction_request.card_expiry_month
        card_token_payload["card[exp_year]"] = self.transaction_request.card_expiry_year
        card_token_payload[
            "card[cvc]"
        ] = self.transaction_request.card_verification_value

        api_response = self._send_request(TOKENS_API_URL_STRIPE, card_token_payload)
        card_token = self._extract_object_id(api_response)

        return card_token

    def _get_customer_id(self):
        """Gets the customer id that is going to be used in charge request for ACH payments"""
        customer_id = None
        customer_payload = dict()
        self._fill_payload_shipping_info(customer_payload)
        self._fill_payload_customer_info(customer_payload)

        api_response = self._send_request(CUSTOMER_API_URL_STRIPE, customer_payload)
        customer_id = self._extract_object_id(api_response)

        return customer_id

    def _get_bank_account_token(self):
        """Gets the bank account token that is going to be used in the charge request for ACH payments"""
        bank_account_token = None
        bank_account_token_payload = dict()
        bank_account_token_payload["bank_account[country]"] = "US"
        bank_account_token_payload["bank_account[currency]"] = "usd"
        bank_account_token_payload[
            "bank_account[account_holder_name]"
        ] = self.transaction_request.ach_name_on_account
        bank_account_token_payload[
            "bank_account[account_holder_type]"
        ] = self.transaction_request.ach_account_type
        bank_account_token_payload[
            "bank_account[routing_number]"
        ] = self.transaction_request.ach_routing_number
        bank_account_token_payload[
            "bank_account[account_number]"
        ] = self.transaction_request.ach_account_number

        api_response = self._send_request(
            TOKENS_API_URL_STRIPE, bank_account_token_payload
        )
        bank_account_token = self._extract_object_id(api_response)

        return bank_account_token

    def _is_valid_account(self, verify_api_url):
        """Sends a verify request to stripe to verify a bank account , if everything went well returns true, otherwise false"""
        is_valid = True
        payload = dict()
        #  THIS TWO AMOUNT REPRESENT A PROBLEM BECAUSE WE NEED THAT THE CUSTOMER SENT THEM TO US TO VERIFY THE BANK ACCOUNT
        payload["amounts[]"] = [32, 45]  # TEST AMOUNT THAT STRIPE GIVES US

        api_response = self._send_request(verify_api_url, payload)
        if api_response.status_code != 200:
            is_valid = False

        return is_valid, api_response

    def _verify_bank_account(self, customer_id):
        """Verifies the bank account that is going to be used in ACH payments, if some problem happens raises an error to indicates it"""
        payload = dict()
        create_bank_account_api_url = CREATE_BANK_ACCOUNT_API_URL_STRIPE.format(
            customer_id
        )
        # Before to send the ACH charge request we must to verify the bank account with the following steps:
        # 1) Get a bank account token and use it as a source
        # 2) Use the customer created and the bank account token to genereate a bank account
        # 3) Verify the bank account
        payload["source"] = self._get_bank_account_token()
        bank_account_id = self._extract_object_id(
            self._send_request(create_bank_account_api_url, payload)
        )
        is_valid_account, verify_account_response = self._is_valid_account(
            create_bank_account_api_url
            + VERIFY_BANK_ACCOUNT_API_URL_STRIPE.format(bank_account_id)
        )

        if not is_valid_account:
            self._get_error_message(verify_account_response)

        elif verify_account_response.json().get("status") != "verified":
            raise serializers.ValidationError("Account not yet verified")

    def _fill_payload_shipping_info(self, payload):
        """Fills the payload with the shipping info if available."""
        full_name = "{} {}".format(
            self.transaction_request.ship_to_first_name or "",
            self.transaction_request.ship_to_last_name or "",
        )

        payload["shipping[name]"] = full_name.strip()
        assign_if_not_none(
            payload, "shipping[phone]", self.transaction_request.ship_to_phone
        )
        assign_if_not_none(
            payload,
            "shipping[address[line1]]",
            self.transaction_request.ship_to_address
            if self.transaction_request.ship_to_address
            else "-",
        )
        assign_if_not_none(
            payload, "shipping[address[city]]", self.transaction_request.ship_to_city
        )
        assign_if_not_none(
            payload,
            "shipping[address[country]]",
            self.transaction_request.ship_to_country,
        )
        assign_if_not_none(
            payload, "shipping[address[state]]", self.transaction_request.ship_to_state
        )
        assign_if_not_none(
            payload,
            "shipping[address[postal_code]]",
            self.transaction_request.ship_to_zip,
        )

    def _fill_payload_customer_info(self, customer_payload):
        """Fills the payload with the info if available for one customer. Uses billing info"""
        full_name = "{} {}".format(
            self.transaction_request.bill_to_first_name,
            self.transaction_request.bill_to_last_name,
        )
        assign_if_not_none(customer_payload, "name", full_name.strip())
        assign_if_not_none(
            customer_payload, "phone", self.transaction_request.bill_to_phone
        )
        assign_if_not_none(
            customer_payload, "email", self.transaction_request.bill_to_email
        )
        assign_if_not_none(
            customer_payload,
            "address[line1]",
            self.transaction_request.bill_to_address
            if self.transaction_request.bill_to_address
            else "-",
        )
        assign_if_not_none(
            customer_payload, "address[city]", self.transaction_request.bill_to_city
        )
        assign_if_not_none(
            customer_payload,
            "address[country]",
            self.transaction_request.bill_to_country,
        )
        assign_if_not_none(
            customer_payload, "address[state]", self.transaction_request.bill_to_state
        )
        assign_if_not_none(
            customer_payload,
            "address[postal_code]",
            self.transaction_request.bill_to_zip,
        )

    def _fill_payload_tender_info(self):
        """Setups the tender information."""
        if TENDER_TYPE_CREDIT_CARD == self.transaction_request.tender_type:
            self.payload["source"] = self._get_card_token()
            # False when is necessary to place a holdin in the funds otherwise true
            self.payload["capture"] = (
                False
                if self.transaction_request.transaction_type
                == TRANSACTION_TYPE_AUTHORIZE
                else True
            )
        else:
            # With Stripe, you can accept ACH payments in nearly the same way as you accept credit card payments, by providing a verified bank account as the source argument for a charge request. However, accepting bank accounts requires a slightly different initial workflow than accepting credit cards:
            # 1) Bank accounts must first be verified.
            # 2) Bank accounts must be authorized for your use by the customer.
            self.payload["customer"] = self._get_customer_id()
            self._verify_bank_account(self.payload["customer"])

    def _fill_charges_payload(self):
        """Fills the paylod to perform a charge request. Billing info is not supported using token."""
        self.payload = dict()
        self._fill_payload_shipping_info(self.payload)
        self._fill_payload_tender_info()
        self.payload["amount"] = self.transaction_request.amount_in_cents
        self.payload["currency"] = "usd"
        self.payload["description"] = (
            self.transaction_request.description
            if self.transaction_request.description
            else "Charge for {} (amount in cents) {}".format(
                self.payload["amount"], self.payload["currency"]
            )
        )

    def _authorize(self):
        "Performs an authorize transaction using charge requests"
        if TENDER_TYPE_CREDIT_CARD == self.transaction_request.tender_type:
            self._fill_charges_payload()
            self.api_response = self._send_request(CHARGES_API_URL_STRIPE, self.payload)
        else:
            raise serializers.ValidationError(
                "Authorize transactions are allowed in payments with CC only"
            )

    def _capture(self):
        """Performs a capture transaction. Allowed in CC payments only"""
        if TENDER_TYPE_CREDIT_CARD == self.transaction_request.tender_type:
            capture_url = CHARGES_CAPTURE_API_URL_STRIPE.format(
                self.transaction_request.original_transaction_id
            )
            self.payload = dict()
            self.payload["amount"] = self.transaction_request.amount_in_cents
            self.api_response = self._send_request(capture_url, self.payload)
        else:
            raise serializers.ValidationError(
                "Capture transactions are allowed in payments with CC only"
            )

    def _sale(self):
        "Performs a sale transaction using charge requests"
        self._fill_charges_payload()
        self.api_response = self._send_request(CHARGES_API_URL_STRIPE, self.payload)

    def _refund(self):
        """Refunds a transactions that has been already captured."""
        self.payload = dict()
        self.payload["amount"] = self.transaction_request.amount_in_cents
        self.payload["charge"] = self.transaction_request.original_transaction_id
        self.api_response = self._send_request(
            CHARGES_REFUNDS_API_URL_STRIPE, self.payload
        )

    def _void(self):
        """Stripe does not allow void/cancel operation in charges, but we can use refund transaction instead and has the same result"""
        if TENDER_TYPE_CREDIT_CARD == self.transaction_request.tender_type:
            self._refund()
        else:
            raise serializers.ValidationError(
                "Void transactions are allowed in payments with CC only"
            )

    def serialize_api_response(self):
        try:
            self.api_response = self.api_response.json()
        except ValueError:
            raise serializers.ValidationError(
                "Something went wrong while the api response was being decoding"
            )

    def _parse_processor_response(self):
        """Parses the processor response into the format we need to return in this API"""
        result = RESULT_APPROVED  # we infer ok by default
        message = ""

        if self.api_response.status_code != 200:
            result = RESULT_ERROR
            message = self._get_error_message(self.api_response)
            self.serialize_api_response()
        else:
            self.serialize_api_response()
            transaction_type = self.transaction_request.transaction_type
            transaction_status = self.api_response.get("status")

            if transaction_status in ["succeeded", "failed", "pending"]:
                result = self.api_decision_map[self.api_response["status"]]
            else:
                result = RESULT_ERROR

            self.transaction_response.transaction_id = self.api_response.get("id")

            message = "Transaction type: {} - Result: {}{}.".format(
                transaction_type,
                transaction_status + "," if transaction_type == "authorize" else "",
                "held for review"
                if transaction_type == "authorize"
                else transaction_status,
            )

        self.transaction_response.message = message
        self.transaction_response.result = result
        self.transaction_response.processor_response = self.api_response
