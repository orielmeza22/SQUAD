import React from 'react';
import { X, Cpu, Clock, Award, Shield, FileText } from 'lucide-react';
import { useApp } from '../context/AppContext';

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

export default function AgentInspector({ isOpen, onClose, nodeData }: AgentInspectorProps) {
  const { pipelineLogs, isPipelineRunning } = useApp();
  
  if (!isOpen || !nodeData) return null;

  const { thinking, toolCalls, confidence, specVersion } = parseInspectorLogs(
    nodeData.label, 
    pipelineLogs, 
    isPipelineRunning
  );

  const getConfidenceColor = (val: number) => {
    if (val >= 0.85) return 'from-emerald-500 to-teal-500';
    if (val >= 0.6) return 'from-amber-500 to-orange-500';
    return 'from-rose-500 to-red-500';
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-end bg-black/40 backdrop-blur-sm transition-all duration-300">
      <div className="h-full w-[460px] border-l border-white/10 bg-[#0E0E12]/80 p-6 shadow-2xl backdrop-blur-xl flex flex-col space-y-6 animate-in slide-in-from-right duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-500/10 rounded-lg border border-indigo-500/20 text-indigo-400">
              <Cpu size={18} />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">{nodeData.label}</h2>
              <span className="text-[9px] font-mono text-indigo-400 uppercase tracking-widest">
                Agente: {nodeData.agentType || 'Orquestador'}
              </span>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-all cursor-pointer"
          >
            <X size={16} />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto space-y-6 pr-2 select-text font-sans">
          
          {/* Confidence Score */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-1.5 text-xs text-gray-300 font-bold">
                <Award size={14} className="text-indigo-400" />
                <span>Confidence Score</span>
              </div>
              <span className="text-xs font-mono font-bold text-indigo-300">
                {isPipelineRunning || pipelineLogs.length > 0 ? `${(confidence * 100).toFixed(0)}%` : '—'}
              </span>
            </div>
            <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden border border-white/5 p-[1px]">
              <div 
                className={`bg-gradient-to-r ${getConfidenceColor(confidence)} h-full rounded-full transition-all duration-500`}
                style={{ width: `${(isPipelineRunning || pipelineLogs.length > 0) ? confidence * 100 : 0}%` }}
              />
            </div>
          </div>

          {/* Context Received */}
          <div className="space-y-3">
            <div className="flex items-center space-x-1.5 text-xs font-bold text-gray-300">
              <FileText size={14} className="text-indigo-400" />
              <span>Contexto Recibido</span>
            </div>
            <div className="bg-black/30 border border-white/5 rounded-lg p-3 space-y-2.5">
              <div className="flex items-center justify-between text-[10px] text-gray-400">
                <span>Especificación Activa:</span>
                <span className="font-mono text-indigo-300">{specVersion}</span>
              </div>
              <div className="text-[10px] text-gray-400 space-y-1">
                <div>Skills Inyectadas:</div>
                <div className="flex flex-wrap gap-1 mt-1">
                  <span className="bg-white/5 text-gray-500 px-1.5 py-0.5 rounded text-[8px]">Ninguna</span>
                </div>
              </div>
            </div>
          </div>

          {/* Thinking Chain */}
          <div className="space-y-3">
            <div className="flex items-center space-x-1.5 text-xs font-bold text-gray-300">
              <Shield size={14} className="text-indigo-400" />
              <span>Thinking Chain (Razonamiento)</span>
            </div>
            <div className="bg-black/40 border border-white/5 rounded-lg p-4 font-mono text-[10px] text-gray-300 leading-relaxed space-y-3">
              {thinking.map((thought, idx) => (
                <div key={idx} className="flex items-start space-x-2">
                  <span className="text-indigo-400 select-none">›</span>
                  <p>{thought}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Cronología de Herramientas */}
          <div className="space-y-3">
            <div className="flex items-center space-x-1.5 text-xs font-bold text-gray-300">
              <Clock size={14} className="text-indigo-400" />
              <span>Llamadas a Herramientas</span>
            </div>
            <div className="space-y-2">
              {toolCalls.length === 0 ? (
                <div className="text-white/20 italic text-[10px] py-2 text-center">
                  Ninguna llamada a herramienta registrada.
                </div>
              ) : (
                toolCalls.map((call, idx) => (
                  <div key={idx} className="bg-[#141419]/60 border border-white/5 p-2.5 rounded-lg flex items-center justify-between text-[10px]">
                    <div className="space-y-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-amber-400 font-bold">{call.name}()</span>
                        <span className="bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-1 rounded text-[8px] uppercase tracking-widest font-bold">
                          {call.status}
                        </span>
                      </div>
                      <code className="text-gray-500 text-[9px] block max-w-[280px] truncate">{call.args}</code>
                    </div>
                    <span className="font-mono text-gray-400 text-[9px]">{call.time}</span>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
