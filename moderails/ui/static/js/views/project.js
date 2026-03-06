/**
 * Project view -- task list + queue panel.
 */
function projectView() {
  return {
    project: null,
    tasks: [],
    flows: [],
    showCreate: false,
    editingName: false,
    editName: '',
    newTask: { title: '', description: '', type: 'feature' },
    startingTask: null,
    startChain: ['default'],
    addFlowSelect: 'default',
    startPrompt: '',
    isFirstRun: false,

    async init() {
      const pid = Alpine.store('router').params.projectId;
      if (!pid) return;
      await this.load(pid);
      this._interval = setInterval(() => this.load(pid), 5000);
    },

    destroy() {
      if (this._interval) clearInterval(this._interval);
    },

    async load(pid) {
      try {
        [this.project, this.tasks, this.flows] = await Promise.all([
          API.get(`/api/projects/${pid}`),
          API.get(`/api/projects/${pid}/tasks`),
          API.get('/api/flows'),
        ]);
      } catch (e) {
        console.error('Project load error:', e);
      }
    },

    statusColor(status) {
      return {
        backlog: 'bg-gray-600', pending: 'bg-blue-500',
        executing: 'bg-yellow-500', completed: 'bg-green-500',
      }[status] || 'bg-gray-600';
    },

    statusBadge(status) {
      return {
        idle: 'bg-gray-700 text-gray-300',
        queued: 'bg-blue-900/50 text-blue-300',
        running: 'bg-yellow-900/50 text-yellow-300',
      }[status] || 'bg-gray-700 text-gray-300';
    },

    typeColor(type) {
      return {
        feature: 'text-blue-400', fix: 'text-red-400',
        refactor: 'text-yellow-400', chore: 'text-gray-400',
      }[type] || 'text-gray-400';
    },

    async createTask() {
      const pid = this.project?.id;
      if (!pid) return;
      await API.post(`/api/projects/${pid}/tasks`, this.newTask);
      this.newTask = { title: '', description: '', type: 'feature' };
      this.showCreate = false;
      await this.load(pid);
    },

    async renameProject() {
      if (!this.editName.trim() || !this.project) return;
      await API.patch(`/api/projects/${this.project.id}`, { name: this.editName.trim() });
      this.editingName = false;
      await this.load(this.project.id);
      Alpine.store('app').init();
    },

    async deleteProject() {
      if (!this.project) return;
      if (!confirm(`Delete project "${this.project.name}"? All tasks and runs will be lost.`)) return;
      await API.del(`/api/projects/${this.project.id}`);
      Alpine.store('app').init();
      Alpine.store('router').navigate('dashboard');
    },

    openStartDialog(task) {
      this.startingTask = task.id;
      this.startChain = [];
      this.addFlowSelect = this.flows[0]?.name || 'default';
      this.startPrompt = task.description || '';
      this.isFirstRun = (task.run_count || 0) === 0;
    },

    async confirmStart() {
      if (!this.startingTask || this.startChain.length === 0) return;
      await API.post(`/api/tasks/${this.startingTask}/start`, {
        flow: this.startChain[0],
        flow_chain: this.startChain,
        user_prompt: this.startPrompt,
      });
      this.startingTask = null;
      await this.load(this.project.id);
    },

    async deleteTask(taskId) {
      if (!confirm('Delete this task?')) return;
      await API.del(`/api/tasks/${taskId}`);
      await this.load(this.project.id);
    },

    openTask(taskId) {
      Alpine.store('router').navigate('task', { taskId });
    },

    sortedTasks() {
      return [...this.tasks].sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    },
  };
}
