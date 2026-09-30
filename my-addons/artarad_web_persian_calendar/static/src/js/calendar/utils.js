import * as utils from "@web/views/calendar/utils";

const originalGetFormattedDateSpan = utils.getFormattedDateSpan;
utils.getFormattedDateSpan = function (start, end, options = {}) {
    if (odoo.user_calendar_type !== "jalaali") {
        return originalGetFormattedDateSpan.call(this, start, end, options);
    }
    const isSameDay = start.hasSame(end, "jdays");
    if (!isSameDay && start.hasSame(end, "jmonth")) {
        // Simplify date-range if an event occurs into the same month (eg. "August 4-5, 2019")
        return start.toFormat("jLLLL jd") + "-" + end.toFormat("jd, jy");
    }
    return isSameDay
        ? start.toFormat(options.sameDayFormat ?? "jDDD")
        : start.toFormat("jDDD") + " - " + end.toFormat("jDDD");
};
