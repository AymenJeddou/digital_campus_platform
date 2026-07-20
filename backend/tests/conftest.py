"""Shared test setup.

These tests exercise the real register -> email -> verify -> login flow (they
patch send_verification_email and read the token from the mock call). That means
the email step must actually run, i.e. AUTO_VERIFY_EMAIL must be False.

A developer's local .env commonly sets AUTO_VERIFY_EMAIL=true so login works
without SMTP. Force it off here -- before app.main (and its Settings) is imported
by any test module -- so the suite is deterministic regardless of that .env.
Environment variables take precedence over .env values in pydantic-settings.
"""
import os

os.environ["AUTO_VERIFY_EMAIL"] = "False"
