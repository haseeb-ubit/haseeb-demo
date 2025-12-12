{
    'name': 'Ust website contactus page',
    'description': 'Ust website contactuus page',
    'category': 'Theme',
    'sequence': 10,
    'version': '18.0',
    'depends': ['website', ],

    'data': [
        'views/contact_us.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'ust_website_contactus/static/src/css/responsive.css',
            'ust_website_contactus/static/src/css/slick.css',
            'ust_website_contactus/static/src/css/stylesheet.css',
            'ust_website_contactus/static/src/js/function.js',
            'ust_website_contactus/static/src/js/jquery.countup.js',
            'ust_website_contactus/static/src/js/jquery.waypoints.min.js',
            'ust_website_contactus/static/src/js/jquery.slick.min.js',

        ],
    },

    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
