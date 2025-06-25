import logging

import firebase_admin
from firebase_admin import credentials, messaging

_logger = logging.getLogger(__name__)

# Global variable to store the Firebase app instance
firebase_app = None


def _get_firebase_app(env):
    """Get or initialize Firebase app with credentials from database"""
    global firebase_app

    if firebase_app is not None:
        return firebase_app

    try:
        firebase_config = env["firebase.config"].search(
            [("is_active", "=", True)], limit=1
        )
        if not firebase_config:
            _logger.error("No active Firebase configuration found")
            return None

        credentials_dict = firebase_config.get_firebase_credentials()
        if not credentials_dict:
            _logger.error("No Firebase credentials found in configuration")
            return None

        # Initialize Firebase app with credentials from database
        firebase_cred = credentials.Certificate(credentials_dict)
        firebase_app = firebase_admin.initialize_app(firebase_cred)
        _logger.info("Firebase app initialized successfully")
        return firebase_app

    except Exception as e:
        _logger.error(f"Failed to initialize Firebase app: {str(e)}")
        return None


def send_firebase_notifications(messages, env=None) -> int:
    """
    [
        {'token':'','body':'','title':''},
        {'token':'','body':'','title':''}
    ]
    :param messages:
    :param env: Odoo environment (optional, will create if not provided)
    :return: successfully send message count
    """
    if env is None:
        # This approach requires the caller to pass the environment
        _logger.error("Environment parameter is required for Firebase notifications")
        return 0

    app = _get_firebase_app(env)
    if not app:
        _logger.error("Firebase app not initialized. Cannot send notifications.")
        return 0

    try:
        messages = list(
            map(
                lambda msg: messaging.Message(
                    notification=messaging.Notification(
                        msg.get("title"), msg.get("body")
                    ),
                    token=msg.get("token"),
                ),
                messages,
            )
        )
        response = messaging.send_each(messages, app=app)
        return response.success_count
    except Exception as e:
        _logger.error(f"Failed to send Firebase notifications: {str(e)}")
        return 0
