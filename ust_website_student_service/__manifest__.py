{
    'name': 'Ust website student service',
    'description': 'Ust website student service',
    'category': 'Theme',
    'sequence': 10,
    'version': '18.0',
    'depends': ['website'],
    'data': [
        'views/menus.xml',
        'views/exam_schedule.xml',
        'views/campus.xml',
        'views/college.xml',
        'views/study_schedules.xml',
        'views/academic-calendar.xml',
        'views/student-accommodation.xml',
        'views/forms.xml',
        'views/library.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'ust_website_student_service/static/src/css/responsive.css',
            'ust_website_student_service/static/src/css/slick.css',
            'ust_website_student_service/static/src/css/stylesheet.css',
            'ust_website_student_service/static/src/js/function.js',
            'ust_website_student_service/static/src/js/jquery.countup.js',
            'ust_website_student_service/static/src/js/jquery.waypoints.min.js',
            'ust_website_student_service/static/src/js/jquery.slick.min.js',

        ],
    },


    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
