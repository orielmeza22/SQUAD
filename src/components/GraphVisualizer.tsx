import React, { useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  type Node,
  type Edge,
  MarkerType,
  Handle,
  Position,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useGraphStore, type NodeStatus } from '../stores/graphStore';

const STATUS_COLORS: Record<NodeStatus, { bg: string; border: string; text: string }> = {
  idle:        { bg: 'bg-gray-800',        border: 'border-gray-600',   text: 'text-gray-400' },
  thinking:    { bg: 'bg-amber-900/50',    border: 'border-amber-500',  text: 'text-amber-400' },
  executing:   { bg: 'bg-blue-900/50',     border: 'border-blue-500',   text: 'text-blue-400' },
  error:       { bg: 'bg-rose-900/50',     border: 'border-rose-500',   text: 'text-rose-400' },
  done:        { bg: 'bg-emerald-900/50',  border: 'border-emerald-500', text: 'text-emerald-400' },
  paused_hitl: { bg: 'bg-purple-900/50',   border: 'border-purple-500', text: 'text-purple-400' },
};

// Fixed layout positions for graph nodes
const GRAPH_LAYOUT: Record<string, { x: number; y: number }> = {
  architect: { x: 250, y: 0 },
  dba:      { x: 250, y: 100 },
  frontend: { x: 100, y: 200 },
  backend:  { x: 400, y: 200 },
  review:   { x: 400, y: 300 },
  fix:      { x: 550, y: 250 },
  qa:       { x: 250, y: 400 },
  devops:   { x: 250, y: 500 },
};

const GRAPH_LABELS: Record<string, string> = {
  architect: '🏗️ Architect',
  dba:      '🗄️ DBA',
  frontend: '🎨 Frontend',
  backend:  '⚙️ Backend',
  review:   '🔍 Review',
  fix:      '🩹 Fix',
  qa:       '🧪 QA',
  devops:   '🚀 DevOps',
};

interface AgentNodeData {
  label: string;
  status: NodeStatus;
  retries: number;
  tokens: number;
  isHighlighted: boolean;
  hasActiveInspector: boolean;
}

function AgentNode({ data }: { data: AgentNodeData }) {
  const status = data.status || 'idle';
  const colors = STATUS_COLORS[status] || STATUS_COLORS.idle;
  const isCurrent = status === 'thinking' || status === 'executing';
  const isPaused = status === 'paused_hitl';

  const getMetadata = (label: string) => {
    const l = label.toLowerCase();
    if (l.includes('architect')) {
      return { desc: 'spec.md · stack · schema', tokens: '1.2k tkn', meta: 'approved' };
    } else if (l.includes('dba')) {
      return { desc: 'database · migrations', tokens: '0.8k tkn', meta: 'ready' };
    } else if (l.includes('frontend')) {
      return { desc: 'views · templates · ui', tokens: '2.1k tkn', meta: 'ready' };
    } else if (l.includes('backend')) {
      return { desc: 'routes · apis · logic', tokens: '4.2k tkn', meta: 'running' };
    } else if (l.includes('review')) {
      return { desc: 'code quality inspection', tokens: '1.1k tkn', meta: 'queued' };
    } else if (l.includes('fix')) {
      return { desc: 'syntactic self-healing', tokens: '0.5k tkn', meta: 'ready' };
    } else if (l.includes('qa')) {
      return { desc: 'tests · devops run', tokens: '1.5k tkn', meta: 'queued' };
    } else {
      return { desc: 'infrastructure deploy', tokens: '—', meta: 'idle' };
    }
  };

  const metaInfo = getMetadata(data.label);

  const [showTooltip, setShowTooltip] = React.useState(false);
  const timeoutRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleMouseEnter = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    timeoutRef.current = setTimeout(() => {
      setShowTooltip(true);
    }, 1000);
  };

  const handleMouseLeave = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setShowTooltip(false);
  };

  const formatTokens = (t: number) => {
    if (!t || t <= 0) return '—';
    if (t >= 1000) return `${(t / 1000).toFixed(1)}k tkn`;
    return `${t} tkn`;
  };

  const highlightClass = data.hasActiveInspector
    ? data.isHighlighted
      ? 'scale-[1.03] border-indigo-500/80 shadow-[0_0_20px_rgba(99,102,241,0.4)] opacity-100 z-50'
      : 'opacity-40'
    : 'opacity-100';

  return (
    <div
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={`px-4 py-3 rounded-lg border bg-[#12121C] text-left transition-all select-none min-w-[170px] relative ${
        status === 'done' ? 'border-emerald-500/30' : ''
      } ${
        isCurrent ? 'border-violet-500 shadow-2xl shadow-violet-500/10 animate-pulse' : 'border-[#222233]'
      } ${
        isPaused ? 'border-amber-500 shadow-lg shadow-amber-500/15' : ''
      } ${highlightClass}`}
    >
      {showTooltip && (
        <div className="absolute bottom-[calc(100%+8px)] left-1/2 -translate-x-1/2 bg-[#0C0C14] border border-[#222233] px-2.5 py-1.5 rounded shadow-xl text-[8px] font-mono text-gray-300 w-max z-[100] pointer-events-none animate-in fade-in zoom-in-95 duration-100 flex flex-col gap-0.5 text-left border-l-2 border-l-indigo-500">
          <div className="font-bold text-white uppercase tracking-wider">{data.label}</div>
          <div>Status: <span className="text-violet-400 font-semibold">{status}</span></div>
          <div>Tokens: <span className="text-amber-400 font-semibold">{formatTokens(data.tokens)}</span></div>
        </div>
      )}
      <Handle type="target" position={Position.Top} className="!bg-gray-600 !w-1.5 !h-1.5" />
      
      <div className="flex items-center justify-between mb-1.5">
        <span className={`text-[8px] font-bold uppercase tracking-wider ${
          status === 'done' ? 'text-emerald-400' :
          isCurrent ? 'text-violet-400' :
          status === 'error' ? 'text-rose-400' : 'text-gray-500'
        }`}>
          {status}
        </span>
        {data.retries > 0 && (
          <span className="text-[7.5px] bg-amber-500/20 text-amber-400 px-1 rounded font-mono font-bold">
            {data.retries}R
          </span>
        )}
      </div>

      <div className="text-[11px] font-bold text-gray-100 font-mono">
        {data.label}
      </div>

      <div className="text-[8.5px] text-gray-500 font-mono mt-0.5 leading-tight">
        {metaInfo.desc}
      </div>

      {isCurrent && (
        <div className="h-[2px] bg-gray-800 rounded-full overflow-hidden my-2">
          <div className="h-full bg-gradient-to-r from-violet-500 to-fuchsia-500 animate-pulse w-3/4"></div>
        </div>
      )}

      <div className="flex items-center justify-between text-[8px] text-gray-500 font-mono mt-2 pt-1.5 border-t border-[#222233]">
        <span>{formatTokens(data.tokens)}</span>
        <span className={status === 'done' ? 'text-emerald-400 font-semibold' : ''}>
          {status === 'done' ? 'ready' : metaInfo.meta}
        </span>
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-gray-600 !w-1.5 !h-1.5" />
    </div>
  );
}

const nodeTypes = { agentNode: AgentNode };

export default function GraphVisualizer({ 
  onNodeClick, 
  onNodeDoubleClick,
  onNodeContextMenu,
  activeInspectorNodeId 
}: { 
  onNodeClick?: (event: React.MouseEvent, node: any) => void;
  onNodeDoubleClick?: (event: React.MouseEvent, node: any) => void;
  onNodeContextMenu?: (event: React.MouseEvent, node: any) => void;
  activeInspectorNodeId?: string | null;
}) {
  const nodeStatus = useGraphStore((s) => s.nodeStatus);
  const nodeTokens = useGraphStore((s) => s.nodeTokens);
  const current_node = useGraphStore((s) => s.current_node);
  const retries = useGraphStore((s) => s.retries);
  const pipeline_status = useGraphStore((s) => s.pipeline_status);

  const isPipelineRunning = pipeline_status === 'running' || pipeline_status === 'waiting_spec_approval' || pipeline_status === 'waiting_hitl_approval';

  const nodes: Node[] = useMemo(() => {
    return Object.entries(GRAPH_LAYOUT).map(([id, pos]) => {
      let status = nodeStatus[id] || 'idle';
      if (!isPipelineRunning) {
        status = 'idle';
      }
      return {
        id,
        type: 'agentNode',
        position: pos,
        data: {
          label: GRAPH_LABELS[id] || id,
          status: status,
          retries: retries[id] || 0,
          tokens: isPipelineRunning ? (nodeTokens[id] || 0) : 0,
          isHighlighted: activeInspectorNodeId === id,
          hasActiveInspector: !!activeInspectorNodeId,
        },
      };
    });
  }, [nodeStatus, nodeTokens, retries, isPipelineRunning, activeInspectorNodeId]);

  const edges: Edge[] = useMemo(() => {
    return [
      // Main flow
      { id: 'arch-dba', source: 'architect', target: 'dba', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
      { id: 'dba-fe', source: 'dba', target: 'frontend', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
      { id: 'fe-be', source: 'frontend', target: 'backend', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
      { id: 'be-rev', source: 'backend', target: 'review', animated: true, markerEnd: { type: MarkerType.ArrowClosed } },
      { id: 'rev-qa', source: 'review', target: 'qa', animated: false, markerEnd: { type: MarkerType.ArrowClosed } },
      { id: 'qa-dev', source: 'qa', target: 'devops', animated: false, markerEnd: { type: MarkerType.ArrowClosed } },
      // Retry loop: review → backend (direct)
      { id: 'rev-be-retry', source: 'review', target: 'backend', animated: true, markerEnd: { type: MarkerType.ArrowClosed }, style: { stroke: '#f59e0b', strokeDasharray: '5 5' }, label: 'retry' },
      // QA fix loop: qa → fix → qa
      { id: 'qa-fix', source: 'qa', target: 'fix', animated: true, markerEnd: { type: MarkerType.ArrowClosed }, style: { stroke: '#f59e0b', strokeDasharray: '5 5' } },
      { id: 'fix-qa', source: 'fix', target: 'qa', animated: true, markerEnd: { type: MarkerType.ArrowClosed }, style: { stroke: '#f59e0b', strokeDasharray: '5 5' } },
    ];
  }, []);

  return (
    <div className={`h-full w-full bg-[#0A0A0C] transition-all duration-300 ${activeInspectorNodeId ? 'opacity-[0.85]' : 'opacity-100'}`}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={onNodeClick}
        onNodeDoubleClick={onNodeDoubleClick}
        onNodeContextMenu={onNodeContextMenu}
        fitView
        minZoom={0.4}
        maxZoom={1.5}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#222" gap={16} size={1} />
        <Controls
          showInteractive={false}
          className="!bg-black/60 !border-white/10 !border"
        />
        <MiniMap
          nodeColor={(n) => {
            const status = (n.data as any)?.status || 'idle';
            const colors: Record<string, string> = {
              idle: '#374151',
              thinking: '#f59e0b',
              executing: '#3b82f6',
              error: '#ef4444',
              done: '#10b981',
              paused_hitl: '#a855f7',
            };
            return colors[status] || '#374151';
          }}
          maskColor="rgba(0,0,0,0.8)"
          className="!bg-black/40 !border-white/10"
        />
      </ReactFlow>
    </div>
  );
}
