from odoo import http
from odoo.http import request


class BlogController(http.Controller):
    @http.route(['/blog', '/blog/page/<int:page>'], type='http', auth='public', website=True)
    def blog_list(self, page=1, **kwargs):
        Blog = request.env['website.blogs'].sudo()
        domain = [('publish', '=', True)]
        page_size = 9

        total = Blog.search_count(domain)
        pager = request.website.pager(url='/blog', total=total, page=page, step=page_size)
        records = Blog.search(domain, order='blogs_date asc, sequence asc', limit=page_size, offset=pager['offset'])

        values = {
            'blog_list': records,
            'pager': pager,
        }
        return request.render('ust_website_news.template_blog_list', values)

    @http.route(['/blog/<string:slug>'], type='http', auth='public', website=True)
    def blog_detail(self, slug, **kwargs):
        """Handle blog detail by URL slug"""
        Blog = request.env['website.blogs'].sudo()
        lang = request.env.context.get('lang') if request.env.context else ''

        # First, try to find by url_slug
        blog = Blog.search([('url_slug', '=', slug), ('publish', '=', True)], limit=1)

        # If not found by slug, check if it's an old ID-based URL or slug with ID
        if not blog:
            # Try to extract ID from slug (e.g., "my-blog-3" -> 3)
            parts = slug.split('-')
            if parts and parts[-1].isdigit():
                blog_id = int(parts[-1])
                blog = Blog.browse(blog_id)

                # Check if blog exists and is published
                if not blog.exists() or not blog.publish:
                    blog = False

            # If still not found and slug is just a number, try by ID
            if not blog and slug.isdigit():
                blog = Blog.browse(int(slug))
                if not blog.exists() or not blog.publish:
                    blog = False

        # If still not found, return 404
        if not blog:
            return request.not_found()

        # If the URL slug doesn't match the current slug, redirect to correct URL
        if blog.url_slug and blog.url_slug != slug:
            return request.redirect(f'/blog/{blog.url_slug}', code=301)

        return request.render('ust_website_news.template_blog_detail', {'blog': blog, 'lang': lang})
