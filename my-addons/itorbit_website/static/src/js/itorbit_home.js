/** @odoo-module **/

import { whenReady } from "@odoo/owl";

/**
 * Lightweight value-noise for wind / flag motion (no external deps).
 */
function hash2(x, y) {
    const s = Math.sin(x * 127.1 + y * 311.7) * 43758.5453;
    return s - Math.floor(s);
}

function smoothNoise(x, y) {
    const x0 = Math.floor(x);
    const y0 = Math.floor(y);
    const fx = x - x0;
    const fy = y - y0;
    const u = fx * fx * (3 - 2 * fx);
    const v = fy * fy * (3 - 2 * fy);
    const a = hash2(x0, y0);
    const b = hash2(x0 + 1, y0);
    const c = hash2(x0, y0 + 1);
    const d = hash2(x0 + 1, y0 + 1);
    return a + (b - a) * u + (c - a) * v + (a - b - c + d) * u * v;
}

function fbm(x, y) {
    let v = 0;
    let a = 0.5;
    let f = 1;
    for (let i = 0; i < 4; i++) {
        v += a * smoothNoise(x * f, y * f);
        a *= 0.5;
        f *= 2.05;
    }
    return v;
}

/**
 * Full-bleed pixel field with flag-in-wind motion (IT Orbit orange / navy).
 * Pixels cover the hero to the borders; density ripples like fabric in wind.
 */
function initPixelField(hero) {
    const canvas = hero.querySelector(".ito-hero__pixels");
    if (!canvas) {
        return;
    }
    const ctx = canvas.getContext("2d", { alpha: true });
    if (!ctx) {
        return;
    }

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    let raf = 0;
    let visible = true;
    let width = 0;
    let height = 0;
    let dpr = 1;
    let cell = 8;
    let cols = 0;
    let rows = 0;
    let start = performance.now();

    const resize = () => {
        const rect = hero.getBoundingClientRect();
        width = Math.max(1, Math.floor(rect.width));
        height = Math.max(1, Math.floor(rect.height));
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        canvas.width = Math.floor(width * dpr);
        canvas.height = Math.floor(height * dpr);
        canvas.style.width = `${width}px`;
        canvas.style.height = `${height}px`;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

        cell = width < 640 ? 6 : width < 1100 ? 7 : 8;
        cols = Math.ceil(width / cell) + 3;
        rows = Math.ceil(height / cell) + 3;
    };

    /**
     * Flag-like wind field: draw nearly every cell to the borders; alpha and
     * horizontal displacement follow flowing waves (fabric in wind).
     */
    const sample = (nx, ny, t) => {
        const wind = t * 0.7;
        const n1 = fbm(nx * 1.8 - wind, ny * 2.8);
        const n2 = fbm(nx * 3.4 - wind * 1.4 + 8.0, ny * 1.4 + 2.0);

        // Vertical folds + traveling gusts (flag ripples).
        const fold = 0.62 + 0.38 * Math.sin(ny * Math.PI * 2.8 + n1 * 3.2 + t * 1.05);
        const gust = 0.62 + 0.38 * Math.sin(nx * Math.PI * 2.6 - t * 1.85 + n2 * 2.8);

        // High base coverage so the field reaches the section borders.
        let strength = 0.52 + n1 * 0.32 + n2 * 0.18;
        strength *= 0.7 + fold * 0.45;
        strength *= 0.72 + gust * 0.4;
        return Math.max(0.18, Math.min(1, strength));
    };

    const draw = (now) => {
        const t = reduced ? 0 : (now - start) * 0.001;
        ctx.clearRect(0, 0, width, height);

        // Faint paper grid across the full hero.
        ctx.fillStyle = "rgba(7, 17, 31, 0.035)";
        const g = cell * 2;
        for (let x = 0; x < width + g; x += g) {
            for (let y = 0; y < height + g; y += g) {
                ctx.fillRect(x, y, 1.1, 1.1);
            }
        }

        const gap = 1.1;
        const amp = cell * 2.1;

        for (let j = 0; j < rows; j++) {
            for (let i = 0; i < cols; i++) {
                const nx = i / Math.max(1, cols - 1);
                const ny = j / Math.max(1, rows - 1);
                const s = sample(nx, ny, t);

                // Flag displacement: strong horizontal wave, light vertical flutter.
                let sway = 0;
                let flutter = 0;
                if (!reduced) {
                    const phase = fbm(nx * 2.2 - t * 0.55, ny * 2.8 + 1.7);
                    sway =
                        Math.sin(t * 1.55 + ny * 7.2 + phase * 5.0) * amp * (0.45 + s * 0.9) +
                        Math.sin(t * 2.35 + ny * 2.4 + i * 0.09) * amp * 0.28;
                    flutter =
                        Math.cos(t * 1.9 + nx * 4.5 + phase * 3.2) * cell * 0.42 * s;
                }

                const x = i * cell + sway;
                const y = j * cell + flutter;
                const size = Math.max(2.2, (cell - gap) * (0.55 + s * 0.55));
                const alpha = 0.16 + s * 0.72;

                if (s > 0.72) {
                    ctx.fillStyle = `rgba(240, 90, 40, ${alpha})`;
                } else if (s > 0.5) {
                    ctx.fillStyle = `rgba(220, 88, 42, ${alpha * 0.92})`;
                } else if (s > 0.34) {
                    ctx.fillStyle = `rgba(160, 88, 55, ${alpha * 0.7})`;
                } else {
                    ctx.fillStyle = `rgba(7, 17, 31, ${alpha * 0.48})`;
                }
                ctx.fillRect(x, y, size, size);
            }
        }
    };

    const loop = (now) => {
        if (!visible) {
            raf = 0;
            return;
        }
        draw(now);
        if (!reduced) {
            raf = requestAnimationFrame(loop);
        }
    };

    const startLoop = () => {
        if (raf || reduced) {
            if (reduced) {
                draw(performance.now());
            }
            return;
        }
        raf = requestAnimationFrame(loop);
    };

    const stopLoop = () => {
        if (raf) {
            cancelAnimationFrame(raf);
            raf = 0;
        }
    };

    resize();
    draw(performance.now());
    if (!reduced) {
        startLoop();
    }

    window.addEventListener("resize", () => {
        resize();
        draw(performance.now());
    });

    if (typeof IntersectionObserver !== "undefined" && !reduced) {
        const io = new IntersectionObserver(
            (entries) => {
                visible = entries.some((e) => e.isIntersecting);
                if (visible) {
                    startLoop();
                } else {
                    stopLoop();
                }
            },
            { threshold: 0.05 }
        );
        io.observe(hero);
    }
}

whenReady(() => {
    const roots = document.querySelectorAll(".ito-home, .ito-contact, .ito-thanks");
    if (!roots.length) {
        return;
    }

    requestAnimationFrame(() => {
        roots.forEach((el) => el.classList.add("is-ready"));
    });

    document.querySelectorAll(".ito-hero").forEach(initPixelField);

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
