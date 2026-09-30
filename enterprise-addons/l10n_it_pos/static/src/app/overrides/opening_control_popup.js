import { OpeningControlPopup } from "@point_of_sale/app/components/popups/opening_control_popup/opening_control_popup";
import { patch } from "@web/core/utils/patch";

patch(OpeningControlPopup.prototype, {
    async confirm() {
        await super.confirm(...arguments);
        if (this.pos.config.useFiscalPrinter) {
            let fiscalPrinter = await this.pos.ticketPrinter.selectPrinter();
            if (!fiscalPrinter) {
                fiscalPrinter = this.pos.ticketPrinter.receiptPrinters.find(
                    (printer) => printer.printer_type === "it_fiscal_printer"
                );
                this.pos.ticketPrinter.defaultPrinter = fiscalPrinter;
            }
            fiscalPrinter?._instance?.getPrinterSerialNumber().then((sn) => {
                this.pos.config.it_fiscal_printer_serial_number = sn;
            });
        }
    },
});
