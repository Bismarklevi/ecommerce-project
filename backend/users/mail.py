"""Email helpers.

Django's default mail encoding runs any text body through quoted-printable or
base64 (see django.core.mail.message.EmailMessage._add_bodies -> stdlib
email.message.EmailMessage.set_content), even when the body is pure ASCII.
For a short note that's invisible to the end user -- real mail clients decode
MIME transfer encoding transparently before rendering a clickable link -- but
it silently corrupts the *raw* message source: quoted-printable's 76-column
soft-wrapping can split a long URL (e.g. a password-reset link) across two
lines with literal "=3D"/"=" artifacts in between. That raw source is exactly
what the console backend prints, and exactly what some plain-text mail
gateways or log scrapers forward as-is, so anyone reading it (a developer
testing locally, a strict downstream relay) sees a broken link even though a
normal inbox would have rendered it correctly.

PlainAsciiEmailMessage sidesteps this by forcing Content-Transfer-Encoding:
7bit whenever the body is ASCII-safe, so the text -- links included --
reaches the wire byte-for-byte unchanged. It transparently falls back to
Django's normal (safe) encoding for any body containing non-ASCII text.
"""
import email.message as _email_message

from django.core.mail import EmailMessage


class PlainAsciiEmailMessage(EmailMessage):
    def message(self):
        msg = super().message()

        try:
            self.body.encode("ascii")
        except UnicodeEncodeError:
            # Non-ASCII content (e.g. an accented name) needs real MIME
            # encoding to survive transport -- let Django handle it normally.
            return msg

        plain = _email_message.EmailMessage()
        for key, value in msg.items():
            if key.lower() not in ("content-type", "content-transfer-encoding", "mime-version"):
                plain[key] = value
        plain.set_content(self.body, subtype=self.content_subtype, cte="7bit")
        return plain
