{
    "name": "Discuss - Livekit Integration",
    "summary": "Integrate LiveKit video conferencing with Odoo Discuss",
    "version": "18.0.1.0.0",
    "author": "Odoo Community Association (OCA), Solvti Sp. z o.o.",
    "license": "LGPL-3",
    "category": "Discuss",
    "depends": ["mail"],
    "website": "https://www.solvti.com",
    "data": [
        "security/ir.model.access.csv",
        "data/ir_cron.xml",
        "views/res_config_settings_views.xml",
        "views/livekit_assets_templates.xml",
    ],
    "assets": {
        "mail_livekit.assets_livekit": [
            "mail_livekit/static/lib/livekit/livekit-client.umd.js",
            "mail_livekit/static/lib/livekit/livekit-track-processors.umd.min.js",
            "mail_livekit/static/src/discuss/livekit/*.js",
            "mail_livekit/static/src/discuss/*.js",
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
