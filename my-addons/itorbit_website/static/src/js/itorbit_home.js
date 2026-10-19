/** @odoo-module **/

import { whenReady } from "@odoo/owl";

whenReady(() => {
    const roots = document.querySelectorAll(".ito-home, .ito-contact, .ito-thanks");
    if (!roots.length) {
        return;
    }

    requestAnimationFrame(() => {
        roots.forEach((el) => el.classList.add("is-ready"));
    });

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        return;
    }

    const targets = document.querySelectorAll(
        ".ito-products [data-ito-reveal], .ito-why [data-ito-reveal], .ito-cta [data-ito-reveal]"
    );
    if (!targets.length) {
        return;
    }

    const reveal = (el) => el.classList.add("is-inview");

    if (typeof IntersectionObserver === "undefined") {
        targets.forEach(reveal);
        return;
    }

    const io = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-inview");
                    io.unobserve(entry.target);
                }
            });
        },
        { rootMargin: "0px 0px -5% 0px", threshold: 0.05 }
    );

    targets.forEach((el, i) => {
        el.style.transitionDelay = `${Math.min(i % 5, 4) * 0.06}s`;
        io.observe(el);
    });

    window.setTimeout(() => {
        targets.forEach(reveal);
    }, 1800);
});
