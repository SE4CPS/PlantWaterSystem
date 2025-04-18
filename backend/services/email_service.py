import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL')

    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_content: Optional[str] = None
    ) -> dict:
        """
        Send an email to a single recipient.
        
        Args:
            to_email: Recipient's email address
            subject: Email subject
            body: Plain text email body
            html_content: Optional HTML version of the email body
            
        Returns:
            dict: Status of the email sending operation
        """
        try:
            # Create message container
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            # Create the body of the message
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)

            # Attach HTML content if provided
            if html_content:
                html_part = MIMEText(html_content, 'html')
                msg.attach(html_part)

            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            return {
                "status": "success",
                "message": f"Email sent successfully to {to_email}"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def send_bulk_email(
        self,
        to_emails: List[str],
        subject: str,
        body: str,
        html_content: Optional[str] = None
    ) -> dict:
        """
        Send an email to multiple recipients.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            body: Plain text email body
            html_content: Optional HTML version of the email body
            
        Returns:
            dict: Status of the email sending operation
        """
        try:
            # Create message container
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = ', '.join(to_emails)

            # Create the body of the message
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)

            # Attach HTML content if provided
            if html_content:
                html_part = MIMEText(html_content, 'html')
                msg.attach(html_part)

            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            return {
                "status": "success",
                "message": f"Email sent successfully to {len(to_emails)} recipients"
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def send_moisture_alert(
        self,
        to_email: str,
        plant_name: str,
        current_moisture: float,
        threshold: float,
        location: str
    ) -> dict:
        """
        Send a moisture alert email when plant moisture level is below threshold.
        
        Args:
            to_email: Recipient's email address
            plant_name: Name of the plant
            current_moisture: Current moisture level
            threshold: Moisture threshold
            location: Plant location
            
        Returns:
            dict: Status of the email sending operation
        """
        subject = f"Moisture Alert: {plant_name} needs water!"
        
        # Plain text version
        body = f"""
        Dear Plant Owner,

        Your plant '{plant_name}' needs attention!

        Current moisture level: {current_moisture}%
        Threshold: {threshold}%
        Location: {location}

        Please water your plant soon to maintain its health.

        Best regards,
        Plant Watering System
        """

        # HTML version
        html_content = f"""
        <html>
            <body>
                <h2>Moisture Alert: {plant_name} needs water!</h2>
                <p>Dear Plant Owner,</p>
                <p>Your plant '{plant_name}' needs attention!</p>
                <ul>
                    <li>Current moisture level: {current_moisture}%</li>
                    <li>Threshold: {threshold}%</li>
                    <li>Location: {location}</li>
                </ul>
                <p>Please water your plant soon to maintain its health.</p>
                <p>Best regards,<br>Plant Watering System</p>
            </body>
        </html>
        """

        return self.send_email(to_email, subject, body, html_content)
