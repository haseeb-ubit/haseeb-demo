from odoo import http
from odoo.http import request


class NewsController(http.Controller):
    @http.route(['/news', '/news/page/<int:page>'], type='http', auth='public', website=True)
    def news_list(self, page=1, **kwargs):
        News = request.env['website.pagee'].sudo()
        domain = [('publish', '=', True)]
        page_size = 9
        lang = request.env.context.get('lang') if request.env.context else ''
        total = News.search_count(domain)
        pager = request.website.pager(url='/news', total=total, page=page, step=page_size)
        records = News.search(domain, order='news_date desc, sequence asc', limit=page_size, offset=pager['offset'])
        values = {
            'news_list': records,
            'pager': pager,
            'lang': lang,
        }
        return request.render('ust_website_news.template_news_list', values)

    @http.route(['/news/<string:slug>'], type='http', auth='public', website=True)
    def news_detail(self, slug, **kwargs):
        """Handle news detail by URL slug"""
        News = request.env['website.pagee'].sudo()
        lang = request.env.context.get('lang') if request.env.context else ''
        # First, try to find by url_slug
        news = News.search([('url_slug', '=', slug), ('publish', '=', True)], limit=1)

        # If not found by slug, check if it's an old ID-based URL or slug with ID
        if not news:
            # Try to extract ID from slug (e.g., "phone-3" -> 3)
            parts = slug.split('-')
            if parts and parts[-1].isdigit():
                news_id = int(parts[-1])
                news = News.browse(news_id)

                # Check if news exists and is published
                if not news.exists() or not news.publish:
                    news = False

            # If still not found and slug is just a number, try by ID
            if not news and slug.isdigit():
                news = News.browse(int(slug))
                if not news.exists() or not news.publish:
                    news = False

        # If still not found, return 404
        if not news:
            return request.not_found()

        # If the URL slug doesn't match the current slug, redirect to correct URL
        if news.url_slug and news.url_slug != slug:
            return request.redirect(f'/news/{news.url_slug}', code=301)

        return request.render('ust_website_news.template_news_detail', {'news': news, 'lang': lang})