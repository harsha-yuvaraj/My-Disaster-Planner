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
  autoDismissAlerts('.alert-dismissible', 10000);

  // Clear Chatbot History on Logout
  const logoutBtn = document.getElementById('logout-btn');
  const CHAT_HISTORY_KEY = 'chatbot_history'; // Ensure this key matches the one in chatbot.js

  if (logoutBtn) {
    logoutBtn.addEventListener('click', function() {
      // When the logout button is clicked, remove the chat history from sessionStorage.
      sessionStorage.removeItem(CHAT_HISTORY_KEY);
    });
  }
});