from typing import List
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from discord_webhook import DiscordWebhook, DiscordEmbed
from sqlalchemy.orm import Session
from datetime import datetime

from app.config import settings
from app.models import User, JobPosting, Notification, NotificationQueue, NotificationChannel, NotificationStatus


class NotificationService:
    async def process_notification_queue(self, db: Session):
        """
        Process all pending notifications in the queue.

        Args:
            db: Database session
        """
        print("[NOTIFICATION] Processing notification queue...")

        # Get all pending notifications from queue
        queue_entries = db.query(NotificationQueue).all()

        if not queue_entries:
            print("[NOTIFICATION] No notifications in queue")
            return

        print(f"[NOTIFICATION] Processing {len(queue_entries)} queue entries")

        for entry in queue_entries:
            try:
                # Get user and job
                user = db.query(User).filter(User.id == entry.user_id).first()
                job = db.query(JobPosting).filter(JobPosting.id == entry.job_posting_id).first()

                if not user or not job:
                    print(f"[NOTIFICATION] User or job not found for queue entry {entry.id}")
                    db.delete(entry)
                    continue

                # Parse channels
                channels = entry.channels.split(",")

                # Send notification to each channel
                for channel in channels:
                    channel = channel.strip()
                    if channel == "email":
                        await self.send_email_notification(user, job, db)
                    elif channel == "discord":
                        await self.send_discord_notification(user, job, db)
                    elif channel == "dashboard":
                        await self.send_dashboard_notification(user, job, db)

                # Remove from queue after processing
                db.delete(entry)
                db.commit()

            except Exception as e:
                print(f"[NOTIFICATION] Error processing queue entry {entry.id}: {str(e)}")
                continue

        print("[NOTIFICATION] Queue processing complete")

    async def send_email_notification(self, user: User, job: JobPosting, db: Session):
        """
        Send email notification to user about new job.

        Args:
            user: User instance
            job: JobPosting instance
            db: Database session
        """
        print(f"[NOTIFICATION] Sending email to {user.email} for job {job.title}")

        try:
            # Create email content
            subject = f"New Job Match: {job.title} at {job.career_page.company_name}"
            html_body = self._create_email_html(user, job)

            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = settings.email_from
            message["To"] = user.email

            html_part = MIMEText(html_body, "html")
            message.attach(html_part)

            # Send email
            await aiosmtplib.send(
                message,
                hostname=settings.smtp_host,
                port=settings.smtp_port,
                username=settings.smtp_username,
                password=settings.smtp_password,
                start_tls=True
            )

            # Record notification
            notification = Notification(
                user_id=user.id,
                job_posting_id=job.id,
                channel=NotificationChannel.EMAIL,
                status=NotificationStatus.SENT,
                sent_at=datetime.utcnow()
            )
            db.add(notification)
            db.commit()

            print(f"[NOTIFICATION] Email sent successfully to {user.email}")

        except Exception as e:
            print(f"[NOTIFICATION] Failed to send email to {user.email}: {str(e)}")

            # Record failed notification
            notification = Notification(
                user_id=user.id,
                job_posting_id=job.id,
                channel=NotificationChannel.EMAIL,
                status=NotificationStatus.FAILED,
                error_message=str(e)
            )
            db.add(notification)
            db.commit()

    def _create_email_html(self, user: User, job: JobPosting) -> str:
        """
        Create HTML email body for job notification.

        Args:
            user: User instance
            job: JobPosting instance

        Returns:
            HTML string
        """
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #2c3e50;">New Job Match!</h2>

                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #3498db;">{job.title}</h3>
                    <p><strong>Company:</strong> {job.career_page.company_name}</p>
                    <p><strong>Location:</strong> {job.location or 'Not specified'}</p>
                    <p><strong>Job Type:</strong> {job.job_type or 'Not specified'}</p>
                    <p><strong>Experience Level:</strong> {job.experience_level or 'Not specified'}</p>
                </div>

                <div style="margin: 20px 0;">
                    <h4>Description:</h4>
                    <p>{job.description or 'No description available'}</p>
                </div>

                <div style="margin: 20px 0;">
                    <h4>Requirements:</h4>
                    <p>{job.requirements or 'No requirements specified'}</p>
                </div>

                <div style="margin: 30px 0;">
                    <a href="{job.url}"
                       style="background-color: #3498db; color: white; padding: 12px 24px;
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        View Job Posting
                    </a>
                </div>

                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">

                <p style="font-size: 12px; color: #7f8c8d;">
                    You received this email because it matches your job preferences.
                    To update your preferences or unsubscribe, please contact support.
                </p>
            </body>
        </html>
        """
        return html

    async def send_discord_notification(self, user: User, job: JobPosting, db: Session):
        """
        Send Discord webhook notification to user about new job.

        Args:
            user: User instance
            job: JobPosting instance
            db: Database session
        """
        print(f"[NOTIFICATION] Sending Discord notification for job {job.title}")

        if not user.discord_webhook_url:
            print(f"[NOTIFICATION] User {user.email} has no Discord webhook URL")
            return

        try:
            # Create Discord webhook
            webhook = DiscordWebhook(url=user.discord_webhook_url)

            # Create embed
            embed = DiscordEmbed(
                title=f"🎯 New Job Match: {job.title}",
                description=job.description or "No description available",
                color=0x3498db
            )

            embed.add_embed_field(name="Company", value=job.career_page.company_name, inline=True)
            embed.add_embed_field(name="Location", value=job.location or "Not specified", inline=True)
            embed.add_embed_field(name="Job Type", value=job.job_type or "Not specified", inline=True)
            embed.add_embed_field(name="Experience", value=job.experience_level or "Not specified", inline=True)

            if job.requirements:
                embed.add_embed_field(name="Requirements", value=job.requirements[:1024], inline=False)

            embed.add_embed_field(name="🔗 Apply", value=f"[View Job Posting]({job.url})", inline=False)

            embed.set_footer(text=f"Posted: {job.first_seen_at.strftime('%Y-%m-%d %H:%M')}")

            webhook.add_embed(embed)

            # Send webhook
            response = webhook.execute()

            # Record notification
            notification = Notification(
                user_id=user.id,
                job_posting_id=job.id,
                channel=NotificationChannel.DISCORD,
                status=NotificationStatus.SENT,
                sent_at=datetime.utcnow()
            )
            db.add(notification)
            db.commit()

            print(f"[NOTIFICATION] Discord notification sent successfully")

        except Exception as e:
            print(f"[NOTIFICATION] Failed to send Discord notification: {str(e)}")

            # Record failed notification
            notification = Notification(
                user_id=user.id,
                job_posting_id=job.id,
                channel=NotificationChannel.DISCORD,
                status=NotificationStatus.FAILED,
                error_message=str(e)
            )
            db.add(notification)
            db.commit()

    async def send_dashboard_notification(self, user: User, job: JobPosting, db: Session):
        """
        Create dashboard notification record (for web dashboard display).

        Args:
            user: User instance
            job: JobPosting instance
            db: Database session
        """
        print(f"[NOTIFICATION] Creating dashboard notification for user {user.email}")

        try:
            # Just create notification record - the dashboard will query these
            notification = Notification(
                user_id=user.id,
                job_posting_id=job.id,
                channel=NotificationChannel.DASHBOARD,
                status=NotificationStatus.SENT,
                sent_at=datetime.utcnow()
            )
            db.add(notification)
            db.commit()

            print(f"[NOTIFICATION] Dashboard notification created")

            # TODO: In future, send WebSocket message to connected clients
            # await websocket_manager.send_to_user(user.id, notification_data)

        except Exception as e:
            print(f"[NOTIFICATION] Failed to create dashboard notification: {str(e)}")
