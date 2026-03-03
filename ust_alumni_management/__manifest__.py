# -*- coding: utf-8 -*-
{
    'name': 'UST Alumni Management',
    'version': '19.0.1.0.0',
    'author': 'UST',
    'category': 'Website/Human Resources',
    'summary': 'Comprehensive alumni management system with portal, website directory, and events',
    'description': """
        Alumni Management System
        ========================
        - Admin panel for managing alumni profiles
        - Portal access for alumni to manage their information
        - Employment verification workflow
        - Achievements management and verification
        - Website alumni directory with search and filters
        - Events integration for alumni
        - Reporting and dashboard
    """,
    'depends': [
        'base',
        'portal',
        'website',
        'mail',
        'hr',
        'website_event',
    ],
    'data': [
        'security/alumni_security.xml',
        'security/ir.model.access.csv',
        'data/mail_templates.xml',
        'views/alumni_profile_views.xml',
        'views/alumni_employment_views.xml',
        'views/alumni_achievement_views.xml',
        'views/alumni_import_wizard_views.xml',
        'views/alumni_employment_reject_wizard_views.xml',
        'views/event_views.xml',
        'views/portal_templates.xml',
        'views/website_templates.xml',
        'views/website_snippets.xml',
        'views/alumni_dashboard.xml',
        'views/alumni_menu.xml',
        'reports/alumni_reports.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'ust_alumni_management/static/src/css/alumni_portal.css',
            'ust_alumni_management/static/src/css/alumni_website.css',
            'ust_alumni_management/static/src/css/alumni_directory.css',
            'ust_alumni_management/static/src/css/alumni_profile.css',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
