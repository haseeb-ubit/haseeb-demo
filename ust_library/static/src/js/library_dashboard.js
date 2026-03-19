/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, onMounted, onPatched, useRef, useState } from "@odoo/owl";

export class LibraryDashboard extends Component {
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({ loading: true, data: {} });
        this.chartsRendered = false;

        this.donutRef = useRef("donutChart");
        this.barRef = useRef("barChart");
        this.hbarRef = useRef("hbarChart");

        onMounted(async () => {
            await this._loadChartJs();
            const data = await this.orm.call("library.dashboard.api", "get_dashboard_data", []);
            this.state.data = data;
            this.state.loading = false;
            // Charts will render in onPatched when DOM updates
        });

        onPatched(() => {
            if (!this.state.loading && !this.chartsRendered) {
                this.chartsRendered = true;
                this._renderCharts();
            }
        });
    }

    openAction(resModel, actionName, domain = []) {
        let action = {
            type: "ir.actions.act_window",
            name: actionName,
            res_model: resModel,
            view_mode: "list,form",
            views: [[false, "list"], [false, "form"]],
            target: "current",
        };
        if (domain.length > 0) {
            action.domain = domain;
        }
        this.action.doAction(action);
    }

    _loadChartJs() {
        if (window.Chart) return Promise.resolve();
        return new Promise((resolve, reject) => {
            const s = document.createElement("script");
            s.src = "https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js";
            s.onload = resolve;
            s.onerror = reject;
            document.head.appendChild(s);
        });
    }

    _renderCharts() {
        const d = this.state.data;
        if (!d.copy_status) return;

        // ── Donut: Copy Status ──
        if (this.donutRef.el) {
            new Chart(this.donutRef.el, {
                type: "doughnut",
                data: {
                    labels: d.copy_status.labels,
                    datasets: [{
                        data: d.copy_status.values,
                        backgroundColor: ["#10b981", "#f59e0b", "#3b82f6", "#ef4444", "#6b7280"],
                        borderWidth: 2,
                        borderColor: "#fff",
                        hoverOffset: 8,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    cutout: "60%",
                    plugins: {
                        legend: {
                            position: "bottom",
                            labels: { padding: 12, usePointStyle: true, pointStyle: "circle", font: { size: 11 } },
                        },
                    },
                },
            });
        }

        // ── Bar: Monthly Trend ──
        if (this.barRef.el) {
            new Chart(this.barRef.el, {
                type: "bar",
                data: {
                    labels: d.monthly_borrows.labels,
                    datasets: [{
                        label: "Borrows",
                        data: d.monthly_borrows.values,
                        backgroundColor: "#714B67",
                        borderRadius: 4,
                        hoverBackgroundColor: "#51324b",
                        barThickness: 24,
                    }],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#f1f5f9" } },
                        x: { grid: { display: false } },
                    },
                },
            });
        }

        // ── Horizontal Bar: Top Categories ──
        if (this.hbarRef.el) {
            new Chart(this.hbarRef.el, {
                type: "bar",
                data: {
                    labels: d.top_categories.labels.length ? d.top_categories.labels : ["No data"],
                    datasets: [{
                        label: "Borrows",
                        data: d.top_categories.values.length ? d.top_categories.values : [0],
                        backgroundColor: "#017e84",
                        borderRadius: 4,
                        hoverBackgroundColor: "#015e62",
                        barThickness: 22,
                    }],
                },
                options: {
                    indexAxis: "y",
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: "#f1f5f9" } },
                        y: { grid: { display: false } },
                    },
                },
            });
        }
    }
}

LibraryDashboard.template = "ust_library.LibraryDashboard";
registry.category("actions").add("library_dashboard_action", LibraryDashboard);
