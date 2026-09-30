import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { parseDate, serializeDate } from "@web/core/l10n/dates";
import { localization } from "@web/core/l10n/localization";

/**
 * Portal tender bid form:
 * - unit price keeps locale thousand separators while typing
 * - delivery date uses Odoo datetime-picker (Jalali when calendar is jalaali)
 * - on submit, strip separators and serialize date to ISO for the server
 */
export class ZvyPortalTenderOfferForm extends Interaction {
    static selector = ".o_portal_tender_offer_form";
    dynamicContent = {
        ".o_zvy_unit_price_input": {
            "t-on-input": this.onUnitPriceInput,
            "t-on-blur": this.onUnitPriceBlur,
        },
        _root: {
            "t-on-submit": this.onSubmit,
        },
    };

    start() {
        const priceInput = this.el.querySelector(".o_zvy_unit_price_input");
        if (priceInput && priceInput.value) {
            priceInput.value = this.formatAmount(this.parseAmount(priceInput.value));
        }
    }

    get thousandsSep() {
        return localization.thousandsSep || ",";
    }

    get decimalPoint() {
        return localization.decimalPoint || ".";
    }

    parseAmount(raw) {
        if (raw === undefined || raw === null || raw === "") {
            return NaN;
        }
        let s = String(raw).trim();
        const thousands = this.thousandsSep;
        const decimal = this.decimalPoint;
        if (thousands) {
            s = s.split(thousands).join("");
        }
        // Common extras: spaces, NBSP, Arabic thousands separator
        s = s.replace(/[\s\u00a0\u066c]/g, "");
        if (decimal && decimal !== ".") {
            s = s.replace(decimal, ".");
        }
        // Drop leftover grouping commas when locale sep was already removed
        if ((s.match(/\./g) || []).length <= 1) {
            s = s.replace(/,(?=.*\.)/g, "").replace(/,(?!\d{1,2}$)/g, "");
        }
        return Number(s);
    }

    formatAmount(value) {
        if (value === undefined || value === null || Number.isNaN(value)) {
            return "";
        }
        const abs = Math.abs(value);
        const [intPart, fracPart] = String(abs).split(".");
        const grouped = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, this.thousandsSep);
        const sign = value < 0 ? "-" : "";
        if (fracPart === undefined) {
            return sign + grouped;
        }
        return `${sign}${grouped}${this.decimalPoint}${fracPart}`;
    }

    onUnitPriceInput(ev) {
        const input = ev.currentTarget;
        const start = input.selectionStart;
        const before = input.value;
        // Keep only digits, locale decimal, and minus while typing
        const escapedDec = this.decimalPoint.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        const cleaned = before.replace(new RegExp(`[^0-9\\-${escapedDec}]`, "g"), "");
        if (cleaned !== before) {
            input.value = cleaned;
            const delta = before.length - cleaned.length;
            const pos = Math.max(0, (start || 0) - delta);
            input.setSelectionRange(pos, pos);
        }
    }

    onUnitPriceBlur(ev) {
        const input = ev.currentTarget;
        const num = this.parseAmount(input.value);
        if (!Number.isNaN(num)) {
            input.value = this.formatAmount(num);
        }
    }

    onSubmit() {
        const priceInput = this.el.querySelector(".o_zvy_unit_price_input");
        if (priceInput) {
            const num = this.parseAmount(priceInput.value);
            priceInput.value = Number.isNaN(num) ? "" : String(num);
        }
        const dateInput = this.el.querySelector(".o_zvy_deliver_time_input");
        if (dateInput && dateInput.value) {
            const date = parseDate(dateInput.value);
            if (date && date.isValid) {
                dateInput.value = serializeDate(date);
            }
        }
    }
}

registry
    .category("public.interactions")
    .add("zvy_purchase.portal_tender_offer_form", ZvyPortalTenderOfferForm);
