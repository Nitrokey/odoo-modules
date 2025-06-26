import json
import logging
import os

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class FirebaseNotifyController(http.Controller):

    @http.route('/firebase-messaging-sw.js', type='http', auth='public', methods=['GET'])
    def firebase_messaging_sw(self):
        """Serve Firebase messaging service worker from root path"""
        try:
            import odoo.modules as addons
            # Get the module path using the correct method
            module_path = addons.get_module_path('firebase_notify')
            sw_path = os.path.join(module_path, 'static', 'firebase-messaging-sw.js')
            
            # Read the service worker file
            with open(sw_path, 'r', encoding='utf-8') as f:
                sw_content = f.read()
            
            # Return the service worker with proper headers
            return request.make_response(
                sw_content,
                headers=[
                    ('Content-Type', 'application/javascript'),
                    ('Service-Worker-Allowed', '/'),
                    ('Cache-Control', 'no-cache, no-store, must-revalidate'),
                    ('Pragma', 'no-cache'),
                    ('Expires', '0')
                ]
            )
        except Exception as e:
            _logger.error(f"Failed to serve service worker: {str(e)}")
            return request.not_found()

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
            
            # Check if web app configuration is available
            if not firebase_config.web_api_key or not firebase_config.web_project_id:
                return {
                    'success': False, 
                    'error': 'Firebase web app configuration not set. Please configure web app settings in Firebase Configuration.'
                }
            
            # Return web app configuration for client-side Firebase SDK
            web_config = {
                'apiKey': firebase_config.web_api_key,
                'authDomain': firebase_config.web_auth_domain or f"{firebase_config.web_project_id}.firebaseapp.com",
                'projectId': firebase_config.web_project_id,
                'storageBucket': firebase_config.web_storage_bucket or f"{firebase_config.web_project_id}.appspot.com",
                'messagingSenderId': firebase_config.web_messaging_sender_id,
                'appId': firebase_config.web_app_id,
            }
            
            return {
                'success': True,
                'config': web_config,
                'vapidKey': firebase_config.vapid_key
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

    @http.route('/firebase_notify/send_test', type='json', auth='user', methods=['POST'])
    def send_test_notification(self):
        """Send a test notification to the current user"""
        try:
            user = request.env.user
            
            if not user.firebase_notifications_enabled or not user.firebase_token:
                return {
                    'success': False,
                    'error': 'Firebase notifications not enabled or no token registered'
                }
            
            # Import Firebase tools
            firebase_tools = request.env['firebase.tools']
            
            # Send test notification
            result = firebase_tools.send_notification(
                user.firebase_token,
                'Test Notification',
                'This is a test notification from Odoo Firebase integration!',
                {
                    'test': True,
                    'user_id': user.id,
                    'timestamp': str(request.env.cr.now())
                }
            )
            
            if result:
                return {
                    'success': True,
                    'message': 'Test notification sent successfully!'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to send test notification'
                }
                
        except Exception as e:
            _logger.error(f"Failed to send test notification: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to send test notification: ' + str(e)
            }
