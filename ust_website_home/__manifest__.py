{
    'name': 'Ust website odoo',
    'description': 'Ust website odoo',
    'category': 'Theme',
    'sequence': 10,
    'version': '19.0.0.0.0',
    'depends': ['base', 'website', 'web', ],
    'data': [
        'views/header.xml',
        'views/home_page.xml',
        'views/footer.xml',
        'views/header_before.xml',
        'views/news.xml',
        'views/news_details.xml',
        'views/blog.xml',
        'views/blog_details.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'web/static/lib/zoomodoo/zoomodoo.js',
            'ust_website_home/static/src/css/responsive.css',
            'ust_website_home/static/src/css/slick.css',
            'ust_website_home/static/src/css/stylesheet.css',
            'ust_website_home/static/src/js/function.js',
            'ust_website_home/static/src/js/jquery.countup.js',
            'ust_website_home/static/src/js/jquery.waypoints.min.js',
            'ust_website_home/static/src/js/jquery.slick.min.js',

        ],
    },

    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
