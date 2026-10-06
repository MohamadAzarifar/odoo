/** @odoo-module **/

import { whenReady } from "@odoo/owl";

whenReady(() => {
    const roots = document.querySelectorAll(".modir-home, .modir-contact, .modir-thanks");
    if (!roots.length) {
        return;
    }
    requestAnimationFrame(() => {
        roots.forEach((el) => el.classList.add("is-ready"));
    });
});
