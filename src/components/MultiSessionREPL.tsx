import React, { useState } from 'react';
import { Terminal, Cpu, Database, Eye } from 'lucide-react';

interface REPLSession {
  id: string;
  name: string;
  status: 'active' | 'idle' | 'error';
  logs: string[];
  icon: React.ReactNode;
}

export default function MultiSessionREPL() {
  const [activeSession, setActiveSession] = useState('architect');

  const sessions: REPLSession[] = [
    {
      id: 'architect',
      name: 'Architect Session',
      status: 'idle',
      icon: <Cpu size={12} />,
      logs: [
        '[12:30:15] [INFO] Iniciando módulo Arquitecto...',
        '[12:30:18] [INFO] Cargando SPEC.md...',
        '[12:31:02] [SUCCESS] Arquitectura validada y guardada.'
      ]
    },
    {
      id: 'dba',
      name: 'DBA Session',
      status: 'active',
      icon: <Database size={12} />,
      logs: [
        '[12:32:00] [INFO] Levantando conexión a base de datos de test...',
        '[12:32:04] [INFO] Creando tablas desde el schema.sql...',
        '[12:32:09] [SUCCESS] Todas las 8 tablas migradas correctamente.'
      ]
    },
    {
      id: 'backend',
      name: 'Backend Dev',
      status: 'active',
      icon: <Terminal size={12} />,
      logs: [
        '[12:33:02] [INFO] Levantando Uvicorn en http://localhost:5000...',
        '[12:33:05] [INFO] Registrando rutas REST de /api/turnos...',
        '[12:33:09] [WARNING] Módulo Pydantic v2 importado con advertencias de compatibilidad.'
      ]
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
              <span className={`w-1.5 h-1.5 rounded-full ${getStatusColor(s.status)}`} />
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
