import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";

const menuRouter = async () => {
    const companyId = user.context.allowed_company_ids[0];
    const orm = useService("orm");
    return await orm.call(
        "l10n_fr_reports.aspone.sso.wizard",
        "get_fiscal_report_action",
        [companyId],
    )
};

registry.category("actions").add("l10n_fr_reports.fiscal_declaration_menu_router", menuRouter);
