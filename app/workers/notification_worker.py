from app.database import SessionLocal
from app.services.notification_service import NotificationService


class NotificationWorker:
    """
    Worker that processes the notification queue and sends notifications.
    """

    def __init__(self):
        self.notification_service = NotificationService()

    async def run_notification_pipeline(self):
        """
        Process all pending notifications in the queue.
        """
        print("\n" + "="*60)
        print("[NOTIFICATION WORKER] Starting notification processing")
        print("="*60 + "\n")

        db = SessionLocal()

        try:
            await self.notification_service.process_notification_queue(db)

            print("\n" + "="*60)
            print("[NOTIFICATION WORKER] Notification processing complete")
            print("="*60 + "\n")

        except Exception as e:
            print(f"[NOTIFICATION WORKER] Error in notification pipeline: {str(e)}")
        finally:
            db.close()
