# -*- coding: utf-8 -*-
{
    "name": "UST Library",
    "version": "19.0.2.0.0",
    "summary": "University digital library: catalog, borrowing, reservations, portal, e-books, reviews, purchase requests, study spaces",
    "description": """
        Full-featured university library management system with:
        - Book catalog, copies, borrowing lifecycle
        - Student portal with search, filter, reserve, borrow
        - E-Book upload and online reading
        - Book reviews and ratings
        - Book recommendations
        - Purchase requests for missing books
        - Lost / damaged book incident management
        - Study room / seat booking with calendar
        - Automated notifications and penalty calculation
     """,
    "category": "Services/Library",
    "author": "UST ERP",
    "depends": ["base", "mail", "portal", "website"],

    "data": [
            "security/security.xml",
            "security/ir.model.access.csv",
            "data/sequence.xml",
            "data/penalty_rule.xml",
            "data/scheduled.xml",
            "data/mail_templates.xml",
            "views/library_author_view.xml",
            "views/library_publisher_view.xml",
            "views/library_category_view.xml",
            "views/library_book_view.xml",
            "views/library_book_copy_view.xml",
            "views/library_book_review_view.xml",
            "views/library_book_incident_view.xml",
            "views/library_borrow_view.xml",
            "views/library_purchase_request_view.xml",
            "views/library_space_view.xml",
            "views/library_space_booking_view.xml",
            "views/reports.xml",
            "views/res_partner_view.xml",
            "views/dashboard.xml",          # This is your backend dashboard
            "views/portal_templates.xml",   # This is your frontend portal
            "views/menu.xml",
            # DELETE THE TWO LINES BELOW FROM YOUR FILE:
            # 'views/library_dashboard_views.xml',  <-- DELETE THIS
            # 'views/website_library_templates.xml', <-- DELETE THIS
        ],
    "assets": {
        "web.assets_frontend": [
            "ust_library/static/src/css/library_calendar.css",
            "ust_library/static/src/js/library_calendar.js",
        ],
        "web.assets_backend": [
            "ust_library/static/src/css/library_dashboard.css",
            "ust_library/static/src/js/library_dashboard.js",
            "ust_library/static/src/xml/library_dashboard.xml",
        ],
    },
    "license": "LGPL-3",
    "installable": True,
    "application": True,
}
