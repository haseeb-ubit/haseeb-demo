{
    'name': 'Ust website alumni club',
    'description': 'Ust website alumni club',
    'category': 'Theme',
    'sequence': 10,
    'version': '19.0.0.0.0',
    'depends': ['website',],
    'data': [
        'views/menus.xml',
        'views/university_verification.xml',
        'views/job_vacancies.xml',
        'views/alumni.xml'

    ],

    'assets': {
        'web.assets_frontend': [
            'ust_website_alumni_club/static/src/css/responsive.css',
            'ust_website_alumni_club/static/src/css/slick.css',
            'ust_website_alumni_club/static/src/css/stylesheet.css',
            'ust_website_alumni_club/static/src/js/function.js',
            'ust_website_alumni_club/static/src/js/jquery.countup.js',
            'ust_website_alumni_club/static/src/js/jquery.waypoints.min.js',
            'ust_website_alumni_club/static/src/js/jquery.slick.min.js',

        ],
    },



    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
