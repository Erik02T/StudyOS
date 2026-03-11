import datetime as dt
import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.email_job import EmailJob
from app.services.email_provider_service import EmailProviderService

logger = logging.getLogger(__name__)


class EmailQueueService:
    @staticmethod
    def enqueue(
        db: Session,
        to_email: str,
        subject: str,
        text_body: str,
        html_body: str,
    ) -> EmailJob:
        settings = get_settings()
        now = dt.datetime.utcnow()
        job = EmailJob(
            to_email=to_email,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            provider=settings.email.provider,
            status="pending",
            attempts=0,
            max_attempts=settings.email.max_attempts,
            next_attempt_at=now,
            last_error=None,
            provider_message_id=None,
            created_at=now,
            updated_at=now,
            sent_at=None,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def process_pending(db: Session, batch_size: int = 20) -> dict:
        now = dt.datetime.utcnow()
        jobs = (
            db.query(EmailJob)
            .filter(EmailJob.status.in_(["pending", "retrying"]), EmailJob.next_attempt_at <= now)
            .order_by(EmailJob.next_attempt_at.asc(), EmailJob.id.asc())
            .limit(batch_size)
            .all()
        )
        processed = 0
        sent = 0
        failed = 0
        retrying = 0

        for job in jobs:
            processed += 1
            job.status = "sending"
            job.updated_at = dt.datetime.utcnow()
            db.commit()
            try:
                provider_message_id = EmailProviderService.send_email(
                    to_email=job.to_email,
                    subject=job.subject,
                    text_body=job.text_body,
                    html_body=job.html_body,
                )
                job.status = "sent"
                job.sent_at = dt.datetime.utcnow()
                job.provider_message_id = provider_message_id
                job.last_error = None
                sent += 1
            except Exception as exc:
                job.attempts += 1
                job.last_error = str(exc)
                if job.attempts >= job.max_attempts:
                    job.status = "failed"
                    failed += 1
                else:
                    backoff_minutes = min(60, 2 ** min(job.attempts, 6))
                    job.status = "retrying"
                    job.next_attempt_at = dt.datetime.utcnow() + dt.timedelta(minutes=backoff_minutes)
                    retrying += 1
                logger.exception("email_send_failed", extra={"job_id": job.id})
            finally:
                job.updated_at = dt.datetime.utcnow()
                db.commit()

        return {"processed": processed, "sent": sent, "failed": failed, "retrying": retrying}

    @staticmethod
    def stats(db: Session) -> dict:
        counts = (
            db.query(EmailJob.status, func.count(EmailJob.id))
            .group_by(EmailJob.status)
            .all()
        )
        by_status = {status: count for status, count in counts}
        pending_oldest = (
            db.query(EmailJob)
            .filter(EmailJob.status.in_(["pending", "retrying"]))
            .order_by(EmailJob.created_at.asc())
            .first()
        )
        return {
            "by_status": by_status,
            "oldest_pending_created_at": str(pending_oldest.created_at) if pending_oldest else None,
            "oldest_pending_age_seconds": (
                int((dt.datetime.utcnow() - pending_oldest.created_at).total_seconds()) if pending_oldest else None
            ),
        }
