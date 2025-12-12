!function(t) {
    "use strict";
    t.fn.countUp = function(e) {
        var n = t.extend({ time: 1000, delay: 10 }, e);
        return this.each(function() {
            var e = t(this), a = n;
            e.waypoint(function() {
                if (!e.data("counterupTo")) {
                    e.data("counterupTo", e.text());
                }

                var t = parseInt(e.data("counter-time")) > 0 ? parseInt(e.data("counter-time")) : a.time,
                    n = parseInt(e.data("counter-delay")) > 0 ? parseInt(e.data("counter-delay")) : a.delay,
                    u = t / n, r = e.data("counterupTo"), o = [r], c = /[0-9]+,[0-9]+/.test(r);

                r = r.replace(/,/g, "");

                if (/^[0-9]+$/.test(r)) {
                    for (var i = u; i >= 1; i--) {
                        var p = parseInt(Math.round(r / u * i));
                        if (c) {
                            for (; /(\d+)(\d{3})/.test(p.toString());)
                                p = p.toString().replace(/(\d+)(\d{3})/, "$1,$2");
                        }
                        o.unshift(p);
                    }
                }
                e.data("counterup-nums", o);
                e.text("0");
                console.log("Initial numbers array:", o);
                e.data("counterup-func", function() {
                    var nums = e.data("counterup-nums");
                    if (nums && nums.length > 0) {
                        e.text(nums.shift());
                        console.log("Updated number:", e.text());

                        if (nums.length) {
                            setTimeout(e.data("counterup-func"), n);
                        } else {
                            e.data("counterup-nums", null);
                            e.data("counterup-func", null);
                        }
                    }
                });
                setTimeout(e.data("counterup-func"), n);
            }, { offset: "100%", triggerOnce: true });
        });
    };
}(jQuery);