{
    "name": "Discuss - Livekit Integration",
    "summary": "Integrate LiveKit video conferencing with Odoo Discuss",
    "version": "18.0.1.0.2",
    "author": "Nitrokey GmbH, Solvti Sp. z o.o.",
    "license": "LGPL-3",
    "category": "Discuss",
    "depends": ["mail"],
    "website": "https://github.com/Nitrokey/odoo-modules/",
    "data": [
        "views/res_config_settings_views.xml",
        "views/livekit_assets_templates.xml",
    ],
    "assets": {
        "mail_livekit.assets_livekit": [
            "mail_livekit/static/lib/livekit/livekit-client.umd.min.js",
            "mail_livekit/static/src/discuss/livekit_service.js",
            "mail_livekit/static/src/discuss/livekit_adapter.js",
            "mail_livekit/static/src/discuss/rtc_livekit_patch.js",
            "mail_livekit/static/src/discuss/thread_actions_patch.js",
            "mail_livekit/static/src/discuss/call_participant_video_patch.js",
            "mail_livekit/static/src/discuss/call_context_menu_patch.js",
        ],
        "web.assets_unit_tests": [
            "mail_livekit/static/lib/livekit/livekit-client.umd.min.js",
            "mail_livekit/static/src/discuss/livekit_service.js",
            "mail_livekit/static/src/discuss/livekit_adapter.js",
            "mail_livekit/static/tests/**/*",
        ],
    },
    "external_dependencies": {
        "python": ["livekit-api"],
    },
    "reusable": False,
    "installable": True,
    "application": False,
    "auto_install": False,
}
