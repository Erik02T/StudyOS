from app.core.config import get_settings


class EmailTemplates:
    @staticmethod
    def verification_link(token: str) -> str:
        settings = get_settings()
        return f"{settings.app.public_app_url.rstrip('/')}/verify-email?token={token}"

    @staticmethod
    def password_reset_link(token: str) -> str:
        settings = get_settings()
        return f"{settings.app.public_app_url.rstrip('/')}/reset-password?token={token}"

    @staticmethod
    def verify_email(email: str, token: str) -> tuple[str, str, str]:
        link = EmailTemplates.verification_link(token)
        subject = "Verify your StudyOS email"
        text = (
            f"Hi {email},\n\n"
            f"Use the link below to verify your email:\n{link}\n\n"
            "If you did not request this, ignore this message."
        )
        html = (
            f"<p>Hi {email},</p>"
            f"<p>Use the link below to verify your email:</p>"
            f"<p><a href='{link}'>{link}</a></p>"
            "<p>If you did not request this, ignore this message.</p>"
        )
        return subject, text, html

    @staticmethod
    def password_reset(email: str, token: str) -> tuple[str, str, str]:
        link = EmailTemplates.password_reset_link(token)
        subject = "Reset your StudyOS password"
        text = (
            f"Hi {email},\n\n"
            f"Use the link below to reset your password:\n{link}\n\n"
            "If you did not request this, ignore this message."
        )
        html = (
            f"<p>Hi {email},</p>"
            f"<p>Use the link below to reset your password:</p>"
            f"<p><a href='{link}'>{link}</a></p>"
            "<p>If you did not request this, ignore this message.</p>"
        )
        return subject, text, html
