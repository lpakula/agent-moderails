/**
 * Daemon status widget for the sidebar.
 */
function daemonWidget() {
  return {
    running: false,
    pid: null,
    showLogs: false,
    logLines: [],
    _logInterval: null,

    async init() {
      await this.checkStatus();
      this._interval = setInterval(() => this.checkStatus(), 10000);
    },

    destroy() {
      if (this._interval) clearInterval(this._interval);
      this._stopLogPolling();
    },

    async checkStatus() {
      try {
        const data = await API.get('/api/daemon/status');
        this.running = data.running;
        this.pid = data.pid;
      } catch (e) {
        this.running = false;
        this.pid = null;
      }
    },

    async loadLogs() {
      try {
        const data = await API.get('/api/daemon/logs?lines=300');
        this.logLines = data.lines || [];
      } catch (e) {
        this.logLines = ['Failed to load logs'];
      }
    },

    toggleLogs() {
      this.showLogs = !this.showLogs;
      if (this.showLogs) {
        this.loadLogs();
        this._logInterval = setInterval(() => this.loadLogs(), 3000);
      } else {
        this._stopLogPolling();
      }
    },

    _stopLogPolling() {
      if (this._logInterval) {
        clearInterval(this._logInterval);
        this._logInterval = null;
      }
    },
  };
}
