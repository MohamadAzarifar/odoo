import * as fullCalendarHook from "@web/views/calendar/hooks/full_calendar_hook";
import { loadBundle } from "@web/core/assets";
import { onMounted, onPatched, onWillStart, onWillUnmount, signal, useProps } from "@odoo/owl";

// Same hook as web's, but loading the jalaali build of FullCalendar for jalaali users.
fullCalendarHook.useFullCalendar = function useFullCalendar(ref, params) {
    const isJalaali = odoo.user_calendar_type === "jalaali";
    const props = useProps();
    const instance = signal(null);

    onWillStart(() => loadBundle(isJalaali ? "web.jfullcalendar_lib" : "web.fullcalendar_lib"));
    onMounted(() => {
        try {
            const Calendar = isJalaali ? jFullCalendar.Calendar : FullCalendar.Calendar;
            instance.set(new Calendar(ref(), params));
            instance().render();
        } catch (e) {
            throw new Error(`Cannot instantiate FullCalendar\n${e.message}`);
        }
    });
    onPatched(() => {
        instance().refetchEvents();
        instance().setOption("weekends", props.isWeekendVisible);
        if (params.weekNumbers && props.model.scale === "year") {
            instance().destroy();
            instance().render();
        }
    });
    onWillUnmount(() => instance().destroy());

    return instance;
};
