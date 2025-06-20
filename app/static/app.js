function autoDismissAlerts(selector, timeout) {
  const alerts = document.querySelectorAll(selector);
  alerts.forEach(alert => {
    setTimeout(() => {
      // Use Bootstrap's Alert component to close the alert
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, timeout);
  });
}

// Wait for the DOM to be fully loaded before running any scripts
document.addEventListener('DOMContentLoaded', () => {
  // Call our function to add timeouts to the flashed messages
  autoDismissAlerts('.alert-dismissible', 6000);
});