"""Tests for app/paystack.py in isolation -- no Django models involved, just
the HTTP wrapper's error handling around requests. Every network call is
mocked; nothing here talks to the real Paystack API.
"""
import hashlib
import hmac
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from . import paystack


@override_settings(PAYSTACK_SECRET_KEY="test-secret", PAYSTACK_BASE_URL="https://api.paystack.co")
class InitializeTransactionTests(TestCase):
    @patch("app.paystack.requests.post")
    def test_successful_response_returns_data(self, mock_post):
        mock_post.return_value = Mock(
            ok=True,
            status_code=200,
            json=lambda: {"status": True, "data": {"authorization_url": "https://paystack.test/pay/abc"}},
        )
        result = paystack.initialize_transaction(email="a@example.com", amount_pesewas=1000, reference="ref1")
        self.assertEqual(result["authorization_url"], "https://paystack.test/pay/abc")

    @patch("app.paystack.requests.post")
    def test_amount_is_sent_in_pesewas_not_cedis(self, mock_post):
        # Regression guard: Paystack expects the smallest currency unit.
        # Sending cedis directly would be a 100x overcharge bug.
        mock_post.return_value = Mock(ok=True, status_code=200, json=lambda: {"status": True, "data": {}})
        paystack.initialize_transaction(email="a@example.com", amount_pesewas=12345, reference="ref2")
        sent_payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(sent_payload["amount"], 12345)

    @patch("app.paystack.requests.post")
    def test_non_ok_response_raises_paystack_error(self, mock_post):
        mock_post.return_value = Mock(
            ok=False, status_code=400, json=lambda: {"status": False, "message": "Invalid key"}
        )
        with self.assertRaisesMessage(paystack.PaystackError, "Invalid key"):
            paystack.initialize_transaction(email="a@example.com", amount_pesewas=1000, reference="ref3")

    @patch("app.paystack.requests.post")
    def test_non_json_response_raises_paystack_error_not_json_decode_error(self, mock_post):
        def _raise_value_error():
            raise ValueError("not json")

        mock_post.return_value = Mock(ok=True, status_code=200, json=_raise_value_error)
        with self.assertRaises(paystack.PaystackError):
            paystack.initialize_transaction(email="a@example.com", amount_pesewas=1000, reference="ref4")

    @patch("app.paystack.requests.post")
    def test_network_failure_raises_paystack_error(self, mock_post):
        import requests as requests_module

        mock_post.side_effect = requests_module.ConnectionError("no route to host")
        with self.assertRaises(paystack.PaystackError):
            paystack.initialize_transaction(email="a@example.com", amount_pesewas=1000, reference="ref5")

    @override_settings(PAYSTACK_SECRET_KEY="")
    def test_missing_secret_key_raises_before_any_network_call(self):
        with self.assertRaises(paystack.PaystackError):
            paystack.initialize_transaction(email="a@example.com", amount_pesewas=1000, reference="ref6")


@override_settings(PAYSTACK_SECRET_KEY="test-secret", PAYSTACK_BASE_URL="https://api.paystack.co")
class VerifyTransactionTests(TestCase):
    @patch("app.paystack.requests.get")
    def test_returns_the_data_payload(self, mock_get):
        mock_get.return_value = Mock(
            ok=True, status_code=200,
            json=lambda: {"status": True, "data": {"status": "success", "amount": 1000}},
        )
        result = paystack.verify_transaction("ref1")
        self.assertEqual(result["status"], "success")

    @patch("app.paystack.requests.get")
    def test_failed_transaction_is_still_a_valid_response_not_an_error(self, mock_get):
        # Paystack returns status=True (the API call itself succeeded) even
        # when the underlying transaction failed -- verify_transaction must
        # return that data for the caller to inspect, not raise.
        mock_get.return_value = Mock(
            ok=True, status_code=200,
            json=lambda: {"status": True, "data": {"status": "failed", "gateway_response": "Declined"}},
        )
        result = paystack.verify_transaction("ref2")
        self.assertEqual(result["status"], "failed")

    @patch("app.paystack.requests.get")
    def test_api_level_failure_raises_paystack_error(self, mock_get):
        mock_get.return_value = Mock(
            ok=False, status_code=404, json=lambda: {"status": False, "message": "Transaction not found"}
        )
        with self.assertRaisesMessage(paystack.PaystackError, "Transaction not found"):
            paystack.verify_transaction("does-not-exist")


class WebhookSignatureTests(TestCase):
    @override_settings(PAYSTACK_SECRET_KEY="test-secret")
    def test_correct_signature_verifies(self):
        body = b'{"event":"charge.success"}'
        sig = hmac.new(b"test-secret", body, hashlib.sha512).hexdigest()
        self.assertTrue(paystack.verify_webhook_signature(body, sig))

    @override_settings(PAYSTACK_SECRET_KEY="test-secret")
    def test_wrong_signature_is_rejected(self):
        body = b'{"event":"charge.success"}'
        self.assertFalse(paystack.verify_webhook_signature(body, "not-the-right-signature"))

    @override_settings(PAYSTACK_SECRET_KEY="test-secret")
    def test_tampered_body_is_rejected(self):
        original_body = b'{"event":"charge.success","amount":1000}'
        sig = hmac.new(b"test-secret", original_body, hashlib.sha512).hexdigest()
        tampered_body = b'{"event":"charge.success","amount":9999999}'
        self.assertFalse(paystack.verify_webhook_signature(tampered_body, sig))

    @override_settings(PAYSTACK_SECRET_KEY="")
    def test_missing_secret_key_never_verifies(self):
        body = b'{"event":"charge.success"}'
        self.assertFalse(paystack.verify_webhook_signature(body, "anything"))

    @override_settings(PAYSTACK_SECRET_KEY="test-secret")
    def test_missing_signature_header_is_rejected(self):
        body = b'{"event":"charge.success"}'
        self.assertFalse(paystack.verify_webhook_signature(body, ""))
