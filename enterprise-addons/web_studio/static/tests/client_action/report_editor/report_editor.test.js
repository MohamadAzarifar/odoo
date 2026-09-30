import { useEnv } from "@web/owl2/utils";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import { describe, expect, test } from "@odoo/hoot";
import { hover, waitFor } from "@odoo/hoot-dom";
import { animationFrame } from "@odoo/hoot-mock";
import { Component, onPatched, proxy, t, useProps, xml } from "@odoo/owl";
import { contains, mockService, mountWithCleanup, onRpc } from "@web/../tests/web_test_helpers";
import { WebClientEnterprise } from "@web_enterprise/webclient/webclient";
import { ReportEditorModel } from "@web_studio/client_action/report_editor/report_editor_model";
import { defineStudioEnvironment } from "../../studio_tests_context";

describe.current.tags("desktop");

test("setting is in edition doesn't produce intempestive renders", async () => {
    defineMailModels();

    mockService("ui", {
        block: () => expect.step("block"),
        unblock: () => expect.step("unblock"),
    });

    class Child extends Component {
        static template = xml`<div class="child" t-out="this.props.rem.isInEdition"/>`;
        props = useProps({
            rem: t.instanceOf(ReportEditorModel),
        });
        setup() {
            onPatched(() => expect.step("Child rendered"));
        }
    }

    class Parent extends Component {
        static components = { Child };
        static template = xml`
            <Child rem="this.rem" />
            <button class="test-btn" t-on-click="() => this.rem.setInEdition(false)">btn</button>
        `;

        setup() {
            const env = useEnv();
            this.rem = proxy(
                new ReportEditorModel({ services: env.services, resModel: "partner" })
            );
            onPatched(() => expect.step("Parent rendered"));
            this.rem.setInEdition(true);
        }
    }

    await mountWithCleanup(Parent);
    await animationFrame();

    expect.verifySteps(["block"]);
    expect(".child").toHaveText("true");

    await contains("button.test-btn").click();

    expect(".child").toHaveText("false");
    expect.verifySteps(["unblock", "Child rendered"]);
});

test("reports tab disabled when no record", async () => {
    defineStudioEnvironment();
    onRpc("ir.model", "studio_model_infos", ({ args }) => ({
        is_mail_thread: true,
        record_ids: [],
        name: "Custom Partner Model",
        model: args[0],
    }));
    await mountWithCleanup(WebClientEnterprise);
    await contains("a.o_app[data-menu-xmlid=app_1]").click();
    await contains(".o_web_studio_navbar_item:not(.o_disabled)").click();
    expect(".o_web_studio_menu .o_menu_sections button:contains(Reports)").toHaveCount(1);
    expect(".o_web_studio_menu .o_menu_sections button:contains(Reports):disabled").toHaveCount(1);
    await hover(".o_web_studio_menu .o_menu_sections button:contains(Reports)");
    await waitFor(".o-overlay-item", { timeout: 1000 });
    expect(".o-overlay-item").toHaveText(
        "You cannot edit a report while there is no Custom Partner Model (partner)"
    );
});
