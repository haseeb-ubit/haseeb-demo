{
    'name': 'Ust website research and publications',
    'description': 'Ust website research and publications',
    'category': 'Theme',
    'sequence': 10,
    'version': '18.0',
    'depends': ['website', 'base'],
    'data': [
        'views/menus.xml',
        'views/research.xml',

    ],

    'assets': {
        'web.assets_frontend': [
            'ust_website_reseach_publications/static/src/css/responsive.css',
            'ust_website_reseach_publications/static/src/css/slick.css',
            'ust_website_reseach_publications/static/src/css/stylesheet.css',
            'ust_website_reseach_publications/static/src/js/function.js',
            'ust_website_reseach_publications/static/src/js/jquery.countup.js',
            'ust_website_reseach_publications/static/src/js/jquery.waypoints.min.js',
            'ust_website_reseach_publications/static/src/js/jquery.slick.min.js',

        ],
    },


    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
