/*global jQuery: true */
(function ($) {
    var ready = $.fn.ready;
    $.fn.ready = function (fn) {
        if (typeof fn !== "function") {
            return ready.apply(this, arguments);
        }
        return ready.call(this, function () {
            try {
                return fn.apply(this, arguments);
            } catch (e) {
                if (window.console && console.error) {
                    console.error("jQuery ready handler error:", e);
                }
            }
        });
    };
}(jQuery));
