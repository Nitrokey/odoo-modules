/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, useState } from "@odoo/owl";

// Firebase SDK imports (these would need to be loaded externally)
// import { initializeApp } from 'firebase/app';
// import { getMessaging, getToken, onMessage } from 'firebase/messaging';

class FirebaseNotifyService {
    constructor(env, services) {
        this.env = env;
        this.rpc = services.rpc;
        this.notification = services.notification;
        this.firebaseApp = null;
        this.messaging = null;
        this.isInitialized = false;
    }

    async initialize() {
        if (this.isInitialized) {
            return;
        }

        try {
            // Check if Firebase SDK is available
            if (typeof firebase === 'undefined') {
                console.warn('Firebase SDK not loaded. Please include Firebase SDK in your page.');
                return;
            }

            // Get Firebase configuration from server
            const configResult = await this.rpc('/firebase_notify/get_config', {});
            
            if (!configResult.success) {
                console.warn('Firebase configuration not available:', configResult.error);
                return;
            }

            // Initialize Firebase
            this.firebaseApp = firebase.initializeApp(configResult.config);
            this.messaging = firebase.messaging();

            // Request notification permission
            const permission = await Notification.requestPermission();
            
            if (permission === 'granted') {
                await this.registerToken();
                this.setupMessageListener();
            } else {
                console.warn('Notification permission denied');
            }

            this.isInitialized = true;

        } catch (error) {
            console.error('Failed to initialize Firebase:', error);
        }
    }

    async registerToken() {
        try {
            // Get registration token
            const token = await this.messaging.getToken({
                vapidKey: 'YOUR_VAPID_KEY' // This should be configured in Firebase console
            });

            if (token) {
                // Register token with Odoo
                const result = await this.rpc('/firebase_notify/register_token', {
                    token: token
                });

                if (result.success) {
                    this.notification.add('Firebase notifications enabled successfully!', {
                        type: 'success'
                    });
                } else {
                    console.error('Failed to register token:', result.error);
                }
            }

        } catch (error) {
            console.error('Failed to get Firebase token:', error);
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
        });
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
registry.category("services").add("firebase_notify", {
    dependencies: ["rpc", "notification"],
    start(env, services) {
        const service = new FirebaseNotifyService(env, services);
        
        // Auto-initialize when service starts
        service.initialize();
        
        return service;
    },
});

// Component for Firebase notification settings
export class FirebaseNotifyWidget extends Component {
    setup() {
        this.firebaseService = useService("firebase_notify");
        this.state = useState({
            enabled: false,
            hasToken: false,
            loading: false
        });

        onMounted(async () => {
            await this.loadStatus();
        });
    }

    async loadStatus() {
        this.state.loading = true;
        try {
            const status = await this.firebaseService.getStatus();
            if (status.success) {
                this.state.enabled = status.enabled;
                this.state.hasToken = status.has_token;
            }
        } catch (error) {
            console.error('Failed to load Firebase status:', error);
        } finally {
            this.state.loading = false;
        }
    }

    async enableNotifications() {
        this.state.loading = true;
        try {
            await this.firebaseService.initialize();
            await this.loadStatus();
        } catch (error) {
            console.error('Failed to enable notifications:', error);
        } finally {
            this.state.loading = false;
        }
    }
}

FirebaseNotifyWidget.template = "firebase_notify.FirebaseNotifyWidget";

// Register the component
registry.category("public_components").add("FirebaseNotifyWidget", FirebaseNotifyWidget);
