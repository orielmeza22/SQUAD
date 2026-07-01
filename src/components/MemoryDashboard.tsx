import React, { useState, useEffect } from 'react';
import { Shield, Brain, Sparkles, RefreshCw } from 'lucide-react';

interface Assumption {
  id: string;
  title: string;
  details: string;
  resolved_value?: string | null;
  status: 'pending' | 'approved' | 'rejected';
}

interface Decision {
  key: string;
  value: string;
}

const API_BASE = window.location.port === '3000' ? 'http://localhost:8000' : '';

export default function MemoryDashboard() {
  const [assumptions, setAssumptions] = useState<Assumption[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const fetchMemory = async () => {
    try {
      setIsLoading(true);
      const resp = await fetch(`${API_BASE}/api/infra/memory`);
      const data = await resp.json();
      
      setAssumptions(data.assumptions || []);
      
      const decList: Decision[] = [];
      if (data.decisions) {
        Object.entries(data.decisions).forEach(([k, v]) => {
          decList.push({ key: k, value: String(v) });
        });
      }
      setDecisions(decList);
    } catch (e) {
      console.error('Error fetching memory:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMemory();
    const interval = setInterval(fetchMemory, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleStatusChange = async (id: string, newStatus: 'confirmed' | 'overridden') => {
    try {
      setAssumptions(prev => prev.map(a => a.id === id ? { ...a, status: newStatus === 'confirmed' ? 'approved' : 'rejected' } : a));
      
      await fetch(`${API_BASE}/api/infra/memory/assumption/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, status: newStatus, value: "Resuelto mediante control interactivo de usuario" })
      });
      fetchMemory();
    } catch (e) {
      console.error('Error resolving assumption:', e);
    }
  };

  return (
    <div className="w-full h-full flex flex-col space-y-4 text-white p-4 font-sans select-text">
      {/* Top Header */}
      <div className="flex items-center justify-between border-b border-white/5 pb-2">
        <div className="flex items-center space-x-2">
          <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400 border border-indigo-500/20">
            <Brain size={16} />
          </div>
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider">Memory & Decisions Dashboard</h2>
            <span className="text-[9px] text-gray-400">Seguimiento interactivo en tiempo real de asunciones y decisiones del enjambre</span>
          </div>
        </div>
        <button 
          onClick={fetchMemory}
          className={`p-1.5 hover:bg-white/5 text-gray-400 hover:text-white rounded transition-colors ${isLoading ? 'animate-spin' : ''}`}
          title="Sincronizar memoria"
        >
          <RefreshCw size={13} />
        </button>
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
            {assumptions.length === 0 ? (
              <div className="text-white/20 italic text-[10px] py-4 text-center">
                Ninguna asunción técnica registrada en el workspace actual.
              </div>
            ) : (
              assumptions.map(ass => (
                <div 
                  key={ass.id} 
                  className={`p-3 rounded-lg border flex flex-col justify-between space-y-3 transition-all ${
                    ass.status === 'approved'
                      ? 'bg-emerald-500/5 border-emerald-500/20'
                      : ass.status === 'rejected'
                      ? 'bg-rose-500/5 border-rose-500/20'
                      : 'bg-[#141419]/50 border-amber-500/30 border-dashed animate-pulse'
                  }`}
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-[9px] font-mono text-gray-500 uppercase tracking-widest">Asunción #{ass.id}</span>
                      <span className={`text-[8px] px-1.5 py-0.5 rounded font-mono uppercase tracking-widest ${
                        ass.status === 'approved' ? 'text-emerald-400 bg-emerald-500/10' :
                        ass.status === 'rejected' ? 'text-rose-400 bg-rose-500/10' : 'text-amber-400 bg-amber-500/10'
                      }`}>
                        {ass.status}
                      </span>
                    </div>
                    <h4 className="text-[10px] font-bold text-gray-200 mt-2">{ass.title}</h4>
                    <p className="text-[9.5px] text-gray-400 font-sans leading-relaxed mt-1 select-text">{ass.details}</p>
                    {ass.resolved_value && (
                      <div className="text-[8.5px] text-indigo-300 font-mono mt-1 border-t border-white/5 pt-1">
                        Resolución: {ass.resolved_value}
                      </div>
                    )}
                  </div>

                  {ass.status === 'pending' && (
                    <div className="flex justify-end space-x-2 pt-1">
                      <button
                        onClick={() => handleStatusChange(ass.id, 'overridden')}
                        className="px-2 py-1 bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/20 text-rose-400 hover:text-rose-300 text-[8px] font-bold uppercase rounded transition-all cursor-pointer"
                      >
                        Rechazar
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
              ))
            )}
          </div>
        </div>

        {/* Decision Memory Timeline */}
        <div className="bg-[#0E0E12]/40 border border-white/5 rounded-xl p-4 flex flex-col space-y-3 backdrop-blur-md">
          <h3 className="text-xs font-bold text-gray-200 border-b border-white/5 pb-2 uppercase tracking-wider flex items-center space-x-2">
            <Shield size={12} className="text-indigo-400" />
            <span>Decision Memory Timeline</span>
          </h3>
          <div className="flex-1 space-y-3 overflow-y-auto max-h-[300px] pr-1">
            {decisions.length === 0 ? (
              <div className="text-white/20 italic text-[10px] py-4 text-center">
                Ninguna decisión arquitectónica registrada aún.
              </div>
            ) : (
              decisions.map((dec, idx) => (
                <div key={idx} className="flex items-start space-x-3 text-[10px]">
                  <div className="flex-1 bg-[#141419]/50 border border-white/5 p-2.5 rounded-lg space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-gray-200 uppercase text-[9px] tracking-wide">{dec.key}</span>
                    </div>
                    <div className="text-gray-400 text-[9px] font-mono leading-relaxed mt-1 whitespace-pre-wrap select-text">
                      {dec.value}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
