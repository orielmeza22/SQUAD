import { create } from 'zustand';

export type NodeStatus = 'idle' | 'thinking' | 'executing' | 'error' | 'done' | 'paused_hitl';

export interface GraphNodeStatus {
  [agentName: string]: NodeStatus;
}

export interface DiffData {
  original: string;
  modified: string;
  filename: string;
}

interface GraphState {
  // Backend data
  runId: string | null;
  current_node: string | null;
  nodeStatus: GraphNodeStatus;
  retries: Record<string, number>;
  lastError: string | null;
  isPausedHitl: boolean;
  isPausedSpec: boolean;
  pipeline_status: string | null;

  // Diff panel for HITL
  diffData: DiffData | null;
  showDiffPanel: boolean;

  // Loading
  isLoading: boolean;

  // Internal (not exported to components)
  _pollInterval: ReturnType<typeof setInterval> | null;
  _eventSource: EventSource | null;

  // Actions
  fetchStatus: () => Promise<void>;
  approveSpec: () => Promise<void>;
  approveHitl: () => Promise<void>;
  setDiffData: (data: DiffData | null) => void;

  // Polling (fallback if SSE not available)
  startPolling: () => void;
  stopPolling: () => void;

  // SSE (preferred)
  connectSSE: () => void;
  disconnectSSE: () => void;
}

const API_BASE = window.location.port === '3000' ? 'http://localhost:8000' : '';

export const useGraphStore = create<GraphState>((set, get) => ({
  runId: null,
  current_node: null,
  nodeStatus: {},
  retries: {},
  lastError: null,
  isPausedHitl: false,
  isPausedSpec: false,
  pipeline_status: null,
  diffData: null,
  showDiffPanel: false,
  isLoading: false,
  _pollInterval: null,
  _eventSource: null,

  fetchStatus: async () => {
    try {
      set({ isLoading: true });
      const resp = await fetch(`${API_BASE}/api/graph/status`);
      const data = await resp.json();
      set({
        runId: data.run_id || null,
        current_node: data.current_node || null,
        nodeStatus: data.node_status || {},
        retries: data.retries || {},
        lastError: data.last_error || null,
        isPausedHitl: data.is_paused_hitl || false,
        isPausedSpec: data.pipeline_status === 'waiting_spec_approval',
        pipeline_status: data.pipeline_status || null,
      });
    } catch {
      // silent — don't break UI if backend unreachable
    } finally {
      set({ isLoading: false });
    }
  },

  approveSpec: async () => {
    try {
      await fetch(`${API_BASE}/api/agent/spec/approve`, { method: 'POST' });
      set({ isPausedSpec: false });
    } catch (e) {
      console.error('Error aprobando SPEC:', e);
    }
  },

  approveHitl: async () => {
    try {
      await fetch(`${API_BASE}/api/graph/hitl/approve`, { method: 'POST' });
      set({ isPausedHitl: false, showDiffPanel: false, diffData: null });
    } catch (e) {
      console.error('Error aprobando HITL:', e);
    }
  },

  setDiffData: (data) => set({ diffData: data, showDiffPanel: !!data }),

  startPolling: () => {
    if (get()._pollInterval) return;
    get().fetchStatus();
    const interval = setInterval(() => get().fetchStatus(), 2000);
    set({ _pollInterval: interval });
  },

  stopPolling: () => {
    const interval = get()._pollInterval;
    if (interval) {
      clearInterval(interval);
      set({ _pollInterval: null });
    }
  },

  connectSSE: () => {
    if (get()._eventSource) return;
    const es = new EventSource(`${API_BASE}/api/stream-logs`);

    // Listen for graph_status events (new event type from backend)
    es.addEventListener('graph_status', (event) => {
      try {
        const data = JSON.parse(event.data);
        set({
          current_node: data.current_node || null,
          nodeStatus: data.node_status || {},
          retries: data.retries || {},
          lastError: data.last_error || null,
          isPausedHitl: data.is_paused_hitl || false,
          isPausedSpec: data.pipeline_status === 'waiting_spec_approval',
          pipeline_status: data.pipeline_status || null,
        });
      } catch { /* ignore non-JSON */ }
    });

    // Also derive graph state from pipeline_logs events (existing)
    es.addEventListener('pipeline_logs', (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.pipeline_status) {
          set((prev) => ({
            isPausedSpec: data.pipeline_status === 'waiting_spec_approval',
            pipeline_status: data.pipeline_status,
          }));
        }
      } catch { /* ignore */ }
    });

    es.onerror = () => {
      // Connection lost — fall back to polling
      get().disconnectSSE();
      get().startPolling();
    };

    set({ _eventSource: es });
  },

  disconnectSSE: () => {
    const es = get()._eventSource;
    if (es) {
      es.close();
      set({ _eventSource: null });
    }
    get().stopPolling();
  },
}));
