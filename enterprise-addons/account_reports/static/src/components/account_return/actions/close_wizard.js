import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export async function AccountReturnCloseWizard(_, action) {
    const params = action.params || {};
    useService("action").doAction({
        type: 'ir.actions.act_window_close'
    });
    return params.next_action;
}

registry.category("actions").add("action_return_close_wizard", AccountReturnCloseWizard);
