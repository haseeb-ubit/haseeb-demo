{
    'name': 'Ust website university Study',
    'description': 'Ust website university study',
    'category': 'Theme',
    'sequence': 10,
    'version': '18.0',
    'depends': ['website', 'base'],
    'data': [
        'views/menus.xml',
        'views/international_language_center.xml',
        'views/handramout_branch.xml',
        'views/facilities_of_medicine.xml',
        'views/handramout_branch_details.xml',
        'views/the-faculty-of-humanities-administrative-sciences.xml',
        'views/deanship-of-e-learning-and-distance-eduction.xml',
        'views/deanship-of-postgraduate-studies-scientific-research.xml',
        'views/university_book_center.xml',
        'views/faculty-of-engineering-and-computing.xml',

    ],

    'assets': {
        'web.assets_frontend': [
            'ust_website_university_study/static/src/css/responsive.css',
            'ust_website_university_study/static/src/css/slick.css',
            'ust_website_university_study/static/src/css/stylesheet.css',
            'ust_website_university_study/static/src/js/function.js',
            'ust_website_university_study/static/src/js/jquery.countup.js',
            'ust_website_university_study/static/src/js/jquery.waypoints.min.js',
            'ust_website_university_study/static/src/js/jquery.slick.min.js',

        ],
    },

    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
