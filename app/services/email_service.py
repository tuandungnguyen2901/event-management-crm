import uuid
import boto3
import os
from datetime import datetime
from typing import List, Optional
from botocore.exceptions import ClientError

from app.config.database import db_config
from app.models.email import EmailSent, EmailSentCreate, EmailStatus, EmailSendRequest, EmailSendResponse, EmailTrackingResponse
from app.models.user import User


class EmailService:
    def __init__(self):
        self.table = db_config.get_table('emails')
        self.ses_client = boto3.client('ses', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.sender_email = os.getenv('SES_SENDER_EMAIL', 'noreply@example.com')
        self.mock_mode = os.getenv('EMAIL_MOCK_MODE', 'true').lower() == 'true'

    async def send_emails_to_users(self, request: EmailSendRequest, users: List[User]) -> EmailSendResponse:
        """Send emails to a list of users"""
        email_ids = []
        total_sent = 0
        total_failed = 0
        
        for user in users:
            if user.id in request.userIds:
                try:
                    email_data = EmailSentCreate(
                        userId=user.id,
                        recipientEmail=user.email,
                        subject=request.subject,
                        message=request.message,
                        status=EmailStatus.pending
                    )
                    
                    # Create email record
                    email_record = await self.create_email_record(email_data)
                    email_ids.append(email_record.id)
                    
                    # Send email
                    success = await self.send_single_email(
                        email_record.id,
                        user.email,
                        request.subject,
                        request.message,
                        user.firstName
                    )
                    
                    if success:
                        total_sent += 1
                        await self.update_email_status(email_record.id, EmailStatus.sent)
                    else:
                        total_failed += 1
                        await self.update_email_status(email_record.id, EmailStatus.failed)
                        
                except Exception as e:
                    print(f"Failed to send email to user {user.id}: {e}")
                    total_failed += 1
        
        return EmailSendResponse(
            emailIds=email_ids,
            totalSent=total_sent,
            totalFailed=total_failed,
            message=f"Sent {total_sent} emails successfully, {total_failed} failed"
        )

    async def create_email_record(self, email_data: EmailSentCreate) -> EmailSent:
        """Create a new email record in DynamoDB"""
        email_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        email_item = {
            'id': email_id,
            'userId': email_data.userId,
            'recipientEmail': email_data.recipientEmail,
            'subject': email_data.subject,
            'message': email_data.message,
            'status': email_data.status.value,
            'sentAt': None,
            'openedAt': None,
            'createdAt': now.isoformat(),
            'updatedAt': now.isoformat()
        }
        
        try:
            self.table.put_item(Item=email_item)
            return EmailSent(**email_item)
        except ClientError as e:
            raise Exception(f"Failed to create email record: {e.response['Error']['Message']}")

    async def send_single_email(self, email_id: str, recipient: str, subject: str, message: str, first_name: str) -> bool:
        """Send a single email via SES or mock"""
        try:
            if self.mock_mode:
                # Mock email sending for development
                print(f"MOCK EMAIL SEND:")
                print(f"To: {recipient}")
                print(f"Subject: {subject}")
                print(f"Message: {message[:100]}...")
                print(f"Tracking URL: {self._get_tracking_url(email_id)}")
                return True
            else:
                # Real SES email sending
                html_body = self._create_html_email(message, first_name, email_id)
                text_body = self._create_text_email(message, first_name)
                
                response = self.ses_client.send_email(
                    Source=self.sender_email,
                    Destination={'ToAddresses': [recipient]},
                    Message={
                        'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                        'Body': {
                            'Html': {'Data': html_body, 'Charset': 'UTF-8'},
                            'Text': {'Data': text_body, 'Charset': 'UTF-8'}
                        }
                    }
                )
                
                print(f"Email sent to {recipient}, Message ID: {response['MessageId']}")
                return True
                
        except ClientError as e:
            print(f"Failed to send email to {recipient}: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error sending email to {recipient}: {e}")
            return False

    async def update_email_status(self, email_id: str, status: EmailStatus, opened_at: Optional[datetime] = None) -> bool:
        """Update email status and timestamps"""
        try:
            now = datetime.utcnow()
            update_expression = "SET #status = :status, updatedAt = :updated_at"
            expression_values = {
                ':status': status.value,
                ':updated_at': now.isoformat()
            }
            expression_names = {'#status': 'status'}
            
            if status == EmailStatus.sent:
                update_expression += ", sentAt = :sent_at"
                expression_values[':sent_at'] = now.isoformat()
            elif status == EmailStatus.opened and opened_at:
                update_expression += ", openedAt = :opened_at"
                expression_values[':opened_at'] = opened_at.isoformat()
            
            self.table.update_item(
                Key={'id': email_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ExpressionAttributeNames=expression_names
            )
            return True
            
        except ClientError as e:
            print(f"Failed to update email status: {e}")
            return False

    async def track_email_open(self, email_id: str) -> EmailTrackingResponse:
        """Track email open and return tracking pixel"""
        try:
            # Get email record
            response = self.table.get_item(Key={'id': email_id})
            if 'Item' not in response:
                return EmailTrackingResponse(
                    emailId=email_id,
                    status=EmailStatus.failed,
                    openedAt=None,
                    message="Email not found"
                )
            
            email_record = EmailSent(**response['Item'])
            
            # Update status to opened if not already opened
            if email_record.status != EmailStatus.opened:
                opened_at = datetime.utcnow()
                await self.update_email_status(email_id, EmailStatus.opened, opened_at)
                
                return EmailTrackingResponse(
                    emailId=email_id,
                    status=EmailStatus.opened,
                    openedAt=opened_at,
                    message="Email tracking updated"
                )
            else:
                return EmailTrackingResponse(
                    emailId=email_id,
                    status=EmailStatus.opened,
                    openedAt=email_record.openedAt,
                    message="Email already tracked as opened"
                )
                
        except Exception as e:
            print(f"Failed to track email open: {e}")
            return EmailTrackingResponse(
                emailId=email_id,
                status=EmailStatus.failed,
                openedAt=None,
                message=f"Error tracking email: {str(e)}"
            )

    def _get_tracking_url(self, email_id: str) -> str:
        """Generate tracking URL for email"""
        base_url = os.getenv('API_BASE_URL', 'https://api.example.com')
        return f"{base_url}/track/open?emailId={email_id}"

    def _create_html_email(self, message: str, first_name: str, email_id: str) -> str:
        """Create HTML email with tracking pixel"""
        tracking_url = self._get_tracking_url(email_id)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Event Management CRM</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Hello {first_name}!</h2>
                
                <div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    {message.replace(chr(10), '<br>')}
                </div>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <p style="font-size: 12px; color: #666;">
                    This email was sent from Event Management CRM System.
                </p>
                
                <!-- Tracking pixel -->
                <img src="{tracking_url}" width="1" height="1" style="display: none;" alt="">
            </div>
        </body>
        </html>
        """
        
        return html_content

    def _create_text_email(self, message: str, first_name: str) -> str:
        """Create plain text email"""
        return f"""
Hello {first_name}!

{message}

---
This email was sent from Event Management CRM System.
        """.strip()

    async def get_email_stats(self, user_id: Optional[str] = None) -> dict:
        """Get email statistics"""
        try:
            scan_kwargs = {}
            
            if user_id:
                scan_kwargs['FilterExpression'] = 'userId = :user_id'
                scan_kwargs['ExpressionAttributeValues'] = {':user_id': user_id}
            
            response = self.table.scan(**scan_kwargs)
            emails = [EmailSent(**item) for item in response['Items']]
            
            stats = {
                'total': len(emails),
                'sent': len([e for e in emails if e.status == EmailStatus.sent]),
                'opened': len([e for e in emails if e.status == EmailStatus.opened]),
                'failed': len([e for e in emails if e.status == EmailStatus.failed]),
                'pending': len([e for e in emails if e.status == EmailStatus.pending])
            }
            
            if stats['sent'] > 0:
                stats['open_rate'] = round((stats['opened'] / stats['sent']) * 100, 2)
            else:
                stats['open_rate'] = 0
                
            return stats
            
        except Exception as e:
            print(f"Failed to get email stats: {e}")
            return {'error': str(e)}


# Global instance
email_service = EmailService() 