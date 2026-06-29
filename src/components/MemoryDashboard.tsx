import React, { useState } from 'react';
import { Shield, Brain, Sparkles, Check, RefreshCw } from 'lucide-react';

interface Assumption {
  id: string;
  statement: string;
  sourceAgent: string;
  status: 'pending' | 'confirmed' | 'overridden';
}

interface Decision {
  time: string;
  agent: string;
  title: string;
  choice: string;
  confidence: number;
}

export default function MemoryDashboard() {
  const [assumptions, setAssumptions] = useState<Assumption[]>([
    { id: '1', statement: 'El sanatorio utilizará SQLite localmente para persistencia de turnos de manera temporal.', sourceAgent: 'DBA Agent', status: 'pending' },
    { id: '2', statement: 'El esquema de autenticación por defecto es JWT sin estado.', sourceAgent: 'Architect Agent', status: 'confirmed' },
    { id: '3', statement: 'El volumen de consultas por segundo no superará 100/s.', sourceAgent: 'Infra Agent', status: 'pending' }
  ]);

  const decisions: Decision[] = [
    { time: '12:34:10', agent: 'Architect', title: 'Selección de Stack', choice: 'FastAPI + HTMX + SQLite', confidence: 0.98 },
    { time: '12:35:15', agent: 'DBA', title: 'Límite de Conexiones', choice: '10 conexiones en pool', confidence: 0.88 },
    { time: '12:36:20', agent: 'Backend Dev', title: 'Modelo de Cifrado', choice: 'bcrypt con rounds de 12', confidence: 0.94 }
  ];

  const handleStatusChange = (id: string, newStatus: 'confirmed' | 'overridden') => {
    setAssumptions(prev => prev.map(a => a.id === id ? { ...a, status: newStatus } : a));
  };

  return (
    <div className="w-full h-full flex flex-col space-y-4 text-white p-4 font-sans select-text">
      {/* Top Header */}
      <div className="flex items-center space-x-2">
        <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400 border border-indigo-500/20">
          <Brain size={16} />
        </div>
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider">Memory & Decisions Dashboard</h2>
          <span className="text-[9px] text-gray-400">Seguimiento en tiempo real de asunciones y decisiones del enjambre</span>
        </div>
      </div>

      {/* Main Content Layout */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-6 overflow-y-auto pr-1">
        
        {/* Assumptions Ledger */}
        <div className="bg-[#0E0E12]/40 border border-white/5 rounded-xl p-4 flex flex-col space-y-3 backdrop-blur-md">
          <h3 className="text-xs font-bold text-gray-200 border-b border-white/5 pb-2 uppercase tracking-wider flex items-center space-x-2">
            <Sparkles size={12} className="text-indigo-400" />
            <span>Assumptions Ledger</span>
          </h3>
          <div className="flex-1 space-y-3 overflow-y-auto max-h-[300px]">
            {assumptions.map(ass => (
              <div 
                key={ass.id} 
                className={`p-3 rounded-lg border flex flex-col justify-between space-y-3 transition-all ${
                  ass.status === 'confirmed'
                    ? 'bg-emerald-500/5 border-emerald-500/20'
                    : ass.status === 'overridden'
                    ? 'bg-rose-500/5 border-rose-500/20'
                    : 'bg-[#141419]/50 border-amber-500/30 border-dashed animate-pulse'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[9px] font-mono text-gray-500 uppercase tracking-widest">{ass.sourceAgent}</span>
                    <span className={`text-[8px] px-1.5 py-0.5 rounded font-mono uppercase tracking-widest ${
                      ass.status === 'confirmed' ? 'text-emerald-400 bg-emerald-500/10' :
                      ass.status === 'overridden' ? 'text-rose-400 bg-rose-500/10' : 'text-amber-400 bg-amber-500/10'
                    }`}>
                      {ass.status}
                    </span>
                  </div>
                  <p className="text-[10px] text-gray-300 font-sans leading-relaxed mt-2 select-text">{ass.statement}</p>
                </div>

                {ass.status === 'pending' && (
                  <div className="flex justify-end space-x-2 pt-1">
                    <button
                      onClick={() => handleStatusChange(ass.id, 'overridden')}
                      className="px-2 py-1 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-400 hover:text-rose-300 text-[8px] font-bold uppercase rounded transition-all cursor-pointer"
                    >
                      Override
                    </button>
                    <button
                      onClick={() => handleStatusChange(ass.id, 'confirmed')}
                      className="px-2 py-1 bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 text-emerald-400 hover:text-emerald-300 text-[8px] font-bold uppercase rounded transition-all cursor-pointer"
                    >
                      Confirmar
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Decision Memory Timeline */}
        <div className="bg-[#0E0E12]/40 border border-white/5 rounded-xl p-4 flex flex-col space-y-3 backdrop-blur-md">
          <h3 className="text-xs font-bold text-gray-200 border-b border-white/5 pb-2 uppercase tracking-wider flex items-center space-x-2">
            <Shield size={12} className="text-indigo-400" />
            <span>Decision Memory Timeline</span>
          </h3>
          <div className="flex-1 space-y-3 overflow-y-auto max-h-[300px] pr-1">
            {decisions.map((dec, idx) => (
              <div key={idx} className="flex items-start space-x-3 text-[10px]">
                <span className="font-mono text-gray-500 select-none">{dec.time}</span>
                <div className="flex-1 bg-[#141419]/50 border border-white/5 p-2.5 rounded-lg space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-gray-200">{dec.title}</span>
                    <span className="text-[8px] font-mono text-indigo-400">{dec.agent}</span>
                  </div>
                  <div className="text-gray-400">
                    Elección: <code className="text-indigo-300 font-mono text-[9px]">{dec.choice}</code>
                  </div>
                  <div className="text-[8.5px] text-gray-500">
                    Confianza: <span className="text-emerald-400 font-bold">{(dec.confidence * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
