import React from 'react';
import { X, Cpu, Clock, Award, Shield, FileText } from 'lucide-react';

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
    confidence?: number;
    thinking?: string[];
    contextReceived?: {
      spec?: string;
      skills?: string[];
      decisions?: string[];
    };
    toolCalls?: ToolCall[];
  } | null;
}

export default function AgentInspector({ isOpen, onClose, nodeData }: AgentInspectorProps) {
  if (!isOpen || !nodeData) return null;

  const confidence = nodeData.confidence ?? 0.85;
  const toolCalls = nodeData.toolCalls ?? [
    { name: 'read_file', args: '{"path": "SPEC.md"}', status: 'success', time: '0.4s' },
    { name: 'write_file', args: '{"path": "db/schema.sql"}', status: 'success', time: '1.2s' },
    { name: 'check_syntax', args: '{"file": "db/schema.sql"}', status: 'success', time: '0.8s' }
  ];

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
              <span className="text-xs font-mono font-bold text-indigo-300">{(confidence * 100).toFixed(0)}%</span>
            </div>
            <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden border border-white/5 p-[1px]">
              <div 
                className={`bg-gradient-to-r ${getConfidenceColor(confidence)} h-full rounded-full transition-all duration-500`}
                style={{ width: `${confidence * 100}%` }}
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
                <span className="font-mono text-indigo-300">SPEC.md (v2.0)</span>
              </div>
              <div className="text-[10px] text-gray-400 space-y-1">
                <div>Skills Inyectadas:</div>
                <div className="flex flex-wrap gap-1 mt-1">
                  {nodeData.contextReceived?.skills?.map((sk, idx) => (
                    <span key={idx} className="bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 px-1.5 py-0.5 rounded text-[8px] uppercase tracking-wider">
                      {sk}
                    </span>
                  )) || (
                    <span className="bg-white/5 text-gray-500 px-1.5 py-0.5 rounded text-[8px]">Ninguna</span>
                  )}
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
              {nodeData.thinking?.map((thought, idx) => (
                <div key={idx} className="flex items-start space-x-2">
                  <span className="text-indigo-400 select-none">›</span>
                  <p>{thought}</p>
                </div>
              )) || (
                <div className="space-y-2.5">
                  <p className="text-emerald-400">// Cargando especificaciones del proyecto...</p>
                  <p>1. Analizando el prompt del usuario: Sanatorio Médico</p>
                  <p>2. Determinando estructura óptima de la base de datos (SQLite)</p>
                  <p>3. Planificando módulos del backend (fastapi) y UI (htmx/templates)</p>
                  <p className="text-indigo-300">✓ Especificación generada con confianza alta.</p>
                </div>
              )}
            </div>
          </div>

          {/* Cronología de Herramientas */}
          <div className="space-y-3">
            <div className="flex items-center space-x-1.5 text-xs font-bold text-gray-300">
              <Clock size={14} className="text-indigo-400" />
              <span>Llamadas a Herramientas</span>
            </div>
            <div className="space-y-2">
              {toolCalls.map((call, idx) => (
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
              ))}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
