// Channel Broadcasting Management System - Client-side JavaScript

document.addEventListener("DOMContentLoaded", function () {
    // Auto-dismiss flash messages after 5 seconds
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.style.transition = "opacity 0.5s";
            alert.style.opacity = "0";
            setTimeout(function () {
                alert.remove();
            }, 500);
        }, 5000);
    });

    // Confirm before destructive actions
    const confirmForms = document.querySelectorAll("form[data-confirm]");
    confirmForms.forEach(function (form) {
        form.addEventListener("submit", function (e) {
            if (!confirm(form.getAttribute("data-confirm"))) {
                e.preventDefault();
            }
        });
    });

    // Client-side search filter for tables
    const searchInput = document.getElementById("table-search");
    if (searchInput) {
        searchInput.addEventListener("input", function () {
            const term = this.value.toLowerCase();
            const rows = document.querySelectorAll("table tbody tr");
            rows.forEach(function (row) {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(term) ? "" : "none";
            });
        });
    }
});
