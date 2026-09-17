from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import TestCase
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Address, User


class RegisterLoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "newbuyer", "email": "newbuyer@example.com",
                "password": "a-strong-passw0rd!", "password_confirm": "a-strong-passw0rd!",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.data)
        me = self.client.get("/api/me/")
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.data["username"], "newbuyer")

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "buyer2", "email": "b2@example.com",
                "password": "a-strong-passw0rd!", "password_confirm": "different",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_login_rejects_bad_credentials(self):
        response = self.client.post(
            "/api/auth/login/", {"username": "nobody", "password": "wrong"}, format="json",
        )
        self.assertEqual(response.status_code, 401)


class ProfileUpdateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="profile_buyer", email="p@example.com", password="pw")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_can_update_own_name_and_phone(self):
        response = self.client.patch(
            "/api/me/", {"first_name": "Ama", "last_name": "Owusu", "phone_number": "0551234567"}, format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Ama")
        self.assertEqual(self.user.phone_number, "0551234567")

    def test_username_and_email_are_not_editable_through_this_endpoint(self):
        response = self.client.patch(
            "/api/me/", {"username": "hacked", "email": "hacked@example.com"}, format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "profile_buyer")
        self.assertEqual(self.user.email, "p@example.com")


class AddressTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="addr_buyer", email="a@example.com", password="pw")
        self.other_user = User.objects.create_user(username="addr_other", email="o@example.com", password="pw")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _create(self, **overrides):
        payload = {
            "label": "Home", "full_name": "Ama Owusu", "address_line1": "12 High St",
            "city": "Kumasi", "country": "Ghana", "is_default": True,
        }
        payload.update(overrides)
        return self.client.post("/api/addresses/", payload, format="json")

    def test_setting_a_second_address_default_unsets_the_first(self):
        first = self._create(label="Home", is_default=True)
        second = self._create(label="Office", is_default=True)
        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(second.status_code, 201, second.data)

        listing = self.client.get("/api/addresses/")
        defaults = {row["label"]: row["is_default"] for row in listing.data["results"]}
        self.assertEqual(defaults, {"Home": False, "Office": True})

    def test_user_cannot_read_another_users_address(self):
        mine = self._create()
        self.client.force_authenticate(self.other_user)
        response = self.client.get(f"/api/addresses/{mine.data['id']}/")
        self.assertEqual(response.status_code, 404)

    def test_user_cannot_delete_another_users_address(self):
        mine = self._create()
        self.client.force_authenticate(self.other_user)
        response = self.client.delete(f"/api/addresses/{mine.data['id']}/")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Address.objects.filter(pk=mine.data["id"]).exists())


class ChangePasswordTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="pw_buyer", email="pw@example.com", password="OldPass123!")
        self.client = APIClient()
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_wrong_current_password_is_rejected(self):
        response = self.client.post(
            "/api/account/change-password/",
            {"current_password": "WrongPass", "new_password": "NewPass456!"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldPass123!"))

    def test_successful_change_revokes_old_token_and_updates_password(self):
        response = self.client.post(
            "/api/account/change-password/",
            {"current_password": "OldPass123!", "new_password": "NewPass456!"},
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass456!"))

        # The token issued before the change must no longer work.
        stale_client = APIClient()
        stale_client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.assertEqual(stale_client.get("/api/me/").status_code, 401)


class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="reset_buyer", email="reset@example.com", password="OldPass123!")
        self.client = APIClient()

    def test_request_does_not_reveal_whether_email_exists(self):
        known = self.client.post("/api/auth/password-reset/", {"email": "reset@example.com"}, format="json")
        unknown = self.client.post("/api/auth/password-reset/", {"email": "nobody@example.com"}, format="json")
        self.assertEqual(known.status_code, 200)
        self.assertEqual(unknown.status_code, 200)
        self.assertEqual(known.data, unknown.data)
        self.assertEqual(len(mail.outbox), 1, "only the real user should actually receive an email")

    def test_confirm_with_bad_token_is_rejected(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.post(
            "/api/auth/password-reset/confirm/",
            {"uid": uid, "token": "not-a-real-token", "new_password": "NewPass456!"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_confirm_with_valid_token_resets_password_and_is_single_use(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        first = self.client.post(
            "/api/auth/password-reset/confirm/",
            {"uid": uid, "token": token, "new_password": "NewPass456!"},
            format="json",
        )
        self.assertEqual(first.status_code, 200, first.data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPass456!"))

        # The same token must not work a second time (e.g. an email client
        # or proxy that prefetched/replayed the reset link).
        replay = self.client.post(
            "/api/auth/password-reset/confirm/",
            {"uid": uid, "token": token, "new_password": "AnotherPass789!"},
            format="json",
        )
        self.assertEqual(replay.status_code, 400)

        login = self.client.post(
            "/api/auth/login/", {"username": "reset_buyer", "password": "NewPass456!"}, format="json",
        )
        self.assertEqual(login.status_code, 200)


class GoogleLoginTests(TestCase):
    """verify_google_credential is patched: these test our side of the seam
    (account creation, linking, error mapping), not Google's JWT maths."""

    GOOD = {"email": "Ama.Boateng@gmail.com", "given_name": "Ama", "family_name": "Boateng", "sub": "123"}

    def setUp(self):
        from unittest.mock import patch

        self.client = APIClient()
        patcher = patch("users.views.verify_google_credential", return_value=dict(self.GOOD))
        self.verify = patcher.start()
        self.addCleanup(patcher.stop)

    def _post(self):
        return self.client.post("/api/auth/google/", {"credential": "x.y.z"}, format="json")

    def test_first_sign_in_creates_account_with_unusable_password(self):
        response = self._post()
        self.assertEqual(response.status_code, 201, response.data)
        user = User.objects.get(email__iexact=self.GOOD["email"])
        self.assertEqual(user.username, "amaboateng")
        self.assertEqual(user.first_name, "Ama")
        self.assertFalse(user.has_usable_password())
        self.assertIn("token", response.data)
        self.assertEqual(self.client.get("/api/me/").data["email"], self.GOOD["email"])

    def test_existing_account_is_linked_by_verified_email_not_duplicated(self):
        existing = User.objects.create_user(
            username="ama", email="ama.boateng@gmail.com", password="pw-original!"
        )
        response = self._post()
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["id"], existing.id)
        self.assertEqual(User.objects.filter(email__iexact=self.GOOD["email"]).count(), 1)
        existing.refresh_from_db()
        self.assertTrue(existing.check_password("pw-original!"))  # untouched

    def test_username_collision_gets_a_suffix(self):
        User.objects.create_user(username="amaboateng", email="other@example.com", password="pw")
        response = self._post()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["username"], "amaboateng2")

    def test_unverifiable_credential_is_401_and_creates_nothing(self):
        from users.google import GoogleAuthError

        self.verify.side_effect = GoogleAuthError("Google sign-in could not be verified.")
        response = self._post()
        self.assertEqual(response.status_code, 401)
        self.assertFalse(User.objects.filter(email__iexact=self.GOOD["email"]).exists())

    def test_unconfigured_server_is_503(self):
        from users.google import GoogleNotConfigured

        self.verify.side_effect = GoogleNotConfigured("Google sign-in is not configured on this server.")
        self.assertEqual(self._post().status_code, 503)

    def test_missing_credential_is_400(self):
        response = self.client.post("/api/auth/google/", {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.verify.assert_not_called()


class GoogleVerifierTests(TestCase):
    """The unpatched verifier, with google-auth's own call stubbed."""

    def test_refuses_when_not_configured(self):
        from django.test import override_settings

        from users.google import GoogleNotConfigured, verify_google_credential

        with override_settings(GOOGLE_CLIENT_ID=""):
            with self.assertRaises(GoogleNotConfigured):
                verify_google_credential("x.y.z")

    def test_refuses_unverified_email_and_wrong_issuer(self):
        from unittest.mock import patch

        from django.test import override_settings

        from users.google import GoogleAuthError, verify_google_credential

        base = {"iss": "accounts.google.com", "email": "a@b.c", "email_verified": True, "sub": "1"}
        with override_settings(GOOGLE_CLIENT_ID="cid"):
            with patch("users.google.id_token.verify_oauth2_token", return_value={**base, "email_verified": False}):
                with self.assertRaises(GoogleAuthError):
                    verify_google_credential("t")
            with patch("users.google.id_token.verify_oauth2_token", return_value={**base, "iss": "evil.example"}):
                with self.assertRaises(GoogleAuthError):
                    verify_google_credential("t")
            with patch("users.google.id_token.verify_oauth2_token", side_effect=ValueError("bad sig")):
                with self.assertRaises(GoogleAuthError):
                    verify_google_credential("t")
            with patch("users.google.id_token.verify_oauth2_token", return_value=base):
                self.assertEqual(verify_google_credential("t")["email"], "a@b.c")
