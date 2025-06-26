/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class FirebaseRealNotifyService {
    constructor(env, services) {
        this.env = env;
        this.rpc = services.rpc;
        this.notification = services.notification;
        this.firebaseApp = null;
        this.messaging = null;
        this.isInitialized = false;
        this.isSDKLoaded = false;
    }

    async loadFirebaseSDK() {
        if (this.isSDKLoaded) {
            return true;
        }

        try {
            // Load Firebase SDK dynamically
            await this.loadScript('https://www.gstatic.com/firebasejs/9.23.0/firebase-app-compat.js');
            await this.loadScript('https://www.gstatic.com/firebasejs/9.23.0/firebase-messaging-compat.js');
            
            this.isSDKLoaded = true;
            console.log('Firebase SDK loaded successfully');
            return true;
        } catch (error) {
            console.error('Failed to load Firebase SDK:', error);
            return false;
        }
    }

    loadScript(src) {
        return new Promise((resolve, reject) => {
            // Check if script already exists
            if (document.querySelector(`script[src="${src}"]`)) {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    async initialize() {
        if (this.isInitialized) {
            return { success: true };
        }

        try {
            // Load Firebase SDK first
            const sdkLoaded = await this.loadFirebaseSDK();
            if (!sdkLoaded) {
                return { success: false, error: 'Failed to load Firebase SDK' };
            }

            // Get Firebase configuration from server
            const configResult = await this.rpc('/firebase_notify/get_config', {});
            
            if (!configResult.success) {
                return { success: false, error: configResult.error };
            }

            // Initialize Firebase
            if (!firebase.apps.length) {
                this.firebaseApp = firebase.initializeApp(configResult.config);
            } else {
                this.firebaseApp = firebase.app();
            }
            
            this.messaging = firebase.messaging();

            // Register service worker
            await this.registerServiceWorker();

            this.isInitialized = true;
            return { success: true };

        } catch (error) {
            console.error('Failed to initialize Firebase:', error);
            return { success: false, error: error.message };
        }
    }

    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/firebase_notify/static/firebase-messaging-sw.js');
                console.log('Service Worker registered:', registration);
                
                // Send Firebase config to service worker
                if (registration.active) {
                    const configResult = await this.rpc('/firebase_notify/get_config', {});
                    if (configResult.success) {
                        registration.active.postMessage({
                            type: 'FIREBASE_CONFIG',
                            config: configResult.config
                        });
                    }
                }
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }

    async requestPermissionAndRegisterToken() {
        try {
            // Request notification permission
            const permission = await Notification.requestPermission();
            
            if (permission !== 'granted') {
                return { 
                    success: false, 
                    error: 'Notification permission denied. Please allow notifications in your browser settings.' 
                };
            }

            // Get registration token
            const token = await this.messaging.getToken({
                vapidKey: 'BKxvxQ9K5G8X2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7A8B9C0D1E2F3G4H5I6J7K8L9M0N1O2P3Q4R5S6T7U8V9W0X1Y2Z3'
            });

            if (token) {
                // Register token with Odoo
                const result = await this.rpc('/firebase_notify/register_token', {
                    token: token
                });

                if (result.success) {
                    this.setupMessageListener();
                    return { 
                        success: true, 
                        message: 'Firebase notifications enabled successfully!',
                        token: token
                    };
                } else {
                    return { success: false, error: result.error };
                }
            } else {
                return { success: false, error: 'Failed to get Firebase token' };
            }

        } catch (error) {
            console.error('Failed to register token:', error);
            return { success: false, error: error.message };
        }
    }

    setupMessageListener() {
        // Listen for foreground messages
        this.messaging.onMessage((payload) => {
            console.log('Message received in foreground:', payload);
            
            // Show notification in Odoo
            this.notification.add(payload.notification.body, {
                title: payload.notification.title,
                type: 'info'
            });

            // Also show browser notification if permission granted
            if (Notification.permission === 'granted') {
                new Notification(payload.notification.title, {
                    body: payload.notification.body,
                    icon: '/firebase_notify/static/description/icon.png'
                });
            }
        });
    }

    async sendTestNotification() {
        try {
            const result = await this.rpc('/firebase_notify/send_test', {});
            return result;
        } catch (error) {
            console.error('Failed to send test notification:', error);
            return { success: false, error: error.message };
        }
    }

    async getStatus() {
        try {
            return await this.rpc('/firebase_notify/status', {});
        } catch (error) {
            console.error('Failed to get notification status:', error);
            return { success: false, error: error.message };
        }
    }
}

// Register the service
registry.category("services").add("firebase_real_notify", {
    dependencies: ["rpc", "notification"],
    start(env, services) {
        return new FirebaseRealNotifyService(env, services);
    },
});

// Create a global Firebase service instance
window.firebaseNotifyService = null;

// Initialize the service when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Create service instance directly
    window.firebaseNotifyService = new FirebaseRealNotifyService(
        null, // env
        {
            rpc: function(url, params) {
                return fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        jsonrpc: '2.0',
                        method: 'call',
                        params: params || {}
                    })
                }).then(response => response.json()).then(data => data.result);
            },
            notification: {
                add: function(message, options) {
                    console.log('Notification:', message, options);
                }
            }
        }
    );
});

// Global function for use in form views
window.enableFirebaseNotifications = async function() {
    if (!window.firebaseNotifyService) {
        alert('Firebase service not initialized. Please refresh the page and try again.');
        return;
    }

    try {
        // Initialize Firebase
        const initResult = await window.firebaseNotifyService.initialize();
        if (!initResult.success) {
            alert('Failed to initialize Firebase: ' + initResult.error);
            return;
        }

        // Request permission and register token
        const result = await window.firebaseNotifyService.requestPermissionAndRegisterToken();
        
        if (result.success) {
            alert('✅ ' + result.message);
            // Reload the form to show updated status
            window.location.reload();
        } else {
            alert('❌ Failed to enable notifications: ' + result.error);
        }
    } catch (error) {
        alert('❌ Error: ' + error.message);
        console.error('Firebase enable error:', error);
    }
};

// Global function for testing notifications
window.testFirebaseNotification = async function() {
    if (!window.firebaseNotifyService) {
        alert('Firebase service not initialized. Please refresh the page and try again.');
        return;
    }

    try {
        const result = await window.firebaseNotifyService.sendTestNotification();
        
        if (result.success) {
            alert('✅ Test notification sent! Check your browser for the notification.');
        } else {
            alert('❌ Failed to send test notification: ' + result.error);
        }
    } catch (error) {
        alert('❌ Error: ' + error.message);
        console.error('Firebase test error:', error);
    }
};
