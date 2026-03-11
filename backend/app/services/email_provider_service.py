import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import httpx

from app.core.config import get_settings


class EmailProviderService:
    @staticmethod
    def send_email(to_email: str, subject: str, text_body: str, html_body: str) -> str:
        settings = get_settings()
        provider = settings.email.provider.lower().strip()
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
        msg["From"] = settings.email.from_address
        msg["To"] = to_email
        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(settings.email.smtp_host, settings.email.smtp_port, timeout=20) as server:
            if settings.email.smtp_use_tls:
                server.starttls()
            if settings.email.smtp_username:
                server.login(settings.email.smtp_username, settings.email.smtp_password)
            server.sendmail(settings.email.from_address, [to_email], msg.as_string())
        return f"smtp:{to_email}"

    @staticmethod
    def _send_resend(to_email: str, subject: str, html_body: str) -> str:
        settings = get_settings()
        if not settings.email.resend_api_key:
            raise RuntimeError("Resend API key is not configured")
        payload = {
            "from": settings.email.from_address,
            "to": [to_email],
            "subject": subject,
            "html": html_body,
        }
        headers = {"Authorization": f"Bearer {settings.email.resend_api_key}"}
        response = httpx.post(settings.email.resend_base_url, json=payload, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        return data.get("id", "resend:ok")
