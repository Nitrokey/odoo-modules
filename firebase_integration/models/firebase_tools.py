from odoo import models
from ..tools import firebase
import logging

_logger = logging.getLogger(__name__)


class FirebaseTools(models.AbstractModel):
    _name = 'firebase.tools'
    _description = 'Firebase Tools for sending notifications'

    def send_notification(self, token, title, body, data=None):
        """
        Send a single Firebase notification
        
        Args:
            token (str): Firebase registration token
            title (str): Notification title
            body (str): Notification body
            data (dict, optional): Additional data payload
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not token or not title or not body:
            _logger.warning("Missing required parameters for Firebase notification")
            return False
            
        try:
            _logger.info(f"Sending Firebase notification to token: {token[:20]}...")
            _logger.info(f"Title: {title}, Body: {body}")
            
            messages = [{
                'token': token,
                'title': title,
                'body': body,
                'data': data or {}
            }]
            
            _logger.info("Calling firebase.send_firebase_notifications...")
            success_count = firebase.send_firebase_notifications(messages, self.env)
            _logger.info(f"Firebase notification success count: {success_count}")
            
            return success_count > 0
            
        except Exception as e:
            _logger.error(f"Exception in Firebase tools send_notification: {str(e)}", exc_info=True)
            return False

    def send_notifications(self, notifications):
        """
        Send multiple Firebase notifications
        
        Args:
            notifications (list): List of notification dictionaries
                Each dict should contain: token, title, body, data (optional)
                
        Returns:
            int: Number of successfully sent notifications
        """
        if not notifications:
            return 0
            
        try:
            return firebase.send_firebase_notifications(notifications, self.env)
        except Exception as e:
            _logger.error(f"Failed to send Firebase notifications: {str(e)}")
            return 0
