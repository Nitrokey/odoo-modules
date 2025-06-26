import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class FirebaseTestController(http.Controller):

    @http.route('/firebase_notify/test', type='http', auth='user', website=True)
    def firebase_test_page(self):
        """Test page for Firebase notifications"""
        return request.render('firebase_notify.test_page', {
            'user': request.env.user,
        })

    @http.route('/firebase_notify/send_test', type='json', auth='user', methods=['POST'])
    def send_test_notification(self):
        """Send a test notification to the current user"""
        try:
            user = request.env.user
            
            if not user.firebase_notifications_enabled:
                return {
                    'success': False, 
                    'error': 'Firebase notifications not enabled for your user'
                }
            
            if not user.firebase_token:
                return {
                    'success': False, 
                    'error': 'No Firebase token registered for your user'
                }
            
            # Send test notification
            from odoo.addons.firebase_integration.tools.firebase import send_firebase_notifications
            
            test_messages = [{
                'token': user.firebase_token,
                'title': 'Test Notification from Odoo',
                'body': f'Hello {user.name}! Firebase notifications are working correctly.',
            }]
            
            success_count = send_firebase_notifications(test_messages, request.env)
            
            if success_count > 0:
                return {
                    'success': True,
                    'message': f'Test notification sent successfully to {user.name}'
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
                'error': f'Error: {str(e)}'
            }

    @http.route('/firebase_notify/simple_register', type='json', auth='user', methods=['POST'])
    def simple_register_token(self, token):
        """Simple token registration for testing"""
        try:
            if not token:
                return {'success': False, 'error': 'Token is required'}
            
            # Update current user's Firebase token
            request.env.user.write({
                'firebase_token': token,
                'firebase_notifications_enabled': True,
            })
            
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
