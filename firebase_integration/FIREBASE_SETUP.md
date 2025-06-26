# Firebase Setup Guide for Odoo Integration

This guide explains how to set up Firebase for both server-side (notifications) and client-side (web browser notifications) integration.

## Prerequisites

1. A Firebase project (create at https://console.firebase.google.com)
2. Odoo with firebase_integration and firebase_notify modules installed

## Step 1: Create Firebase Project

1. Go to https://console.firebase.google.com
2. Click "Create a project"
3. Enter project name (e.g., "my-odoo-notifications")
4. Enable Google Analytics (optional)
5. Create project

## Step 2: Generate Service Account Key (Server-side)

1. In Firebase Console, go to **Project Settings** (gear icon)
2. Go to **Service accounts** tab
3. Click **"Generate new private key"**
4. Download the JSON file
5. Keep this file secure - it's for server-side operations

## Step 3: Create Web App (Client-side)

1. In Firebase Console, go to **Project Settings**
2. Go to **General** tab
3. Scroll down to **"Your apps"** section
4. Click **"Add app"** > **Web** (</> icon)
5. Enter app nickname (e.g., "Odoo Web")
6. **Enable "Firebase Hosting"** (optional)
7. Click **"Register app"**
8. Copy the **firebaseConfig** object - you'll need these values:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSyC...",           // Web API Key
  authDomain: "my-project.firebaseapp.com",
  projectId: "my-project",
  storageBucket: "my-project.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123"
};
```

## Step 4: Enable Cloud Messaging

1. In Firebase Console, go to **Cloud Messaging**
2. If prompted, enable Cloud Messaging API
3. Go to **Web configuration** tab
4. Generate a **Web Push Certificate (VAPID key)**:
   - Click "Generate key pair" if no key exists
   - Copy the VAPID key (starts with "B...")

## Step 5: Configure in Odoo

1. Go to **Settings > General Settings**
2. Find **"Firebase Integration"** section
3. Enable **"Enable Firebase Integration"**
4. Upload the **Firebase Private Key File** (service account JSON from Step 2)
5. Configure the **Web App Configuration** section with values from Step 3:
   - **Web API Key**: `apiKey` from firebaseConfig
   - **Auth Domain**: `authDomain` from firebaseConfig
   - **Project ID**: `projectId` from firebaseConfig
   - **Storage Bucket**: `storageBucket` from firebaseConfig
   - **Messaging Sender ID**: `messagingSenderId` from firebaseConfig
   - **App ID**: `appId` from firebaseConfig
   - **VAPID Key**: VAPID key from Step 4
6. Save settings

## Step 6: Test Configuration

1. Go to user preferences (your name > **Preferences**)
2. Enable **"Firebase Notifications"**
3. Click **"Enable Browser Notifications"**
4. Allow notifications when browser prompts
5. Click **"Test Notification"**
6. You should see a desktop notification!

## Troubleshooting

### "No Firebase configuration found"
- Ensure firebase_integration module is installed
- Check that Firebase configuration is marked as "Active"

### "Firebase web app configuration not set"
- Fill in all Web App Configuration fields in Firebase Configuration
- Use exact values from Firebase Console

### "VAPID key not configured"
- Generate VAPID key in Firebase Console
- Add it to Firebase Configuration in Odoo

### "Permission denied"
- Click "Allow" when browser asks for notification permission
- Check browser notification settings if blocked

### Network/Firewall Issues
- Ensure access to Firebase CDN: `www.gstatic.com`
- Check corporate firewall settings

## Security Notes

- **Service Account JSON**: Keep secure, contains private keys
- **Web API Key**: Can be public, used in browser
- **VAPID Key**: Used for web push, should be kept secure

## Testing Checklist

- [ ] Firebase project created
- [ ] Service account key downloaded
- [ ] Web app registered in Firebase
- [ ] Cloud Messaging enabled
- [ ] VAPID key generated
- [ ] Service account JSON uploaded to Odoo
- [ ] Web app configuration filled in Odoo
- [ ] Test notification button works
- [ ] Browser notifications appear
- [ ] Message notifications trigger automatically
