{
    'name': 'Ust website aboutus page',
    'description': 'Ust website aboutus page',
    'category': 'Theme',
    'sequence': 10,
    'version': '18.0',
    'depends': ['website',],
    'data': [
       'views/about_us.xml',
        'views/menu.xml',
      'views/university_president.xml',
        'views/certficates_achievements.xml',
        'views/facts-and-figure.xml',

    ],

    'assets': {
        'web.assets_frontend': [
            'ust_website_aboutus/static/src/css/responsive.css',
            'ust_website_aboutus/static/src/css/slick.css',
            'ust_website_aboutus/static/src/css/stylesheet.css',
            'ust_website_aboutus/static/src/js/function.js',
            'ust_website_aboutus/static/src/js/jquery.countup.js',
            'ust_website_aboutus/static/src/js/jquery.waypoints.min.js',
            'ust_website_aboutus/static/src/js/jquery.slick.min.js',

        ],

    },


    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}