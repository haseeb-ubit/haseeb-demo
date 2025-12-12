{
    'name': 'Ust website News',
    'description': 'Ust website News',
    'category': 'Theme',
    'sequence': 10,
    'version': '18.0',
    'depends': ['base', 'mail', 'website', 'ust_website_home'],
    'data': [
        'security/ir.model.access.csv',
        'views/news.xml',
        'views/blogs.xml',
        'views/upload_image.xml',
        'views/blog_upload_image.xml',
        'views/blog_template.xml',
        'views/website_news_templates.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'ust_website_home/static/src/css/stylesheet.css',
            'ust_website_home/static/src/css/responsive.css',
            'ust_website_home/static/src/css/slick.css',
        ],
        'web_editor.assets_snippets_menu': [
            'ust_website_news/static/src/js/web-editor_patch.js',
        ],
        'web_editor.assets_wysiwyg': [
            'ust_website_news/static/src/js/web-editor_patch.js',
        ]
    },

    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
