{
    'name': 'Ust website Applied College page',
    'description': 'Ust website Applied College page',
    'category': 'Theme',
    'sequence': 10,
    'version': '18.0',
    'depends': ['website', ],

    'data': [
        'views/menu.xml',
        'views/applied_college.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'ust_website_applied_college/static/src/css/responsive.css',
            'ust_website_applied_college/static/src/css/slick.css',
            'ust_website_applied_college/static/src/css/stylesheet.css',
            'ust_website_applied_college/static/src/js/function.js',
            'ust_website_applied_college/static/src/js/jquery.countup.js',
            'ust_website_applied_college/static/src/js/jquery.waypoints.min.js',
            'ust_website_applied_college/static/src/js/jquery.slick.min.js',

        ],
    },

    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
