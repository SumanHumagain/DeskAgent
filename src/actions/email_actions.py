"""
Email-related action handlers
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional, List


class EmailActions:
    """Handles email sending via SMTP"""

    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.email_address = os.getenv('EMAIL_ADDRESS')
        self.email_password = os.getenv('EMAIL_PASSWORD')

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: Optional[List[str]] = None
    ) -> str:
        """
        Send an email via SMTP

        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            attachments: Optional list of file paths to attach

        Returns:
            Success message
        """
        # Validate configuration
        if not self.email_address or not self.email_password:
            raise ValueError(
                "Email not configured. Set EMAIL_ADDRESS and EMAIL_PASSWORD in .env file"
            )

        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.email_address
        msg['To'] = to
        msg['Subject'] = subject

        # Add body
        msg.attach(MIMEText(body, 'plain'))

        # Add attachments
        if attachments:
            for file_path in attachments:
                self._attach_file(msg, file_path)

        # Send email
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_address, self.email_password)
                server.send_message(msg)

            attachment_info = f" with {len(attachments)} attachment(s)" if attachments else ""
            return f"Email sent to {to}{attachment_info}"

        except smtplib.SMTPAuthenticationError:
            raise ValueError(
                "Email authentication failed. Check EMAIL_ADDRESS and EMAIL_PASSWORD. "
                "For Gmail, use an app-specific password."
            )
        except Exception as e:
            raise RuntimeError(f"Failed to send email: {str(e)}")

    def _attach_file(self, msg: MIMEMultipart, file_path: str):
        """Attach a file to the email message"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Attachment not found: {file_path}")

        if not path.is_file():
            raise ValueError(f"Attachment path is not a file: {file_path}")

        # Read file and attach
        with open(path, 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())

        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {path.name}'
        )

        msg.attach(part)
