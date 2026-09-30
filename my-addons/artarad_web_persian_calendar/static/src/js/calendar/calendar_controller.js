/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { CalendarController } from "@web/views/calendar/calendar_controller";

const { DateTime } = luxon;

patch(CalendarController.prototype, {

    get currentDate() {
        if (odoo.user_calendar_type !== "jalaali") {
            return super.currentDate;
        }
        const meta = this.model.meta;
        const scale = meta.scale;
        if (this.uiService.isSmall && ["week", "month"].includes(scale)) {
            const date = meta.date || DateTime.now();
            let text = "";
            if (scale === "week") {
                const startMonth = date.startOf("week");
                const endMonth = date.endOf("week");
                if (startMonth.toFormat("jLLL") !== endMonth.toFormat("jLLL")) {
                    text = `${startMonth.toFormat("jLLL")}-${endMonth.toFormat("jLLL")}`;
                } else {
                    text = startMonth.toFormat("jLLLL");
                }
            } else if (scale === "month") {
                text = date.toFormat("jLLLL");
            }
            return ` - ${text} ${date.jyear}`;
        }
        return "";
    },

    get today() {
        if (odoo.user_calendar_type === "jalaali") {
            return DateTime.now().toFormat("jd");
        }
        return super.today;
    },

    get currentYear() {
        if (odoo.user_calendar_type === "jalaali") {
            return this.date.toFormat("jy");
        }
        return super.currentYear;
    },

    get dayHeader() {
        if (odoo.user_calendar_type === "jalaali") {
            return this.date.toFormat("jd jMMMM jy");
        }
        return super.dayHeader;
    },

    get weekHeader() {
        if (odoo.user_calendar_type !== "jalaali") {
            return super.weekHeader;
        }
        const { start, end } = this.model.visibleRange;
        if (start.jyear != end.jyear) {
            return `${start.toFormat("jMMMM")} ${start.jyear} - ${end.toFormat("jMMMM")} ${end.jyear}`;
        } else if (start.jmonth != end.jmonth) {
            return `${start.toFormat("jMMMM")} - ${end.toFormat("jMMMM")} ${start.jyear}`;
        }
        return `${start.toFormat("jMMMM")} ${start.jyear}`;
    },

    get currentMonth() {
        if (odoo.user_calendar_type === "jalaali") {
            return `${this.date.toFormat("jMMMM")} ${this.date.jyear}`;
        }
        return super.currentMonth;
    },

    get currentWeek() {
        if (odoo.user_calendar_type === "jalaali") {
            return this.model.visibleRange.start.jweekNumber;
        }
        return super.currentWeek;
    },

    setDate(move) {
        if (odoo.user_calendar_type !== "jalaali") {
            return super.setDate(move);
        }
        let date = null;
        switch (move) {
            case "next":
                date = this.model.date.plus({ [`j${this.model.scale}s`]: 1 });
                break;
            case "previous":
                date = this.model.date.plus({ [`j${this.model.scale}s`]: -1 });
                break;
            case "today":
                date = DateTime.local().startOf("day");
                if (date.ts === this.date.startOf("day").ts) {
                    this.model.bus.trigger("SCROLL_TO_CURRENT_HOUR", false);
                }
                break;
        }
        this.model.load({ date });
    },
});
