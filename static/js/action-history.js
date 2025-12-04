// static/js/action-history.js
// Client-side action history stored in localStorage. Keeps last 10 actions.
(function(){
  const KEY = 'axion_action_history_v1';
  function read() {
    try { return JSON.parse(localStorage.getItem(KEY) || '[]'); } catch(e) { return []; }
  }
  function write(arr) { try { localStorage.setItem(KEY, JSON.stringify(arr)); } catch(e){} }

  // Expose a global function to log actions
  window.logUserAction = function(actionObj) {
    try {
      // write locally
      const arr = read();
      arr.unshift(actionObj);
      if (arr.length > 10) arr.splice(10);
      write(arr);

      // attempt to persist server-side if session present (will 302/401 if not logged)
      try {
        fetch('/api/log_action', {
          method: 'POST',
          credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(actionObj)
        }).catch(()=>{});
      } catch(e) {}

      return true;
    } catch (e) {
      console.error('logUserAction error', e);
      return false;
    }
  };

  // Provide helper to get history
  window.getUserActionHistory = function() {
    return read();
  };

  // Periodic housekeeping: trim to last 10 every 2 minutes
  setInterval(function(){
    try { const arr = read(); if (arr.length > 10) { arr.splice(10); write(arr);} } catch(e){}
  }, 120000);
})();
