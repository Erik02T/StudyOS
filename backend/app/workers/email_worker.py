import time

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.email_queue_service import EmailQueueService


def run_once(batch_size: int = 50) -> dict:
    db = SessionLocal()
    try:
        return EmailQueueService.process_pending(db=db, batch_size=batch_size)
    finally:
        db.close()


def run_forever() -> None:
    settings = get_settings()
    while True:
        run_once()
        time.sleep(max(1, settings.email_worker_poll_seconds))


if __name__ == "__main__":
    run_forever()

