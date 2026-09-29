import { registry } from "@web/core/registry";
import { phoneField } from "@web/views/fields/phone/phone_field";

registry.category("fields").add("voip_phone_input", {
    ...phoneField,
    extractProps: (fieldInfo) => ({
        ...phoneField.extractProps(fieldInfo),
        displayButtons: false,
    }),
});
