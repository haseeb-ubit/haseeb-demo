from odoo import http
from odoo.http import request


class NewsViewsAllController(http.Controller):
    @http.route('/all-news', type='http', auth='public', website=True)
    def news_views_all_page(self):
        return request.render('ust_website_home.news_view_all_template', {})


@http.route('/news-details/<int:news_id>', type='http', auth="public", website=True)
def news_details(self, news_id, **kwargs):
    news_record = request.env['website.pagee'].sudo().browse(news_id)

    if not news_record.exists():
        return request.render("website.404")

    return request.render("ust_website_home.news_detail_template", {
        'news': news_record
    })


class BlogsViewAllController(http.Controller):
    @http.route('/all-blog', type='http', auth='public', website=True)
    def blogs_views_all_page(self):
        return request.render('ust_website_home.blog_views_all_template', {})


class BlogDetailsController(http.Controller):
    @http.route('/blog-details', type='http', auth='public', website=True)
    def blog_details_page(self):
        return request.render('ust_website_home.blog_details_template', {})
