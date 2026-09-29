import { Component, onMounted, onPatched, onWillUnmount, proxy, signal } from "@odoo/owl";

export class NoContentAnimation extends Component {
    static template = "timesheet_grid.aw_timesheet_no_content_animation";

    containerRef = signal.ref();

    setup() {
        this.stepsNumber = 5;
        this.stepDuration = 5000;
        this.stepClassPrefix = "aw_nca_step_";
        this.chnagedStepClass = "aw_nca_step_changed";
        this.chnagedStepClassDuration = 800;
        this.intervalId = null;

        this.state = proxy({
            currentStep: 0,
        });

        const restartTimeline = () => {
            this.stopTimeline();
            this.startTimeline();
        };
        onMounted(restartTimeline);
        onPatched(restartTimeline);
        onWillUnmount(() => this.stopTimeline());
    }

    startTimeline() {
        let currentStep = 1;
        this.setStep(currentStep);

        this.intervalId = setInterval(() => {
            currentStep = currentStep >= this.stepsNumber ? 1 : currentStep + 1;
            this.setStep(currentStep);
        }, this.stepDuration);
    }

    setStep(stepNumber) {
        const el = this.containerRef();
        if (!el) {
            return;
        }

        // Remove all existing step classes
        for (let i = 1; i <= this.stepsNumber; i++) {
            el.classList.remove(`${this.stepClassPrefix}${i}`);
        }

        // Add the new step class
        el.classList.add(`${this.stepClassPrefix}${stepNumber}`);

        // Add the flag class to monitor steps change
        if (stepNumber !== 1 && stepNumber !== this.stepsNumber) {
            el.classList.add(this.chnagedStepClass);
            setTimeout(() => {
                el.classList.remove(this.chnagedStepClass);
            }, this.chnagedStepClassDuration);
        }
    }

    stopTimeline() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
}
