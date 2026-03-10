/** @odoo-module **/
/**
 * Library Space Booking Calendar
 * Uses FullCalendar CDN to render bookings on the portal space calendar page.
 */
document.addEventListener("DOMContentLoaded", function () {
    const calendarEl = document.getElementById("library_calendar");
    if (!calendarEl) return;

    const spaceId = calendarEl.dataset.spaceId;
    if (!spaceId) return;

    // Load FullCalendar from CDN
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.css";
    document.head.appendChild(link);

    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.js";
    script.onload = function () {
        initCalendar(calendarEl, spaceId);
    };
    document.head.appendChild(script);
});

function initCalendar(calendarEl, spaceId) {
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: "timeGridWeek",
        headerToolbar: {
            left: "prev,next today",
            center: "title",
            right: "timeGridWeek,timeGridDay,dayGridMonth",
        },
        slotMinTime: "07:00:00",
        slotMaxTime: "22:00:00",
        allDaySlot: false,
        height: "auto",
        events: function (info, successCallback, failureCallback) {
            fetch("/my/library/space/" + spaceId + "/events", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: {},
                }),
            })
                .then((res) => res.json())
                .then((data) => {
                    if (data.result) {
                        successCallback(data.result);
                    } else {
                        successCallback([]);
                    }
                })
                .catch(() => failureCallback());
        },
    });
    calendar.render();
}
