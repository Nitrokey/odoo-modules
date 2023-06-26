{
    "name": "Customer Profiling",
    "version": "15.0.1.0.0",
    "category": "Marketing",
    "license": "AGPL-3",
    "summary": """
This module allows users to perform segmentation within partners.
=================================================================

It uses the profiles criteria from the earlier segmentation module and
improve it. Thanks to the new concept of questionnaire. You can now regroup
questions into a questionnaire and directly use it on a partner.

It also has been merged with the earlier CRM & SRM segmentation tool
because they were overlapping.

**Note:** this module is not compatible with the module segmentation, since
it's the same which has been renamed.
    """,
    "author": "OpenERP SA",
    "website": "https://github.com/OCA/server-tools",
    "depends": ["account", "contacts", "queue_job_batch"],
    "data": [
        "security/ir.model.access.csv",
        "wizard/open_questionnaire_view.xml",
        "views/crm_profiling_view.xml",
        "views/crm_segmentation_view.xml",
    ],
    "installable": True,
    "auto_install": False,
    "images": [
        "images/profiling_questionnaires.jpeg",
        "images/profiling_questions.jpeg",
    ],
}
