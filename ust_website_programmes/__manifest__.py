{
    'name': 'Ust Website Programmes Page',
    'description': 'Ust Website Prgrammes page',
    'category': 'Theme',
    'sequence': 10,
    'version': '18.0',
    'depends': ['website', ],
    'data': [
        'views/menu.xml',
        'views/admission.xml',
        'views/academic_programs.xml',
        'views/applied_college.xml',
        'views/postgraduate_academic_programs.xml',
        'views/postgraduate_addmission.xml',
        'views/postgraduate_applied_college.xml',
        'views/international_admission.xml',
        'views/international_academic_programs.xml',
        'views/international_applied_college.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'ust_website_programmes/static/src/css/responsive.css',
            'ust_website_programmes/static/src/css/slick.css',
            'ust_website_programmes/static/src/css/stylesheet.css',
            'ust_website_programmes/static/src/js/function.js',
            'ust_website_programmes/static/src/js/jquery.countup.js',
            'ust_website_programmes/static/src/js/jquery.waypoints.min.js',
            'ust_website_programmes/static/src/js/jquery.slick.min.js',

        ],
    },

    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
