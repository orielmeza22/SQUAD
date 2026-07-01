import React from 'react';
import { X, Cpu, Clock, Award, Shield, FileText } from 'lucide-react';
import { useApp } from '../context/AppContext';
import { useGraphStore } from '../stores/graphStore';

interface ToolCall {
  name: string;
  args: string;
  status: 'success' | 'failed';
  time: string;
}

interface AgentInspectorProps {
  isOpen: boolean;
  onClose: () => void;
  nodeData: {
    id: string;
    label: string;
    status: string;
    agentType?: string;
  } | null;
  position: { top: number; left: number } | null;
  onViewCode: (label: string) => void;
  onViewLogs: (label: string) => void;
  onViewDiff: () => void;
  onRetry: () => void;
  onEscalate: () => void;
}

function parseInspectorLogs(label: string, logs: string[], isRunning: boolean) {
  const l = label.toLowerCase();
  
  if (!isRunning && logs.length === 0) {
    return {
      thinking: ['SQUAD está en estado de reposo (IDLE). Envía un prompt para iniciar la ejecución del enjambre.'],
      toolCalls: [],
      confidence: 1.0,
      specVersion: '—'
    };
  }

  let prefix = '';
  if (l.includes('architect') || l.includes('arquitecto')) prefix = 'ARQUITECTO';
  else if (l.includes('dba')) prefix = 'DBA';
  else if (l.includes('frontend')) prefix = 'FRONTEND';
  else if (l.includes('backend')) prefix = 'BACKEND';
  else if (l.includes('review')) prefix = 'REVISOR';
  else if (l.includes('fix')) prefix = 'FIX';
  else if (l.includes('qa')) prefix = 'QA';
  else if (l.includes('devops')) prefix = 'DEVOPS';

  if (!prefix) {
    return {
      thinking: ['En espera de inicialización...'],
      toolCalls: [],
      confidence: 1.0,
      specVersion: '—'
    };
  }

  // Filter logs for this specific agent
  const agentLogs = logs.filter(log => {
    const upper = log.toUpperCase();
    return upper.includes(`[AGENTE ${prefix}]`) || upper.includes(`[AGENTE INFRA]`) || upper.includes(`[DEPLOY]`);
  });

  if (agentLogs.length === 0) {
    return {
      thinking: [`El Agente ${label} aún no ha iniciado tareas en esta ejecución.`],
      toolCalls: [],
      confidence: 1.0,
      specVersion: '—'
    };
  }

  // Clean log prefixes for thinking chain representation
  const thinking = agentLogs.map(log => {
    return log.replace(/^\[.*?\]:\s*/, '').replace(/^\[.*?\]\s*/, '');
  });

  // Extract tools dynamically from logs
  const toolCalls: ToolCall[] = [];
  agentLogs.forEach(log => {
    const text = log.toLowerCase();
    if (text.includes('escribiendo') || text.includes('creando') || text.includes('write')) {
      const match = log.match(/(?:escribiendo|creando|write)\s+([a-zA-Z0-9_\-\.\/]+)/i);
      toolCalls.push({
        name: 'write_file',
        args: JSON.stringify({ path: match ? match[1] : 'file' }),
        status: 'success',
        time: '1.2s'
      });
    } else if (text.includes('leyendo') || text.includes('read')) {
      const match = log.match(/(?:leyendo|read)\s+([a-zA-Z0-9_\-\.\/]+)/i);
      toolCalls.push({
        name: 'read_file',
        args: JSON.stringify({ path: match ? match[1] : 'file' }),
        status: 'success',
        time: '0.4s'
      });
    } else if (text.includes('validando') || text.includes('linter') || text.includes('flake8') || text.includes('test')) {
      toolCalls.push({
        name: 'run_validation',
        args: JSON.stringify({ command: 'pytest/flake8' }),
        status: 'success',
        time: '2.5s'
      });
    }
  });

  let confidence = 0.95;
  if (logs.some(log => log.toLowerCase().includes('error') || log.toLowerCase().includes('failed'))) {
    confidence = 0.75;
  }

  return { 
    thinking, 
    toolCalls, 
    confidence,
    specVersion: logs.some(l => l.toLowerCase().includes('spec.md')) ? 'SPEC.md (v2.0)' : 'Ninguna'
  };
}

export default function AgentInspector({
  isOpen,
  onClose,
  nodeData,
  position,
  onViewCode,
  onViewLogs,
  onViewDiff,
  onRetry,
  onEscalate
}: AgentInspectorProps) {
  const { pipelineLogs, isPipelineRunning } = useApp();
  const isPausedHitl = useGraphStore((s) => s.isPausedHitl) || false;
  const ref = React.useRef<HTMLDivElement>(null);

  // Esc key closure
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Click outside closure (without blocking other clicks)
  React.useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        const target = e.target as HTMLElement;
        if (!target.closest('.react-flow__node') && !target.closest('.agent-inspector')) {
          onClose();
        }
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  if (!isOpen || !nodeData) return null;

  const { thinking, toolCalls, confidence } = parseInspectorLogs(
    nodeData.label, 
    pipelineLogs, 
    isPipelineRunning
  );

  const getStatusColor = (status: string) => {
    const s = status.toLowerCase();
    if (s === 'thinking' || s === 'executing') return 'bg-amber-400 animate-pulse';
    if (s === 'done') return 'bg-emerald-400';
    if (s === 'error') return 'bg-rose-500';
    return 'bg-gray-500';
  };

  const getMetadataDesc = (label: string) => {
    const l = label.toLowerCase();
    if (l.includes('architect')) return 'spec.md · stack · schema';
    if (l.includes('dba')) return 'database · migrations';
    if (l.includes('frontend')) return 'views · templates · ui';
    if (l.includes('backend')) return 'routes · apis · logic';
    if (l.includes('review')) return 'code quality inspection';
    if (l.includes('fix')) return 'syntactic self-healing';
    if (l.includes('qa')) return 'tests · devops run';
    return 'infrastructure deploy';
  };

  // Helper to extract unique tool names
  const getToolNames = () => {
    const names = toolCalls.map(tc => tc.name);
    if (names.length === 0) {
      if (nodeData.label.toLowerCase().includes('architect')) return ['read_file', 'write_file'];
      if (nodeData.label.toLowerCase().includes('dba')) return ['execute_sql', 'write_file'];
      return ['repl_execute', 'write_file', 'skill'];
    }
    return Array.from(new Set(names));
  };

  // Format tokens count
  const nodeTokens = useGraphStore((s) => s.nodeTokens) || {};
  const agentTokens = nodeTokens[nodeData.id] || 0;
  const formatTokens = (t: number) => {
    if (!t || t <= 0) return '—';
    if (t >= 1000) return `${(t / 1000).toFixed(1)}k tkn`;
    return `${t} tkn`;
  };

  const filesWrittenCount = toolCalls.filter(c => c.name === 'write_file').length || (isPipelineRunning ? 1 : 0);

  return (
    <div
      ref={ref}
      className="agent-inspector absolute w-[320px] bg-[#0A0A1A]/95 backdrop-blur-[20px] border border-indigo-500/30 rounded-xl p-4 shadow-[0_0_1px_rgba(74,158,255,0.3),0_0_40px_rgba(74,158,255,0.2),0_20px_60px_rgba(0,0,0,0.5)] z-[100] font-sans transition-all select-text text-left"
      style={{
        top: position ? `${position.top}px` : '20%',
        left: position ? `${position.left}px` : '35%',
      }}
    >
      <style>{`
        .agent-inspector {
          animation: inspector-in 0.2s ease-out;
        }
        @keyframes inspector-in {
          from { opacity: 0; transform: scale(0.95) translateY(-8px); }
          to { opacity: 1; transform: scale(1) translateY(0); }
        }
      `}</style>

      {/* Top Header line */}
      <div className="flex items-center justify-between text-[8px] font-mono text-gray-500 mb-2">
        <div className="flex items-center gap-1.5">
          <span className={`w-1.5 h-1.5 rounded-full ${getStatusColor(nodeData.status)}`} />
          <span className="uppercase font-bold tracking-wider">{nodeData.status}</span>
          <span>·</span>
          <span>iter 2</span>
        </div>
        <button 
          onClick={onClose}
          className="text-gray-500 hover:text-white hover:underline transition-all cursor-pointer font-bold animate-pulse"
        >
          [x] cerrar
        </button>
      </div>

      {/* Title block */}
      <div className="mb-2">
        <h3 className="text-[12px] font-bold text-white uppercase tracking-wider font-mono">
          {nodeData.label}
        </h3>
        <p className="text-[9px] text-gray-400 font-mono">
          {getMetadataDesc(nodeData.label)}
        </p>
      </div>

      <hr className="border-indigo-500/10 my-2" />

      {/* Métricas */}
      <div className="font-mono text-[9px] text-gray-400 space-y-0.5">
        <div className="text-[7.5px] font-bold text-indigo-400 uppercase tracking-wider mb-1">Métricas</div>
        <div>
          Tokens: <span className="text-gray-200 font-semibold">{formatTokens(agentTokens)}</span>
          {' · '}
          Tiempo: <span className="text-gray-200 font-semibold">{isPipelineRunning ? '18s' : '55s'}</span>
          {' · '}
          Files: <span className="text-gray-200 font-semibold">{filesWrittenCount}</span>
        </div>
      </div>

      <hr className="border-indigo-500/10 my-2" />

      {/* Actividad Reciente */}
      <div className="font-mono text-[9px] text-gray-400 space-y-1">
        <div className="text-[7.5px] font-bold text-indigo-400 uppercase tracking-wider mb-1">Actividad Reciente</div>
        {thinking.length === 0 ? (
          <div className="text-[8px] text-gray-600 italic">Esperando inicio de actividad...</div>
        ) : (
          <div className="bg-[#05050C]/50 border border-white/5 rounded p-2 text-[8.5px] text-gray-300 leading-relaxed max-h-[80px] overflow-y-auto space-y-1">
            {thinking.slice(-3).map((thought, idx) => (
              <div key={idx} className="flex items-start gap-1">
                <span className="text-indigo-400">›</span>
                <span className="truncate max-w-[250px]">{thought}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      <hr className="border-indigo-500/10 my-2" />

      {/* Herramientas Usadas */}
      <div className="font-mono text-[9px] text-gray-400">
        <div className="text-[7.5px] font-bold text-indigo-400 uppercase tracking-wider mb-1">Herramientas Usadas</div>
        <div className="flex flex-wrap gap-1 mt-1">
          {getToolNames().map((tool, idx) => (
            <span key={idx} className="text-[8px] bg-indigo-500/10 text-indigo-300 border border-indigo-500/20 px-1 rounded">
              [{tool}]
            </span>
          ))}
        </div>
      </div>

      <hr className="border-indigo-500/10 my-2" />

      {/* Confianza */}
      <div className="font-mono text-[9px] text-gray-400 space-y-1">
        <div className="flex justify-between items-center text-[7.5px] font-bold text-indigo-400 uppercase tracking-wider">
          <span>Confianza</span>
          <span className="text-[9px] font-semibold text-gray-200">{(confidence * 100).toFixed(0)}%</span>
        </div>
        <div className="flex items-center gap-2 mt-1">
          <div className="flex-1 bg-white/5 h-2 rounded overflow-hidden border border-white/5 p-[1px]">
            <div 
              className="bg-indigo-500 h-full rounded transition-all duration-300"
              style={{ width: `${confidence * 100}%` }}
            />
          </div>
        </div>
      </div>

      <hr className="border-indigo-500/10 my-2.5" />

      {/* Acciones Disponibles */}
      <div className="flex flex-col gap-1.5 font-mono text-[9px]">
        <div className="flex justify-between gap-1 text-[8.5px]">
          <button 
            onClick={() => onViewCode(nodeData.label)}
            className="flex-1 text-center bg-indigo-600/15 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/20 py-1 rounded transition-all cursor-pointer font-bold"
          >
            [Ver código]
          </button>
          <button 
            onClick={() => onViewLogs(nodeData.label)}
            className="flex-1 text-center bg-indigo-600/15 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/20 py-1 rounded transition-all cursor-pointer font-bold"
          >
            [Ver logs]
          </button>
          <button 
            onClick={onViewDiff}
            className="flex-1 text-center bg-indigo-600/15 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/20 py-1 rounded transition-all cursor-pointer font-bold"
          >
            [Ver diff]
          </button>
        </div>

        {/* Conditional Buttons (Retry/HITL) */}
        {nodeData.status.toLowerCase() === 'error' && (
          <button 
            onClick={onRetry}
            className="w-full text-center bg-rose-500/25 hover:bg-rose-500/35 text-rose-300 border border-rose-500/30 py-1.5 rounded transition-all cursor-pointer font-bold uppercase tracking-wider"
          >
            🔄 Reintentar Nodo
          </button>
        )}

        {(nodeData.status.toLowerCase() === 'paused_hitl' || isPausedHitl) && (
          <button 
            onClick={onEscalate}
            className="w-full text-center bg-amber-500/25 hover:bg-amber-500/35 text-amber-300 border border-amber-500/30 py-1.5 rounded transition-all cursor-pointer font-bold uppercase tracking-wider"
          >
            🙋 Escalar a HITL / Aprobar
          </button>
        )}
      </div>
    </div>
  );
}
