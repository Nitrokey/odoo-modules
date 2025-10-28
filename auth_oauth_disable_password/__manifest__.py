{
    "name": "OAuth Disable Password Login",
    "version": "15.0.1.0.0",
    "category": "Hidden",
    "author": "initOS GmbH",
    "website": "https://www.initos.com",
    "license": "AGPL-3",
    "summary": "Disable password login when OAuth login is enabled for the user",
    "depends": [
        "auth_oauth",
    ],
    "data": [
        "views/res_users_views.xml",
    ],
    "installable": True,
}
