import { registry } from "@web/core/registry";
import { Component, onWillUnmount, proxy, useProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

const WS_INTERVAL_CHECK = 15000;

export class OboxStatus extends Component {
    static template = "obox.OboxStatus";

    props = useProps(standardWidgetProps);

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
        this.wsOfflineTimeout = null;
        this.state = proxy({
            wan: {
                status: false,
                lastChecked: null,
            },
            lan: {
                status: false,
                lastChecked: null,
            },
        });

        if (this.props.record.resId) {
            const busService = useService("bus_service");
            busService.addChannel(this.props.record.data.internal_websocket_channel);
            busService.subscribe("PING", this.wanOboxStatus.bind(this));
            this.startMonitoring();

            onWillUnmount(() => {
                busService.unsubscribe("PING", this.wanOboxStatus.bind(this));
                clearTimeout(this.currentTimeout);
            });
        }
    }

    wanOboxStatus(data) {
        const boxToken = this.props.record.data.external_websocket_channel;
        const online = (boxToken || "").includes(data.token);
        if (!online) {
            // Error when several obox are connected, this widget get
            // the ping of all obox, so we need to return otherwise
            // its always offline.
            return;
        }

        clearTimeout(this.wsOfflineTimeout);
        this.state.wan.status = online;
        this.state.wan.lastChecked = new Date();
    }

    async startMonitoring() {
        const checkWan = async () => {
            try {
                await this.orm.call("obox.obox", "action_check_websocket", [
                    this.props.record.resId,
                ]);
                await this.props.record.load();
                this.wsOfflineTimeout = setTimeout(
                    () => (this.state.wan.status = false),
                    WS_INTERVAL_CHECK + 1000
                );
            } catch {
                this.state.wan.status = false;
            } finally {
                this.state.wan.lastChecked = new Date();
            }
        };

        const checkLan = async () => {
            if (!this.props.record.data.local_ip) {
                await this.props.record.load();
                this.state.lan.status = false;
                this.state.lan.lastChecked = new Date();
                return;
            }

            try {
                const url = `http://${this.props.record.data.local_ip}/odoo/`;
                const response = await fetch(url, {
                    signal: AbortSignal.timeout(1000),
                    targetAddressSpace: "local",
                });

                this.state.lan.status = response.ok;
            } catch {
                this.state.lan.status = false;
            } finally {
                this.state.lan.lastChecked = new Date();
            }
        };

        const check = async () => {
            await Promise.all([checkWan(), checkLan()]);
            this.currentTimeout = setTimeout(check, WS_INTERVAL_CHECK);
        };

        check();
    }
}

export const OboxStatusParams = {
    component: OboxStatus,
};

registry.category("view_widgets").add("obox_status", OboxStatusParams);
