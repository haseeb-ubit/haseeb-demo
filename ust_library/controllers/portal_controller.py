# -*- coding: utf-8 -*-
import base64
from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.http import request, content_disposition


class LibraryPortal(CustomerPortal):

    # ------------------------------------------------------------------
    # Portal home counters (badges on /my)
    # ------------------------------------------------------------------
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        user = request.env.user
        Borrow = request.env["library.borrow"].sudo()
        Reservation = request.env["library.reservation"].sudo()

        if "library_borrow_count" in counters:
            values["library_borrow_count"] = Borrow.search_count(
                [("student_id", "=", user.id)]
            )
        if "library_reservation_count" in counters:
            values["library_reservation_count"] = Reservation.search_count(
                [("student_id", "=", user.id)]
            )
        if "library_overdue_count" in counters:
            values["library_overdue_count"] = Borrow.search_count(
                [("student_id", "=", user.id), ("state", "=", "overdue")]
            )
        if "library_penalty_total" in counters:
            borrows = Borrow.search([("student_id", "=", user.id)])
            values["library_penalty_total"] = sum(borrows.mapped("penalty_amount"))
        return values

    # ------------------------------------------------------------------
    # /my/library  – student dashboard
    # ------------------------------------------------------------------
    @http.route(
        ["/my/library", "/my/library/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_library_dashboard(self, page=1, **kwargs):
        user = request.env.user
        Borrow = request.env["library.borrow"].sudo()
        Reservation = request.env["library.reservation"].sudo()
        SpaceBooking = request.env["library.space.booking"].sudo()

        borrows = Borrow.search(
            [("student_id", "=", user.id)], order="id desc", limit=20
        )
        reservations = Reservation.search(
            [("student_id", "=", user.id)], order="id desc", limit=20
        )
        space_bookings = SpaceBooking.search(
            [("student_id", "=", user.id), ("state", "in", ("requested", "confirmed"))],
            order="date asc", limit=10,
        )

        values = self._prepare_portal_layout_values()
        values.update(
            {
                "page_name": "library_dashboard",
                "borrows": borrows,
                "reservations": reservations,
                "overdue_borrows": borrows.filtered(lambda b: b.state == "overdue"),
                "penalty_total": sum(borrows.mapped("penalty_amount")),
                "space_bookings": space_bookings,
                "library_borrow_count": Borrow.search_count(
                    [("student_id", "=", user.id)]
                ),
                "library_reservation_count": Reservation.search_count(
                    [("student_id", "=", user.id)]
                ),
            }
        )
        return request.render("ust_library.portal_my_library_dashboard", values)

    # ------------------------------------------------------------------
    # /my/library/books  – browse / search / filter
    # ------------------------------------------------------------------
    @http.route(
        ["/my/library/books", "/my/library/books/page/<int:page>"],
        type="http",
        auth="user",
        website=True,
    )
    def portal_library_books(
        self,
        page=1,
        search="",
        category_id=None,
        publisher_id=None,
        language="",
        publication_year="",
        status="all",
        **kwargs,
    ):
        Book = request.env["library.book"].sudo()
        domain = []

        # Text search
        if search:
            domain += [
                "|", "|",
                ("name", "ilike", search),
                ("isbn", "ilike", search),
                ("author_ids.name", "ilike", search),
            ]
        if category_id:
            domain.append(("category_id", "=", int(category_id)))
        if publisher_id:
            domain.append(("publisher_id", "=", int(publisher_id)))
        if language:
            domain.append(("language", "=", language))
        if publication_year:
            domain.append(("publication_year", "=", int(publication_year)))

        # Status filter
        if status == "available":
            domain.append(("available_copies", ">", 0))
        elif status == "borrowed":
            domain.append(("borrowed_copies", ">", 0))
        elif status == "reserved":
            domain.append(("reserved_copies", ">", 0))

        book_count = Book.search_count(domain)
        pager_data = portal_pager(
            url="/my/library/books",
            url_args={
                "search": search,
                "category_id": category_id or "",
                "publisher_id": publisher_id or "",
                "language": language,
                "publication_year": publication_year,
                "status": status,
            },
            total=book_count,
            page=page,
            step=12,
        )
        books = Book.search(
            domain, limit=12, offset=pager_data["offset"], order="name asc"
        )

        # Supporting filter lists
        all_books = Book.search([])
        languages_list = sorted(
            {b.language for b in all_books if b.language}
        )
        years_list = sorted(
            {b.publication_year for b in all_books if b.publication_year},
            reverse=True,
        )

        values = self._prepare_portal_layout_values()
        values.update(
            {
                "books": books,
                "page_name": "library_books",
                "pager": pager_data,
                "search": search,
                "status": status,
                "categories": request.env["library.category"].sudo().search([]),
                "publishers": request.env["library.publisher"].sudo().search([]),
                "languages": languages_list,
                "years": years_list,
                "category_id": int(category_id) if category_id else False,
                "publisher_id": int(publisher_id) if publisher_id else False,
                "language": language,
                "publication_year": int(publication_year) if publication_year else False,
            }
        )
        return request.render("ust_library.portal_library_books", values)

    # ------------------------------------------------------------------
    # /my/library/book/<id>  – book detail
    # ------------------------------------------------------------------
    @http.route(
        "/my/library/book/<int:book_id>",
        type="http",
        auth="user",
        website=True,
    )
    def portal_library_book_detail(self, book_id, **kwargs):
        book = request.env["library.book"].sudo().browse(book_id)
        if not book.exists():
            return request.not_found()

        user = request.env.user
        # Check if user already reviewed this book
        existing_review = request.env["library.book.review"].sudo().search(
            [("book_id", "=", book.id), ("student_id", "=", user.id)], limit=1
        )

        values = self._prepare_portal_layout_values()
        values.update({
            "book": book,
            "page_name": "library_book_detail",
            "existing_review": existing_review,
        })
        return request.render("ust_library.portal_library_book_detail", values)

    # ------------------------------------------------------------------
    # POST  /my/library/borrow/request
    # ------------------------------------------------------------------
    @http.route(
        "/my/library/borrow/request",
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_library_create_borrow_request(self, **post):
        user = request.env.user
        copy_id = int(post.get("copy_id"))
        expected_return_date = post.get("expected_return_date")

        copy = request.env["library.book.copy"].sudo().browse(copy_id)
        if not copy.exists() or copy.status not in ("available", "reserved"):
            return request.redirect("/my/library")

        request.env["library.borrow"].sudo().create(
            {
                "student_id": user.id,
                "copy_id": copy.id,
                "expected_return_date": expected_return_date,
            }
        )
        return request.redirect("/my/library")

    # ------------------------------------------------------------------
    # POST  /my/library/reservation/create
    # ------------------------------------------------------------------
    @http.route(
        "/my/library/reservation/create",
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_library_create_reservation(self, **post):
        user = request.env.user
        copy_id = int(post.get("copy_id"))
        start_date = post.get("start_date")
        end_date = post.get("end_date")

        copy = request.env["library.book.copy"].sudo().browse(copy_id)
        if not copy.exists() or copy.status == "lost":
            return request.redirect("/my/library")

        request.env["library.reservation"].sudo().create(
            {
                "student_id": user.id,
                "book_id": copy.book_id.id,
                "copy_id": copy.id,
                "start_date": start_date,
                "end_date": end_date,
            }
        )
        return request.redirect("/my/library")

    # ------------------------------------------------------------------
    # POST  /my/library/reservation/<id>/cancel
    # ------------------------------------------------------------------
    @http.route(
        "/my/library/reservation/<int:reservation_id>/cancel",
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_library_cancel_reservation(self, reservation_id, **post):
        reservation = (
            request.env["library.reservation"].sudo().browse(reservation_id)
        )
        if reservation.exists() and reservation.student_id.id == request.env.user.id:
            reservation.action_cancel()
        return request.redirect("/my/library")

    # ------------------------------------------------------------------
    # POST  /my/library/book/<id>/review  – submit a review
    # ------------------------------------------------------------------
    @http.route(
        "/my/library/book/<int:book_id>/review",
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_library_submit_review(self, book_id, **post):
        user = request.env.user
        rating = int(post.get("rating", 3))
        review_text = post.get("review_text", "")

        book = request.env["library.book"].sudo().browse(book_id)
        if not book.exists():
            return request.redirect("/my/library/books")

        # Check if already reviewed
        existing = request.env["library.book.review"].sudo().search(
            [("book_id", "=", book.id), ("student_id", "=", user.id)], limit=1
        )
        if existing:
            existing.write({"rating": rating, "review_text": review_text})
        else:
            request.env["library.book.review"].sudo().create({
                "student_id": user.id,
                "book_id": book.id,
                "rating": rating,
                "review_text": review_text,
            })
        return request.redirect("/my/library/book/%s" % book_id)

    # ------------------------------------------------------------------
    # /my/library/book/<id>/ebook  – embedded ebook reader
    # ------------------------------------------------------------------
    @http.route(
        "/my/library/book/<int:book_id>/ebook",
        type="http",
        auth="user",
        website=True,
    )
    def portal_library_ebook_reader(self, book_id, **kwargs):
        book = request.env["library.book"].sudo().browse(book_id)
        if not book.exists() or not book.ebook_file:
            return request.not_found()

        values = self._prepare_portal_layout_values()
        values.update({"book": book, "page_name": "library_ebook_reader"})
        return request.render("ust_library.portal_library_ebook_reader", values)

    # ------------------------------------------------------------------
    # /my/library/book/<id>/ebook/download  – download ebook
    # ------------------------------------------------------------------
    @http.route(
        "/my/library/book/<int:book_id>/ebook/download",
        type="http",
        auth="user",
        website=True,
    )
    def portal_library_ebook_download(self, book_id, **kwargs):
        book = request.env["library.book"].sudo().browse(book_id)
        if not book.exists() or not book.ebook_file or not book.ebook_download_allowed:
            return request.not_found()

        file_content = base64.b64decode(book.ebook_file)
        filename = book.ebook_filename or "ebook.pdf"
        return request.make_response(
            file_content,
            headers=[
                ("Content-Type", "application/octet-stream"),
                ("Content-Disposition", content_disposition(filename)),
            ],
        )

    # ------------------------------------------------------------------
    # /my/library/recommendations  – book recommendations
    # ------------------------------------------------------------------
    @http.route(
        "/my/library/recommendations",
        type="http",
        auth="user",
        website=True,
    )
    def portal_library_recommendations(self, **kwargs):
        user = request.env.user
        Book = request.env["library.book"].sudo()

        values = self._prepare_portal_layout_values()
        values.update({
            "page_name": "library_recommendations",
            "popular_books": Book._get_popular_books(limit=10),
            "recommended_books": Book._get_recommended_for_user(user.id, limit=10),
            "trending_books": Book._get_trending_books(limit=10),
        })
        return request.render("ust_library.portal_library_recommendations", values)

    # ------------------------------------------------------------------
    # /my/library/purchase-requests  – list own purchase requests
    # ------------------------------------------------------------------
    @http.route(
        "/my/library/purchase-requests",
        type="http",
        auth="user",
        website=True,
    )
    def portal_library_purchase_requests(self, **kwargs):
        user = request.env.user
        requests_list = request.env["library.purchase.request"].sudo().search(
            [("student_id", "=", user.id)], order="id desc"
        )
        values = self._prepare_portal_layout_values()
        values.update({
            "page_name": "library_purchase_requests",
            "purchase_requests": requests_list,
        })
        return request.render("ust_library.portal_library_purchase_requests", values)

    # ------------------------------------------------------------------
    # POST  /my/library/purchase-request  – submit purchase request
    # ------------------------------------------------------------------
    @http.route(
        "/my/library/purchase-request",
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_library_create_purchase_request(self, **post):
        user = request.env.user
        request.env["library.purchase.request"].sudo().create({
            "student_id": user.id,
            "book_title": post.get("book_title", ""),
            "author_name": post.get("author_name", ""),
            "publisher_name": post.get("publisher_name", ""),
            "isbn": post.get("isbn", ""),
            "reason": post.get("reason", ""),
        })
        return request.redirect("/my/library/purchase-requests")

    # ------------------------------------------------------------------
    # /my/library/spaces  – list study spaces
    # ------------------------------------------------------------------
    @http.route(
        "/my/library/spaces",
        type="http",
        auth="user",
        website=True,
    )
    def portal_library_spaces(self, **kwargs):
        spaces = request.env["library.space"].sudo().search([("active", "=", True)])
        values = self._prepare_portal_layout_values()
        values.update({
            "page_name": "library_spaces",
            "spaces": spaces,
        })
        return request.render("ust_library.portal_library_spaces", values)

    # ------------------------------------------------------------------
    # /my/library/space/<id>/calendar  – space booking calendar
    # ------------------------------------------------------------------
    @http.route(
        "/my/library/space/<int:space_id>/calendar",
        type="http",
        auth="user",
        website=True,
    )
    def portal_library_space_calendar(self, space_id, **kwargs):
        space = request.env["library.space"].sudo().browse(space_id)
        if not space.exists():
            return request.not_found()

        values = self._prepare_portal_layout_values()
        values.update({
            "page_name": "library_space_calendar",
            "space": space,
        })
        return request.render("ust_library.portal_library_space_calendar", values)

    # ------------------------------------------------------------------
    # JSON  /my/library/space/<id>/events  – calendar event data
    # ------------------------------------------------------------------
    @http.route(
        "/my/library/space/<int:space_id>/events",
        type="json",
        auth="user",
        website=True,
    )
    def portal_library_space_events(self, space_id, **kwargs):
        bookings = request.env["library.space.booking"].sudo().search([
            ("space_id", "=", space_id),
            ("state", "in", ("requested", "confirmed")),
        ])
        events = []
        for b in bookings:
            # Convert float time to HH:MM
            start_h = int(b.start_time)
            start_m = int((b.start_time - start_h) * 60)
            end_h = int(b.end_time)
            end_m = int((b.end_time - end_h) * 60)
            events.append({
                "id": b.id,
                "title": "%s (%s)" % (b.student_id.name, b.name),
                "start": "%s %02d:%02d:00" % (b.date, start_h, start_m),
                "end": "%s %02d:%02d:00" % (b.date, end_h, end_m),
                "color": "#28a745" if b.state == "confirmed" else "#ffc107",
            })
        return events

    # ------------------------------------------------------------------
    # POST  /my/library/space/book  – book a space
    # ------------------------------------------------------------------
    @http.route(
        "/my/library/space/book",
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_library_book_space(self, **post):
        user = request.env.user
        space_id = int(post.get("space_id", 0))
        date = post.get("date", "")
        start_time = float(post.get("start_time", 0))
        end_time = float(post.get("end_time", 0))

        space = request.env["library.space"].sudo().browse(space_id)
        if not space.exists():
            return request.redirect("/my/library/spaces")

        try:
            request.env["library.space.booking"].sudo().create({
                "student_id": user.id,
                "space_id": space.id,
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "state": "confirmed",
            })
        except Exception:
            pass  # Validation error (double booking etc.) — redirect gracefully
        return request.redirect("/my/library/space/%s/calendar" % space_id)

    # ------------------------------------------------------------------
    # POST  /my/library/space/booking/<id>/cancel
    # ------------------------------------------------------------------
    @http.route(
        "/my/library/space/booking/<int:booking_id>/cancel",
        type="http",
        auth="user",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def portal_library_cancel_space_booking(self, booking_id, **post):
        booking = request.env["library.space.booking"].sudo().browse(booking_id)
        if booking.exists() and booking.student_id.id == request.env.user.id:
            booking.action_cancel()
        return request.redirect("/my/library")

    # ------------------------------------------------------------------
    # /my/library/space/bookings  – my space bookings
    # ------------------------------------------------------------------
    @http.route(
        "/my/library/space/bookings",
        type="http",
        auth="user",
        website=True,
    )
    def portal_library_my_space_bookings(self, **kwargs):
        user = request.env.user
        bookings = request.env["library.space.booking"].sudo().search(
            [("student_id", "=", user.id)], order="date desc, start_time asc"
        )
        values = self._prepare_portal_layout_values()
        values.update({
            "page_name": "library_my_space_bookings",
            "bookings": bookings,
        })
        return request.render("ust_library.portal_library_my_space_bookings", values)
