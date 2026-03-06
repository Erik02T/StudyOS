import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from app.core.config import get_settings


class EmailProviderService:
    @staticmethod
    def send_email(to_email: str, subject: str, text_body: str, html_body: str) -> str:
        settings = get_settings()
        provider = settings.email_provider.lower().strip()
        if provider == "smtp":
            return EmailProviderService._send_smtp(to_email, subject, text_body, html_body)
        if provider == "resend":
            return EmailProviderService._send_resend(to_email, subject, html_body)
        return EmailProviderService._send_console(to_email, subject, text_body, html_body)

    @staticmethod
    def _send_console(to_email: str, subject: str, text_body: str, html_body: str) -> str:
        print("=== EMAIL(CONSOLE) ===")
        print("to:", to_email)
        print("subject:", subject)
        print("text:", text_body)
        print("html:", html_body)
        print("======================")
        return f"console:{to_email}:{subject}"

    @staticmethod
    def _send_smtp(to_email: str, subject: str, text_body: str, html_body: str) -> str:
        settings = get_settings()
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.email_from
        msg["To"] = to_email
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.email_smtp_host, settings.email_smtp_port, timeout=20) as server:
            if settings.email_smtp_use_tls:
                server.starttls()
            if settings.email_smtp_username:
                server.login(settings.email_smtp_username, settings.email_smtp_password)
            server.sendmail(settings.email_from, [to_email], msg.as_string())
        return f"smtp:{to_email}"

    @staticmethod
    def _send_resend(to_email: str, subject: str, html_body: str) -> str:
        settings = get_settings()
        if not settings.email_resend_api_key:
            raise RuntimeError("Resend API key is not configured")
        payload = {
            "from": settings.email_from,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }
        headers = {"Authorization": f"Bearer {settings.email_resend_api_key}"}
        response = httpx.post(settings.email_resend_base_url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        return data.get("id", "resend:ok")

