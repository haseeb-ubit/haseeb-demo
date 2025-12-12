from odoo import models, fields, api
import re
from odoo.exceptions import ValidationError


class WebsitePage(models.Model):
    _name = 'website.pagee'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Website News'
    _rec_name = 'news_title'

    news_title = fields.Char(string="Title", required=True)
    news_description = fields.Text(string="Description", required=True)
    news_title_arabic = fields.Char(string="Arabic Title")
    news_description_arabic  = fields.Text(string="Arabic Description")
    main_news = fields.Boolean(string="Main News", default=False)
    is_arabic_filled = fields.Boolean(string="is Arabic filled", default=False)
    news_date = fields.Datetime(string="Date", required=True, default=fields.Datetime.now)
    website_id = fields.Many2one('website', string="Website", required=True)

    # URL slug field - stores the slug part of the URL
    url_slug = fields.Char(
        string="URL Slug",
        copy=False,
        index=True,
        help="The URL-friendly identifier for this news item"
    )

    # URL field - shows and allows editing of full URL
    url = fields.Char(
        string="Website URL",
        compute='_compute_website_url',
        inverse='_set_website_url',
        help="The full URL to view this news item on the website. You can edit the slug part."
    )

    image = fields.Image(string="Image")
    publish = fields.Boolean(string="Published", default=False)
    short_description = fields.Text(string='Short Description')
    sequence = fields.Integer('Sequence', default=10)
    homepage = fields.Boolean(string="Home page News(s)", default=False)

    @api.model
    def create(self, vals):
        """Auto-generate URL slug from title if not provided"""
        if not vals.get('url_slug'):
            if vals.get('url'):
                # Extract slug from URL if provided
                vals['url_slug'] = self._extract_slug_from_url(vals['url'])
            elif vals.get('news_title'):
                # Generate from title
                vals['url_slug'] = self._generate_url_slug(vals['news_title'])
        if (not vals.get('news_title_arabic') and not vals.get('news_description_arabic') ):
            vals['news_description_arabic'] = vals.get('news_description')
            vals['news_title_arabic'] = vals.get('news_title')
        elif not vals.get('news_description_arabic'):
            vals['news_description_arabic'] = vals.get('news_description')
        elif not vals.get('news_title_arabic') :
            vals['news_title_arabic'] = vals.get('news_title')
        vals['is_arabic_filled'] = True
        return super(WebsitePage, self).create(vals)

    def write(self, vals):
        """Handle URL slug updates"""
        if 'url' in vals and 'url_slug' not in vals:
            vals['url_slug'] = self._extract_slug_from_url(vals['url'])
        if(not self.is_arabic_filled):
            if (not vals.get('news_title_arabic') and not vals.get('news_description_arabic')):
                vals['news_description_arabic'] = vals.get('news_description') or self.news_description
                vals['news_title_arabic'] = vals.get('news_title') or self.news_title
            elif not vals.get('news_description_arabic'):
                vals['news_description_arabic'] = vals.get('news_description') or self.news_description
            elif not vals.get('news_title_arabic'):
                vals['news_title_arabic'] = vals.get('news_title') or self.news_title
            vals['is_arabic_filled'] = True
        return super(WebsitePage, self).write(vals)

    def _generate_url_slug(self, name):
        """Generate a URL-friendly slug from a name"""
        if not name:
            return ''

        # Convert to lowercase
        slug = name.lower()
        # Remove special characters, keep only alphanumeric and spaces/hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)
        # Replace spaces with hyphens
        slug = re.sub(r'[\s]+', '-', slug)
        # Remove multiple consecutive hyphens
        slug = re.sub(r'-+', '-', slug)
        # Strip leading/trailing hyphens
        slug = slug.strip('-')

        # Ensure uniqueness
        if self.id:
            existing = self.search([
                ('url_slug', '=', slug),
                ('website_id', '=', self.website_id.id),
                ('id', '!=', self.id)
            ], limit=1)
            if existing:
                slug = f"{slug}-{self.id}"

        return slug

    def _compute_website_url(self):
        """Computes the absolute URL of the news item."""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')

        for news in self:
            # If url_slug is empty, auto-generate and save it
            if not news.url_slug and news.id and news.news_title:
                slug = news._generate_url_slug(news.news_title)
                # Update without triggering infinite recursion
                self.env.cr.execute(
                    "UPDATE website_pagee SET url_slug = %s WHERE id = %s",
                    (slug, news.id)
                )
                news.url_slug = slug

            if news.url_slug:
                news.url = f'{base_url}/news/{news.url_slug}'
            elif news.id:
                # Fallback to ID-based URL
                news.url = f'{base_url}/news/{news.id}'
            else:
                news.url = f'{base_url}/news/'

    def _set_website_url(self):
        """Extract slug from edited URL and update url_slug field"""
        for news in self:
            if news.url:
                slug = self._extract_slug_from_url(news.url)
                if slug and slug != news.url_slug:
                    news.url_slug = slug

    def _extract_slug_from_url(self, url):
        """Extract slug from full URL"""
        if not url:
            return ''

        # Remove base URL and /news/ prefix
        parts = url.rstrip('/').split('/news/')
        if len(parts) > 1:
            slug = parts[-1].strip('/')
            # Validate and clean the slug
            slug = slug.lower()
            slug = re.sub(r'[^\w\s-]', '', slug)
            slug = re.sub(r'[\s]+', '-', slug)
            slug = re.sub(r'-+', '-', slug)
            slug = slug.strip('-')
            return slug

        return ''

    @api.constrains('url_slug')
    def _check_url_slug(self):
        """Validate URL slug format"""
        for record in self:
            if record.url_slug:
                # Check if slug contains only valid characters
                if not re.match(r'^[a-z0-9-]+$', record.url_slug):
                    raise ValidationError(
                        "URL slug can only contain lowercase letters, numbers, and hyphens."
                    )

                # Check for duplicate slugs
                duplicate = self.search([
                    ('url_slug', '=', record.url_slug),
                    ('website_id', '=', record.website_id.id),
                    ('id', '!=', record.id)
                ], limit=1)

                if duplicate:
                    raise ValidationError(
                        f"URL slug '{record.url_slug}' is already used by another news item. "
                        "Please choose a different slug."
                    )

    def action_generate_url_slugs(self):
        """Generate URL slugs for all records without one"""
        records_without_slug = self.search([
            '|',
            ('url_slug', '=', False),
            ('url_slug', '=', '')
        ])

        count = 0
        for record in records_without_slug:
            if record.news_title:
                slug = record._generate_url_slug(record.news_title)
                record.url_slug = slug
                count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Generated URL slugs for {count} records',
                'type': 'success',
                'sticky': False,
            }
        }

    # Constraint to check if homepage news exceeds the limit of 5
    @api.onchange('homepage')
    def _onchange_homepage(self):
        if self.homepage:
            homepage_news_count = self.search_count([('homepage', '=', True)])
            if homepage_news_count >= 9:
                raise ValidationError(
                    "You cannot create more than 5 Home page News records. "
                    "If you want to create a new one, uncheck one of the existing records."
                )

    @api.onchange('main_news')
    def _onchange_main_news(self):
        if self.main_news:
            existing_main_news = self.search([('main_news', '=', True)])
            if len(existing_main_news) > 0:
                return {
                    'warning': {
                        'title': 'Main News Already Exists',
                        'message': 'A Main News record already exists!\n\nPlease uncheck the current one if you wish to proceed with this new entry.',
                    }
                }

    @api.constrains('main_news')
    def _check_main_news(self):
        for record in self:
            if record.main_news:
                existing_main_news = self.search([('main_news', '=', True)])
                if len(existing_main_news) > 1:
                    raise ValidationError(
                        "You can't mark this news as Main News because there is already a Main News record. "
                        "If you want to publish different Main News, first uncheck the existing Main News record and then proceed."
                    )

    @api.constrains('main_news', 'short_description')
    def _check_short_description(self):
        for record in self:
            if record.main_news and not record.short_description:
                raise ValidationError(
                    "Short Description is required when Main News is checked."
                )

    def action_open_image_upload(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'News Image',
            'res_model': 'website.image',
            'view_mode': 'list',
            'target': 'current',
        }


class WebsiteBlogPage(models.Model):
    _name = 'website.blogs'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Website blog'
    _rec_name = 'blogs_title'

    blogs_title = fields.Char(string="Title", required=True)
    blogs_description = fields.Text(string="Description", required=True)
    blogs_title_arabic = fields.Char(string="Arabic Title")
    blogs_description_arabic = fields.Text(string="Arabic Description")
    is_arabic_filled = fields.Boolean(string="Is Arabic Filled", default=False)  # ✅ ADD THIS
    main_blog = fields.Boolean(string="Main Blog", default=False)
    blogs_date = fields.Datetime(string="Date", required=True, default=fields.Datetime.now)
    website_id = fields.Many2one('website', string="Website", required=True)
    image = fields.Image(string="Image")
    publish = fields.Boolean(string="Published", default=False)
    short_description = fields.Text(string='Short Description')
    sequence = fields.Integer('Sequence', default=10)
    homepage = fields.Boolean(string="Home Page Blog(s)", default=False)

    # URL slug field - stores the slug part of the URL
    url_slug = fields.Char(
        string="URL Slug",
        copy=False,
        index=True,
        help="The URL-friendly identifier for this blog item"
    )

    # URL field - shows and allows editing of full URL
    url = fields.Char(
        string="Website URL",
        compute='_compute_website_url',
        inverse='_set_website_url',
        help="The full URL to view this blog item on the website. You can edit the slug part."
    )

    @api.model
    def create(self, vals):
        """Auto-generate URL slug from title if not provided"""
        if not vals.get('url_slug'):
            if vals.get('url'):
                vals['url_slug'] = self._extract_slug_from_url(vals['url'])
            elif vals.get('blogs_title'):
                vals['url_slug'] = self._generate_url_slug(vals['blogs_title'])

        # Handle Arabic fields auto-fill
        if not vals.get('blogs_title_arabic') and not vals.get('blogs_description_arabic'):
            vals['blogs_description_arabic'] = vals.get('blogs_description')
            vals['blogs_title_arabic'] = vals.get('blogs_title')
        elif not vals.get('blogs_description_arabic'):
            vals['blogs_description_arabic'] = vals.get('blogs_description')
        elif not vals.get('blogs_title_arabic'):
            vals['blogs_title_arabic'] = vals.get('blogs_title')
        vals['is_arabic_filled'] = True

        return super(WebsiteBlogPage, self).create(vals)

    def write(self, vals):
        """Handle URL slug updates"""
        if 'url' in vals and 'url_slug' not in vals:
            vals['url_slug'] = self._extract_slug_from_url(vals['url'])

        # Handle Arabic fields auto-fill for existing records
        if not self.is_arabic_filled:
            if not vals.get('blogs_title_arabic') and not vals.get('blogs_description_arabic'):
                vals['blogs_description_arabic'] = vals.get('blogs_description') or self.blogs_description
                vals['blogs_title_arabic'] = vals.get('blogs_title') or self.blogs_title
            elif not vals.get('blogs_description_arabic'):
                vals['blogs_description_arabic'] = vals.get('blogs_description') or self.blogs_description
            elif not vals.get('blogs_title_arabic'):
                vals['blogs_title_arabic'] = vals.get('blogs_title') or self.blogs_title
            vals['is_arabic_filled'] = True

        return super(WebsiteBlogPage, self).write(vals)

    def _generate_url_slug(self, name):
        """Generate a URL-friendly slug from a name"""
        if not name:
            return ''

        slug = name.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        slug = slug.strip('-')

        if self.id:
            existing = self.search([
                ('url_slug', '=', slug),
                ('website_id', '=', self.website_id.id),
                ('id', '!=', self.id)
            ], limit=1)
            if existing:
                slug = f"{slug}-{self.id}"

        return slug

    def _compute_website_url(self):
        """Computes the absolute URL of the blog item."""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url', '')

        for blog in self:
            if not blog.url_slug and blog.id and blog.blogs_title:
                slug = blog._generate_url_slug(blog.blogs_title)
                self.env.cr.execute(
                    "UPDATE website_blogs SET url_slug = %s WHERE id = %s",
                    (slug, blog.id)
                )
                blog.url_slug = slug

            if blog.url_slug:
                blog.url = f'{base_url}/blog/{blog.url_slug}'
            elif blog.id:
                blog.url = f'{base_url}/blog/{blog.id}'
            else:
                blog.url = f'{base_url}/blog/'

    def _set_website_url(self):
        """Extract slug from edited URL and update url_slug field"""
        for blog in self:
            if blog.url:
                slug = self._extract_slug_from_url(blog.url)
                if slug and slug != blog.url_slug:
                    blog.url_slug = slug

    def _extract_slug_from_url(self, url):
        """Extract slug from full URL"""
        if not url:
            return ''

        parts = url.rstrip('/').split('/blog/')
        if len(parts) > 1:
            slug = parts[-1].strip('/')
            slug = slug.lower()
            slug = re.sub(r'[^\w\s-]', '', slug)
            slug = re.sub(r'[\s]+', '-', slug)
            slug = re.sub(r'-+', '-', slug)
            slug = slug.strip('-')
            return slug

        return ''

    @api.constrains('url_slug')
    def _check_url_slug(self):
        """Validate URL slug format"""
        for record in self:
            if record.url_slug:
                if not re.match(r'^[a-z0-9-]+$', record.url_slug):
                    raise ValidationError(
                        "URL slug can only contain lowercase letters, numbers, and hyphens."
                    )

                duplicate = self.search([
                    ('url_slug', '=', record.url_slug),
                    ('website_id', '=', record.website_id.id),
                    ('id', '!=', record.id)
                ], limit=1)

                if duplicate:
                    raise ValidationError(
                        f"URL slug '{record.url_slug}' is already used by another blog item. "
                        "Please choose a different slug."
                    )

    def action_generate_url_slugs(self):
        """Generate URL slugs for all records without one"""
        records_without_slug = self.search([
            '|',
            ('url_slug', '=', False),
            ('url_slug', '=', '')
        ])

        count = 0
        for record in records_without_slug:
            if record.blogs_title:
                slug = record._generate_url_slug(record.blogs_title)
                record.url_slug = slug
                count += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Generated URL slugs for {count} records',
                'type': 'success',
                'sticky': False,
            }
        }
    @api.constrains('main_blog', 'short_description')
    def _check_short_description(self):
        for record in self:
            if record.main_blog and not record.short_description:
                raise ValidationError(
                    "Short Description is required when Main Blog is checked."
                )

    @api.onchange('homepage')
    def _onchange_homepage(self):
        if self.homepage:
            homepage_blogs_count = self.search_count([('homepage', '=', True)])
            if homepage_blogs_count >= 4:
                raise ValidationError(
                    "You cannot create more than 4 Home Page Blogs. "
                    "If you want to create a new one, uncheck one of the existing records."
                )

    def action_open_image_upload(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Blog Images',
            'res_model': 'website.blog.image',
            'view_mode': 'list',
            'target': 'current',
        }


class WebsiteImage(models.Model):
    _name = 'website.image'
    _description = 'News Image'

    upload_image = fields.Image(string="News Image", required=True)
    news_id = fields.Many2one('website.pagee', string="News Id")
    is_favorite = fields.Boolean('Favorite', default=False)
    id_name = fields.Char(
        string="ID",
        default=lambda self: self.env.context.get('active_id') and str(self.env.context['active_id']) or 'No Active ID',
        readonly=True
    )

    @api.model
    def create(self, vals):
        """Add active_id to the record during creation."""
        vals['id_name'] = str(self.env.context.get('active_id', 'No Active ID'))
        return super(WebsiteImage, self).create(vals)


class WebsiteBlogImage(models.Model):
    _name = 'website.blog.image'
    _description = 'Blog Images'

    upload_image = fields.Binary(string="Blog Image", required=True)
    blog_id = fields.Many2one('website.blogs', string="Blog Id")
    is_favorite = fields.Boolean('Favorite', default=False)
    id_name = fields.Char(string="ID", store=True)