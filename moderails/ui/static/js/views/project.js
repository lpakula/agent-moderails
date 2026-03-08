/**
 * Project view -- task list + queue panel.
 */
function projectView() {
  return {
    project: null,
    tasks: [],
    flows: [],
    models: [],
    agents: [],
    showCreate: false,
    editingName: false,
    editName: '',
    newTask: { title: '', description: '', type: 'feature' },
    startingTask: null,
    startChain: ['default'],
    addFlowSelect: '',
    startPrompt: '',
    startModel: '',
    startAgent: '',
    isFirstRun: false,
    showDefaults: false,
    defaultModel: '',
    defaultAgent: 'cursor',
    defaultFlowChain: [],
    defaultAddFlow: '',

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
        [this.project, this.tasks, this.flows, this.agents] = await Promise.all([
          API.get(`/api/projects/${pid}`),
          API.get(`/api/projects/${pid}/tasks`),
          API.get('/api/flows'),
          API.get('/api/agents'),
        ]);
        if (this.project && !this.defaultModel) {
          this.defaultModel = this.project.default_model || '';
          this.defaultAgent = this.project.default_agent || 'cursor';
          this.defaultFlowChain = this.project.default_flow_chain || ['default'];
        }
        await this.loadModelsForAgent(this.startAgent || this.project?.default_agent || 'cursor');
      } catch (e) {
        console.error('Project load error:', e);
      }
    },

    async loadModelsForAgent(agent) {
      try {
        this.models = await API.get(`/api/models?agent=${encodeURIComponent(agent)}`);
        if (this.models.length && !this.models.includes(this.startModel)) {
          this.startModel = this.models[0];
        }
      } catch (e) {
        this.models = [];
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

    async openStartDialog(task) {
      this.startingTask = task.id;
      this.startChain = [...(this.project?.default_flow_chain || ['default'])];
      this.addFlowSelect = '';
      this.startPrompt = '';
      this.startAgent = this.agents.includes(this.project?.default_agent) ? this.project.default_agent : (this.agents[0] || 'cursor');
      await this.loadModelsForAgent(this.startAgent);
      this.startModel = this.project?.default_model || this.models[0] || '';
      this.isFirstRun = (task.run_count || 0) === 0;
    },

    async onAgentChange(agent) {
      await this.loadModelsForAgent(agent);
    },

    async confirmStart() {
      if (!this.startingTask || this.startChain.length === 0 || !this.startModel || !this.startAgent) return;
      await API.post(`/api/tasks/${this.startingTask}/start`, {
        flow: this.startChain[0],
        flow_chain: this.startChain,
        user_prompt: this.startPrompt,
        model: this.startModel,
        agent: this.startAgent,
      });
      this.startingTask = null;
      await this.load(this.project.id);
    },

    async saveDefaults() {
      if (!this.project) return;
      await API.patch(`/api/projects/${this.project.id}`, {
        default_model: this.defaultModel,
        default_agent: this.defaultAgent,
        default_flow_chain: this.defaultFlowChain,
      });
      this.showDefaults = false;
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
