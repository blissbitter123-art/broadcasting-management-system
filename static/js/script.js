/* BroadcastHub - vanilla JavaScript for small UI helpers only.
   All real validation and security checks are enforced on the Flask server. */

(function () {
  "use strict";

  /* ---------- Mobile navigation ---------- */
  var navToggle = document.getElementById("navToggle");
  var navLinks = document.getElementById("navLinks");
  if (navToggle && navLinks) {
    navToggle.addEventListener("click", function () {
      navLinks.classList.toggle("open");
    });
  }

  /* ---------- Flash message close + auto dismiss ---------- */
  document.querySelectorAll(".alert-close").forEach(function (button) {
    button.addEventListener("click", function () {
      var alert = button.closest(".alert");
      if (alert) {
        alert.remove();
      }
    });
  });

  window.setTimeout(function () {
    document.querySelectorAll(".flash-area .alert").forEach(function (alert) {
      alert.remove();
    });
  }, 7000);

  /* ---------- Show duration calculation (add / edit forms) ---------- */
  var startTime = document.getElementById("start_time");
  var endTime = document.getElementById("end_time");
  var durationValue = document.getElementById("durationValue");

  function formatDuration(totalMinutes) {
    var hours = Math.floor(totalMinutes / 60);
    var minutes = totalMinutes % 60;
    return hours + "h " + (minutes < 10 ? "0" + minutes : minutes) + "m";
  }

  function updateDuration() {
    if (!startTime || !endTime || !durationValue) {
      return;
    }
    if (!startTime.value || !endTime.value) {
      durationValue.textContent = "--:--";
      return;
    }
    var start = new Date("2000-01-01T" + startTime.value + ":00");
    var end = new Date("2000-01-01T" + endTime.value + ":00");
    var diff = (end - start) / 60000;
    if (isNaN(diff)) {
      durationValue.textContent = "--:--";
    } else if (diff <= 0) {
      durationValue.textContent = "Invalid (end must be after start)";
      durationValue.style.color = "#c0392b";
      return;
    } else {
      durationValue.style.color = "";
      durationValue.textContent = formatDuration(diff);
    }
  }

  if (startTime && endTime) {
    startTime.addEventListener("change", updateDuration);
    endTime.addEventListener("change", updateDuration);
    updateDuration();
  }

  /* ---------- Show form: quick client-side check before submit ---------- */
  var showForm = document.getElementById("showForm");
  if (showForm) {
    showForm.addEventListener("submit", function (event) {
      var dateField = document.getElementById("broadcast_date");
      if (startTime.value && endTime.value) {
        var start = new Date("2000-01-01T" + startTime.value + ":00");
        var end = new Date("2000-01-01T" + endTime.value + ":00");
        if (end <= start) {
          event.preventDefault();
          alert("End time must be later than start time.");
          endTime.focus();
          return;
        }
      }
      if (dateField && dateField.value) {
        var chosen = new Date(dateField.value + "T00:00:00");
        var today = new Date();
        today.setHours(0, 0, 0, 0);
        if (chosen < today) {
          if (!window.confirm("The broadcast date is in the past. Submit anyway?")) {
            event.preventDefault();
            return;
          }
        }
      }
      /* Server-side validation still runs after this. */
    });
  }

  /* ---------- Registration: live password confirmation ---------- */
  var password = document.getElementById("password");
  var confirmBox = document.getElementById("confirm_password");
  var matchHint = document.getElementById("passwordMatchHint");

  if (password && confirmBox && matchHint) {
    function checkMatch() {
      if (!confirmBox.value) {
        matchHint.textContent = "";
        matchHint.style.color = "";
        return;
      }
      if (password.value === confirmBox.value) {
        matchHint.textContent = "Passwords match.";
        matchHint.style.color = "#1f8a53";
      } else {
        matchHint.textContent = "Passwords do not match yet.";
        matchHint.style.color = "#c0392b";
      }
    }
    password.addEventListener("input", checkMatch);
    confirmBox.addEventListener("input", checkMatch);

    var registerForm = document.getElementById("registerForm");
    if (registerForm) {
      registerForm.addEventListener("submit", function (event) {
        if (password.value !== confirmBox.value) {
          event.preventDefault();
          alert("Passwords do not match. Please re-check the confirm password field.");
          confirmBox.focus();
        }
      });
    }
  }

  /* ---------- Highlight the row of an action target (#show-12) ---------- */
  if (window.location.hash) {
    var target = document.querySelector(window.location.hash);
    if (target && target.tagName === "TR") {
      target.style.outline = "2px solid #1d6fb8";
      target.style.background = "#e8f1fa";
    }
  }
})();
