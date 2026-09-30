/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { DateTimePicker } from "@web/core/datetime/datetime_picker";
import { _t } from "@web/core/l10n/translation";
import { localization } from "@web/core/l10n/localization";
import { isInRange, today } from "@web/core/l10n/dates";
import { range } from "@web/core/utils/numbers";

const { Info } = luxon;

const GRID_COUNT = 10;
const GRID_MARGIN = 1;
const DAYS_PER_WEEK = 7;
const WEEKS_PER_MONTH = 6;

const toDateItem = ({ isOutOfRange = false, isValid = true, label, range, extraClass }) => ({
    id: range[0].toISODate(),
    includesToday: isInRange(today(), range),
    isOutOfRange,
    isValid,
    label: String(range[0]["j" + label]),
    range,
    extraClass,
});

const toWeekItem = (weekDayItems) => ({
    number: weekDayItems[3].range[0].jweekNumber,
    days: weekDayItems,
});

const getStartOfWeek = (date) => {
    const { weekStart } = localization;
    return date.set({ weekday: date.weekday < weekStart ? weekStart - 7 : weekStart });
};

const getStartOfDecade = (date) => Math.floor(date.jyear / 10) * 10;

const getStartOfCentury = (date) => Math.floor(date.jyear / 100) * 100;

const PRECISION_LEVELS = new Map()
    .set("days", {
        mainTitle: _t("Select month"),
        nextTitle: _t("Next month"),
        prevTitle: _t("Previous month"),
        step: { jmonth: 1 },
        getTitle: (date) => `${date.jmonthLong} ${date.jyear}`,
        getItems: (date, { maxDate, minDate, showWeekNumbers, isDateValid, dayCellClass }) => {
            const monthRange = [date.startOf("jmonth"), date.endOf("jmonth")];
            const weeks = [];

            let startOfNextWeek = getStartOfWeek(monthRange[0]);
            for (let w = 0; w < WEEKS_PER_MONTH; w++) {
                const weekDayItems = [];
                for (let d = 0; d < DAYS_PER_WEEK; d++) {
                    const day = startOfNextWeek.plus({ day: d });
                    const dayRange = [day, day.endOf("day")];
                    weekDayItems.push(
                        toDateItem({
                            isOutOfRange: !isInRange(day, monthRange),
                            isValid:
                                isInRange(dayRange, [minDate, maxDate]) && isDateValid?.(day),
                            label: "day",
                            range: dayRange,
                            extraClass: dayCellClass?.(day) || "",
                        })
                    );
                    if (d === DAYS_PER_WEEK - 1) {
                        startOfNextWeek = day.plus({ day: 1 });
                    }
                }
                weeks.push(toWeekItem(weekDayItems));
            }

            const daysOfWeek = weeks[0].days.map((d) => [
                d.range[0].weekdayShort,
                d.range[0].weekdayLong,
                Info.weekdays("narrow", { locale: d.range[0].locale })[d.range[0].weekday - 1],
            ]);
            if (showWeekNumbers) {
                daysOfWeek.unshift(["", _t("Week numbers"), ""]);
            }

            return [
                {
                    id: "__month__0",
                    number: monthRange[0].jmonth,
                    daysOfWeek,
                    weeks,
                },
            ];
        },
    })
    .set("months", {
        mainTitle: _t("Select year"),
        nextTitle: _t("Next year"),
        prevTitle: _t("Previous year"),
        step: { jyear: 1 },
        getTitle: (date) => String(date.jyear),
        getItems: (date, { maxDate, minDate }) => {
            const startOfYear = date.startOf("jyear");
            return range(12).map((month) => {
                const startOfMonth = startOfYear.plus({ jmonth: month });
                const monthRange = [startOfMonth, startOfMonth.endOf("jmonth")];
                return toDateItem({
                    isValid: isInRange(monthRange, [minDate, maxDate]),
                    label: "monthShort",
                    range: monthRange,
                });
            });
        },
    })
    .set("years", {
        mainTitle: _t("Select decade"),
        nextTitle: _t("Next decade"),
        prevTitle: _t("Previous decade"),
        step: { jyear: 10 },
        getTitle: (date) => `${getStartOfDecade(date) - 1} - ${getStartOfDecade(date) + 10}`,
        getItems: (date, { maxDate, minDate }) => {
            const startOfDecade = date.startOf("jyear").set({ jyear: getStartOfDecade(date) });
            return range(-GRID_MARGIN, GRID_COUNT + GRID_MARGIN).map((i) => {
                const startOfYear = startOfDecade.plus({ jyear: i });
                const yearRange = [startOfYear, startOfYear.endOf("jyear")];
                return toDateItem({
                    isOutOfRange: i < 0 || i >= GRID_COUNT,
                    isValid: isInRange(yearRange, [minDate, maxDate]),
                    label: "year",
                    range: yearRange,
                });
            });
        },
    })
    .set("decades", {
        mainTitle: _t("Select century"),
        nextTitle: _t("Next century"),
        prevTitle: _t("Previous century"),
        step: { jyear: 100 },
        getTitle: (date) => `${getStartOfCentury(date) - 10} - ${getStartOfCentury(date) + 100}`,
        getItems: (date, { maxDate, minDate }) => {
            const startOfCentury = date.startOf("jyear").set({ jyear: getStartOfCentury(date) });
            return range(-GRID_MARGIN, GRID_COUNT + GRID_MARGIN).map((i) => {
                const startOfDecade = startOfCentury.plus({ jyear: i * 10 });
                const decadeRange = [startOfDecade, startOfDecade.plus({ jyear: 10, millisecond: -1 })];
                return toDateItem({
                    label: "year",
                    isOutOfRange: i < 0 || i >= GRID_COUNT,
                    isValid: isInRange(decadeRange, [minDate, maxDate]),
                    range: decadeRange,
                });
            });
        },
    });

const isJalaali = () => odoo.user_calendar_type === "jalaali";

patch(DateTimePicker.prototype, {
    get activePrecisionLevel() {
        if (isJalaali()) {
            return PRECISION_LEVELS.get(this.state.precision);
        }
        return super.activePrecisionLevel;
    },

    filterPrecisionLevels(minPrecision, maxPrecision) {
        if (isJalaali()) {
            const levels = [...PRECISION_LEVELS.keys()];
            return levels.slice(levels.indexOf(minPrecision), levels.indexOf(maxPrecision) + 1);
        }
        return super.filterPrecisionLevels(minPrecision, maxPrecision);
    },

    adjustFocus(values, focusedDateIndex, minDate = this.minDate(), maxDate = this.maxDate()) {
        if (!isJalaali()) {
            return super.adjustFocus(values, focusedDateIndex, minDate, maxDate);
        }
        if (!this.shouldAdjustFocusDate && this.state.focusDate) {
            return;
        }
        const dateToFocus =
            values[focusedDateIndex] || values[focusedDateIndex === 1 ? 0 : 1] || today();

        this.shouldAdjustFocusDate = false;
        this.state.focusDate = this.clamp(dateToFocus.startOf("jmonth"), minDate, maxDate);
    },
});
