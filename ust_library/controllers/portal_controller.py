# -*- coding: utf-8 -*-
import base64
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.http import request, content_disposition


class LibraryPortal(CustomerPortal):

    # ------------------------------------------------------------------
    # 1. Portal Home Counters (Badges on the /my page)
    # ------------------------------------------------------------------
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        user = request.env.user
        Borrow = request.env["library.borrow"].sudo()
        Reservation = request.env["library.reservation"].sudo()

        if "library_borrow_count" in counters:
            values["library_borrow_count"] = Borrow.search_count([("student_id", "=", user.id)])
        if "library_reservation_count" in counters:
            values["library_reservation_count"] = Reservation.search_count([("student_id", "=", user.id)])
        return values

    # ------------------------------------------------------------------
    # 2. Main Catalog / Search Page
    # ------------------------------------------------------------------
    @http.route(["/my/library/books", "/my/library/books/page/<int:page>"], type="http", auth="user", website=True)
    def portal_library_books(self, page=1, search="", category_id=None, status="all", **kwargs):
        Book = request.env["library.book"].sudo()
        domain = []
        all_books = Book.search([], order="name asc")
        top_rated_books = Book.search([('rating', '>', 0)], order="rating desc", limit=4)
        my_favorites = Book.search([('favorite_user_ids', 'in', [request.env.user.id])])


        # Search Logic
        if search:
            domain += ["|", ("name", "ilike", search), ("isbn", "ilike", search)]

        if category_id:
            domain.append(("category_id", "=", int(category_id)))

        # Status Logic
        if status == "available":
            domain.append(("available_copies", ">", 0))

        book_count = Book.search_count(domain)
        pager_data = portal_pager(
            url="/my/library/books",
            url_args={"search": search, "category_id": category_id, "status": status},
            total=book_count,
            page=page,
            step=100,
        )

        books = Book.search(domain, limit=100, offset=pager_data["offset"], order="name asc")

        values = self._prepare_portal_layout_values()
        values.update({
            "books": all_books,
            "favorite_books": my_favorites,
            "top_rated": top_rated_books,
            "page_name": "library_books",
            "pager": pager_data,
            "search": search,
            "categories": request.env["library.category"].sudo().search([]),
            "status": status,
        })
        return request.render("ust_library.portal_library_books", values)

    # ------------------------------------------------------------------
    # 3. Book Detailed View
    # ------------------------------------------------------------------
    @http.route("/my/library/book/<int:book_id>", type="http", auth="user", website=True)
    def portal_library_book_detail(self, book_id, **kwargs):
        book = request.env["library.book"].sudo().browse(book_id)
        if not book.exists():
            return request.not_found()

        values = self._prepare_portal_layout_values()
        values.update({
            "book": book,
            "page_name": "library_book_detail",
        })
        return request.render("ust_library.portal_library_book_detail", values)

    # ------------------------------------------------------------------
    # 4. E-Book Reader
    # ------------------------------------------------------------------
    @http.route("/my/library/book/<int:book_id>/read", type="http", auth="user", website=True)
    def portal_library_ebook_reader(self, book_id, **kwargs):
        book = request.env["library.book"].sudo().browse(book_id)
        if not book.exists() or not book.ebook_file:
            return request.not_found()

        values = self._prepare_portal_layout_values()
        values.update({"book": book, "page_name": "library_ebook_reader"})
        return request.render("ust_library.portal_library_ebook_reader", values)

    # ------------------------------------------------------------------
    # 5. Reservations (POST Action)
    # ------------------------------------------------------------------
    @http.route("/my/library/reservation/create", type="http", auth="user", website=True, methods=["POST"], csrf=True)
    def portal_library_create_reservation(self, **post):
        user = request.env.user
        copy_id = int(post.get("copy_id"))

        request.env["library.reservation"].sudo().create({
            "student_id": user.id,
            "copy_id": copy_id,
            "start_date": post.get("start_date"),
            "end_date": post.get("end_date"),
            "book_id": request.env["library.book.copy"].sudo().browse(copy_id).book_id.id,
        })
        return request.redirect("/my/library/books")