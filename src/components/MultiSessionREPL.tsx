import React, { useState } from 'react';
import { Terminal, Cpu, Database, Eye } from 'lucide-react';
import { useApp } from '../context/AppContext';

interface REPLSession {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'error';
  logs: string[];
  icon: React.ReactNode;
}

export default function MultiSessionREPL() {
  const { pipelineLogs, isPipelineRunning, activeNode } = useApp();
  const [activeSession, setActiveSession] = useState('architect');

  // Filter logs dynamically based on the session keyword matches
  const getSessionLogs = (sessionId: string): string[] => {
    let filterKeywords: string[] = [];
    if (sessionId === 'architect') {
      filterKeywords = ['architect', 'planificador', 'diseño', 'spec.md'];
    } else if (sessionId === 'dba') {
      filterKeywords = ['dba', 'sql', 'esquema', 'migracion', 'database'];
    } else if (sessionId === 'backend') {
      filterKeywords = ['backend', 'uvicorn', 'fastapi', 'rutas', 'api'];
    } else if (sessionId === 'qa') {
      filterKeywords = ['qa', 'review', 'fix', 'test', 'linter', 'flake8', 'pytest'];
    }

    const filtered = pipelineLogs.filter(log => {
      const lower = log.toLowerCase();
      return filterKeywords.some(kw => lower.includes(kw));
    });

    if (filtered.length === 0) {
      return [`[INFO] Esperando a que el agente correspondiente inicie su tarea...`];
    }
    return filtered;
  };

  // Determine status based on activeNode from orchestrator
  const getSessionStatus = (sessionId: string): 'active' | 'idle' | 'error' => {
    if (!isPipelineRunning) return 'idle';
    
    const active = String(activeNode || '').toLowerCase();
    if (sessionId === 'architect' && active.includes('architect')) return 'active';
    if (sessionId === 'dba' && active.includes('dba')) return 'active';
    if (sessionId === 'backend' && active.includes('backend')) return 'active';
    if (sessionId === 'qa' && (active.includes('qa') || active.includes('review') || active.includes('fix'))) return 'active';
    
    return 'idle';
  };

  const sessions: REPLSession[] = [
    {
      id: 'architect',
      name: 'Architect Session',
      status: getSessionStatus('architect'),
      icon: <Cpu size={12} />,
      logs: getSessionLogs('architect')
    },
    {
      id: 'dba',
      name: 'DBA Session',
      status: getSessionStatus('dba'),
      icon: <Database size={12} />,
      logs: getSessionLogs('dba')
    },
    {
      id: 'backend',
      name: 'Backend Dev',
      status: getSessionStatus('backend'),
      icon: <Terminal size={12} />,
      logs: getSessionLogs('backend')
    },
    {
      id: 'qa',
      name: 'QA & Review',
      status: getSessionStatus('qa'),
      icon: <Terminal size={12} />,
      logs: getSessionLogs('qa')
    }
  ];

  const currentSession = sessions.find(s => s.id === activeSession) || sessions[0];

  const getStatusColor = (status: 'active' | 'idle' | 'error') => {
    if (status === 'active') return 'bg-emerald-500';
    if (status === 'error') return 'bg-rose-500';
    return 'bg-amber-500';
  };

  return (
    <div className="w-full h-full flex flex-col bg-[#0B0B0E]/80 border border-white/10 rounded-xl overflow-hidden shadow-2xl backdrop-blur-md text-white font-sans select-text">
      {/* Tab Header Selector */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/10 bg-black/40">
        <div className="flex items-center space-x-1.5 overflow-x-auto">
          {sessions.map(s => (
            <button
              key={s.id}
              onClick={() => setActiveSession(s.id)}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-[10px] font-bold uppercase transition-all cursor-pointer border ${
                activeSession === s.id
                  ? 'bg-indigo-500/20 border-indigo-500/30 text-indigo-300'
                  : 'bg-white/5 border-transparent text-gray-500 hover:text-white hover:bg-white/10'
              }`}
            >
              <span className="relative flex h-1.5 w-1.5">
                {s.status === 'active' && (
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                )}
                <span className={`relative inline-flex rounded-full h-1.5 w-1.5 ${getStatusColor(s.status)}`}></span>
              </span>
              {s.icon}
              <span>{s.name}</span>
            </button>
          ))}
        </div>
        <div className="flex items-center space-x-2 text-[9px] text-gray-500 font-mono">
          <Eye size={10} />
          <span>Sincronización en tiempo real</span>
        </div>
      </div>

      {/* Terminal logs area */}
      <div className="flex-1 bg-black/50 p-4 font-mono text-[10.5px] leading-relaxed text-indigo-200 overflow-y-auto space-y-2 select-text">
        {currentSession.logs.map((log, idx) => (
          <div key={idx} className="flex items-start space-x-2.5">
            <span className="text-gray-600 select-none">$</span>
            <span className="whitespace-pre-wrap select-text">{log}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
