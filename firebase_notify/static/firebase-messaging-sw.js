// Firebase Messaging Service Worker
// This file handles background notifications when the browser tab is not active

// Import Firebase scripts
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-app-compat.js');
importScripts('https://www.gstatic.com/firebasejs/9.0.0/firebase-messaging-compat.js');

// Initialize Firebase in the service worker
// Note: This configuration should match the one used in the main application
// The actual config will be loaded dynamically from the server
let firebaseConfig = null;

// Listen for messages from the main thread to get Firebase config
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'FIREBASE_CONFIG') {
        firebaseConfig = event.data.config;
        
        // Initialize Firebase with the received config
        if (!firebase.apps.length) {
            firebase.initializeApp(firebaseConfig);
        }
        
        // Initialize Firebase Messaging
        const messaging = firebase.messaging();
        
        // Handle background messages
        messaging.onBackgroundMessage((payload) => {
            console.log('Received background message:', payload);
            
            const notificationTitle = payload.notification.title || 'New Message';
            const notificationOptions = {
                body: payload.notification.body || 'You have a new message',
                icon: '/firebase_notify/static/description/icon.png',
                badge: '/firebase_notify/static/description/icon.png',
                tag: 'odoo-firebase-notification',
                requireInteraction: true,
                actions: [
                    {
                        action: 'open',
                        title: 'Open Odoo'
                    },
                    {
                        action: 'dismiss',
                        title: 'Dismiss'
                    }
                ]
            };
            
            // Show the notification
            self.registration.showNotification(notificationTitle, notificationOptions);
        });
    }
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
    console.log('Notification clicked:', event);
    
    event.notification.close();
    
    if (event.action === 'open' || !event.action) {
        // Open or focus the Odoo window
        event.waitUntil(
            clients.matchAll({ type: 'window' }).then((clientList) => {
                // Try to find an existing Odoo window
                for (const client of clientList) {
                    if (client.url.includes(self.location.origin) && 'focus' in client) {
                        return client.focus();
                    }
                }
                
                // If no existing window, open a new one
                if (clients.openWindow) {
                    return clients.openWindow('/web');
                }
            })
        );
    }
    // 'dismiss' action or any other action just closes the notification (already done above)
});

// Handle service worker installation
self.addEventListener('install', (event) => {
    console.log('Firebase messaging service worker installed');
    self.skipWaiting();
});

// Handle service worker activation
self.addEventListener('activate', (event) => {
    console.log('Firebase messaging service worker activated');
    event.waitUntil(self.clients.claim());
});
