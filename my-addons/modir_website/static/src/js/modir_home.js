/** @odoo-module **/

import { whenReady } from "@odoo/owl";

whenReady(() => {
    const home = document.querySelector(".modir-home");
    if (!home) {
        return;
    }
    requestAnimationFrame(() => {
        home.classList.add("is-ready");
    });
});
