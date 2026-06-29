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
}

function AgentNode({ data }: { data: AgentNodeData }) {
  const colors = STATUS_COLORS[data.status] || STATUS_COLORS.idle;
  const isCurrent = data.status === 'thinking' || data.status === 'executing';
  const isPaused = data.status === 'paused_hitl';

  return (
    <div
      className={`px-4 py-2.5 rounded-lg border-2 ${colors.bg} ${colors.border} ${
        isCurrent ? 'animate-pulse shadow-lg shadow-amber-500/20' : ''
      } ${isPaused ? 'animate-pulse shadow-lg shadow-purple-500/20' : ''} min-w-[130px] text-center transition-all select-none`}
    >
      <Handle type="target" position={Position.Top} className="!bg-gray-600 !w-2 !h-2" />
      <div className={`text-[10px] font-bold ${colors.text} font-mono`}>
        {data.label}
      </div>
      <div className={`text-[8px] mt-0.5 ${colors.text} opacity-70 font-mono`}>
        {data.status.toUpperCase()}
        {data.retries > 0 && ` · ${data.retries}R`}
      </div>
      {isPaused && (
        <div className="mt-1 text-[7px] text-purple-400 font-bold">⏸️ WAITING APPROVAL</div>
      )}
      <Handle type="source" position={Position.Bottom} className="!bg-gray-600 !w-2 !h-2" />
    </div>
  );
}

const nodeTypes = { agentNode: AgentNode };

export default function GraphVisualizer({ onNodeClick }: { onNodeClick?: (node: any) => void }) {
  const nodeStatus = useGraphStore((s) => s.nodeStatus);
  const current_node = useGraphStore((s) => s.current_node);
  const retries = useGraphStore((s) => s.retries);


  const nodes: Node[] = useMemo(() => {
    return Object.entries(GRAPH_LAYOUT).map(([id, pos]) => ({
      id,
      type: 'agentNode',
      position: pos,
      data: {
        label: GRAPH_LABELS[id] || id,
        status: nodeStatus[id] || 'idle',
        retries: retries[id] || 0,
      },
    }));
  }, [nodeStatus, retries]);

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
    <div className="h-full w-full bg-[#0A0A0C]">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodeClick={(event, node) => {
          if (onNodeClick) onNodeClick(node);
        }}
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
