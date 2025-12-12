# -*- coding: utf-8 -*-
{
    "name": "UST Resume Management",
    "version": "1.0.0",
    "author": "Knysys",
    "category": "Website/eLearning",
    "summary": "إدارة السيرة الذاتية لأعضاء هيئة التدريس - Arabic RTL, preview & PDF",
    "description": "Resume management for academic staff. Backend + Portal + PDF QWeb RTL",
    "depends": ["base", "hr", "portal", "website", "website_slides", "elearning_colleges","base_user_role"],
    "data": [
        "security/ust_resume_security.xml",
        "security/ir.model.access.csv",
        "views/ust_resume_views.xml",
        "views/ust_resume_en_views.xml",
        # "views/portal_templates.xml",
        "reports/ust_resume_report_template.xml",
        "reports/ust_resume_report.xml",
        "views/ust_resume_menu.xml",
        "views/user.xml",
],
    "assets": {
        "web.assets_frontend": [
            "ust_resume_management/static/src/css/ust_resume.css",
        ]
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}

