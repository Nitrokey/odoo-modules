import json
import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class FirebaseNotifyController(http.Controller):

    @http.route('/firebase_notify/register_token', type='json', auth='user', methods=['POST'])
    def register_firebase_token(self, token):
        """Register Firebase token for the current user"""
        try:
            if not token:
                return {'success': False, 'error': 'Token is required'}
            
            # Update current user's Firebase token
            request.env.user.write({
                'firebase_token': token,
                'firebase_notifications_enabled': True,
            })
            
            _logger.info(f"Firebase token registered for user {request.env.user.name}")
            
            return {
                'success': True, 
                'message': 'Firebase token registered successfully'
            }
            
        except Exception as e:
            _logger.error(f"Failed to register Firebase token: {str(e)}")
            return {
                'success': False, 
                'error': 'Failed to register token'
            }

    @http.route('/firebase_notify/get_config', type='json', auth='user', methods=['POST'])
    def get_firebase_config(self):
        """Get Firebase configuration for web notifications"""
        try:
            # Get Firebase configuration from firebase_integration module
            firebase_config = request.env['firebase.config'].search([('is_active', '=', True)], limit=1)
            
            if not firebase_config:
                return {'success': False, 'error': 'No Firebase configuration found'}
            
            credentials = firebase_config.get_firebase_credentials()
            if not credentials:
                return {'success': False, 'error': 'Invalid Firebase credentials'}
            
            # Return only the necessary config for web notifications
            web_config = {
                'apiKey': credentials.get('api_key', ''),
                'authDomain': credentials.get('auth_domain', ''),
                'projectId': credentials.get('project_id', ''),
                'storageBucket': credentials.get('storage_bucket', ''),
                'messagingSenderId': credentials.get('messaging_sender_id', ''),
                'appId': credentials.get('app_id', ''),
            }
            
            return {
                'success': True,
                'config': web_config
            }
            
        except Exception as e:
            _logger.error(f"Failed to get Firebase config: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get Firebase configuration'
            }

    @http.route('/firebase_notify/status', type='json', auth='user', methods=['POST'])
    def get_notification_status(self):
        """Get current user's notification status"""
        try:
            user = request.env.user
            return {
                'success': True,
                'enabled': user.firebase_notifications_enabled,
                'has_token': bool(user.firebase_token),
                'token': user.firebase_token if user.firebase_token else None
            }
        except Exception as e:
            _logger.error(f"Failed to get notification status: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to get status'
            }
