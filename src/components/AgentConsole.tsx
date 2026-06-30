import React from 'react';
import { useApp } from '../context/AppContext';
import { Terminal, Square } from 'lucide-react';

export default function AgentConsole() {
  const {
    pipelineLogs,
    isPipelineRunning,
    launcherLogs,
    setLauncherLogs,
    isAppLaunching,
    setIsAppLaunching,
    stdinInput,
    setStdinInput,
    stdinHistory,
    setStdinHistory,
    stdinHistoryIdx,
    setStdinHistoryIdx,
    logsContainerRef,
    terminalContainerRef,
    tc,
    activeDiagnostic,
    setActiveTab,
    refactorCodeAction,
    showToast,
    pendingWrites,
    resolvePendingWrites
  } = useApp();

  const API_BASE = window.location.port === '3000' ? 'http://localhost:8000' : '';
  const [consoleTab, setConsoleTab] = React.useState<'audit' | 'diagnostic'>('audit');

  const agents = [
    { id: 'architect', name: 'Arquitecto', icon: '🧠', desc: 'Planificación' },
    { id: 'dba', name: 'DBA Agent', icon: '🗄️', desc: 'Esquemas SQL' },
    { id: 'dev', name: 'Dev Agent', icon: '💻', desc: 'Escritura Código' },
    { id: 'qa', name: 'QA Agent', icon: '🔎', desc: 'Verificación tests' },
    { id: 'linter', name: 'Linter Agent', icon: '🧹', desc: 'Sanitización' }
  ];

  const getActiveAgent = (): string => {
    if (!isPipelineRunning || pipelineLogs.length === 0) return '';
    const recentLogs = pipelineLogs.slice(-10).reverse();
    for (const log of recentLogs) {
      const lower = log.toLowerCase();
      if (lower.includes('dba') || lower.includes('database') || lower.includes('base de datos') || lower.includes('provision')) {
        return 'dba';
      }
      if (lower.includes('qa') || lower.includes('test') || lower.includes('verific') || lower.includes('probar') || lower.includes('runner')) {
        return 'qa';
      }
      if (lower.includes('linter') || lower.includes('lint') || lower.includes('eslint') || lower.includes('tsc')) {
        return 'linter';
      }
      if (lower.includes('developer') || lower.includes('dev') || lower.includes('escribiendo') || lower.includes('patch') || lower.includes('edit')) {
        return 'dev';
      }
      if (lower.includes('arquitecto') || lower.includes('orquestador') || lower.includes('planificando') || lower.includes('pensando') || lower.includes('task')) {
        return 'architect';
      }
    }
    return 'architect';
  };

  const activeAgent = getActiveAgent();

  const terminateAppSystem = () => {
    fetch(API_BASE + '/api/infra/terminate', { method: 'POST' })
      .then(r => r.json())
      .then(d => {
        setLauncherLogs(prev => [...prev, "[SISTEMA] Secuencia terminada por el usuario."]);
        setIsAppLaunching(false);
      })
      .catch(() => {
        setIsAppLaunching(false);
      });
  };

  const sendStdin = (e: React.FormEvent) => {
    e.preventDefault();
    if (!stdinInput.trim()) return;
    const cmd = stdinInput;
    setStdinInput('');
    
    // Save to history
    setStdinHistory(prev => [cmd, ...prev].slice(0, 50));
    setStdinHistoryIdx(-1);

    fetch(API_BASE + '/api/infra/stdin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ input: cmd })
    }).catch(e => console.error("Error sending stdin:", e));
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (stdinHistory.length > 0) {
        const nextIdx = Math.min(stdinHistory.length - 1, stdinHistoryIdx + 1);
        setStdinHistoryIdx(nextIdx);
        setStdinInput(stdinHistory[nextIdx]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      const nextIdx = stdinHistoryIdx - 1;
      setStdinHistoryIdx(nextIdx);
      if (nextIdx >= 0) {
        setStdinInput(stdinHistory[nextIdx]);
      } else {
        setStdinInput('');
      }
    }
  };

  return (
    <div className="flex-1 flex flex-col min-h-0 space-y-4">
      {/* 0. SWARM FLOW TOPOLOGY */}
      <div className="bg-[#0b0c10]/40 border border-white/5 rounded-lg p-3 shadow-lg font-mono select-none">
        <style>{`
          @keyframes pulse-ring {
            0% { transform: scale(0.95); opacity: 0.5; }
            50% { transform: scale(1.05); opacity: 0.8; }
            100% { transform: scale(0.95); opacity: 0.5; }
          }
          .agent-active-glow {
            box-shadow: 0 0 15px rgba(245, 158, 11, 0.4);
            animation: pulse-ring 2s infinite ease-in-out;
          }
        `}</style>
        <span className="text-[10px] font-bold text-white/40 uppercase tracking-widest block mb-3 border-b border-white/5 pb-2">
          Flujo de Enjambre (Swarm Topology)
        </span>
        
        <div className="flex items-center justify-between overflow-x-auto py-1 px-1 space-x-1.5 scrollbar-thin">
          {agents.map((agent, index) => {
            const isActive = activeAgent === agent.id;
            return (
              <React.Fragment key={agent.id}>
                {/* Agent Node */}
                <div className="flex flex-col items-center min-w-[70px] transition-all duration-300">
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center text-sm transition-all duration-500 border ${
                    isActive 
                      ? 'bg-amber-500/10 border-amber-400 text-amber-400 agent-active-glow scale-105' 
                      : isPipelineRunning 
                        ? 'bg-blue-500/5 border-blue-500/15 text-blue-300/50' 
                        : 'bg-white/5 border-white/10 text-white/20'
                  }`}>
                    {agent.icon}
                  </div>
                  <span className={`text-[8px] font-bold mt-1 transition-colors duration-300 ${
                    isActive ? 'text-amber-400' : 'text-white/40'
                  }`}>
                    {agent.name}
                  </span>
                  <span className="text-[6px] text-white/25 text-center mt-0.5">
                    {agent.desc}
                  </span>
                </div>

                {/* Connecting Arrow */}
                {index < agents.length - 1 && (
                  <div className="flex-1 flex items-center justify-center min-w-[12px]">
                    <svg className="w-full h-1.5 min-w-[12px]" viewBox="0 0 40 8" fill="none">
                      <path 
                        d="M0 4H36M36 4L32 1M36 4L32 7" 
                        stroke={isActive && isPipelineRunning ? '#f59e0b' : '#1e293b'} 
                        strokeWidth="2"
                        strokeLinecap="round" 
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* 1. AGENTS AUDIT LOGS / CRASH PANEL */}
      <div className="bg-black/30 border border-white/5 rounded p-3 flex-1 flex flex-col overflow-hidden min-h-[160px] shadow-lg font-mono">
        <div className="flex border-b border-white/5 pb-1 select-none items-center justify-between shrink-0">
          <div className="flex space-x-3 text-[10px] font-bold uppercase tracking-wider">
            <button
              onClick={() => setConsoleTab('audit')}
              className={`pb-1 cursor-pointer transition-colors ${
                consoleTab === 'audit' ? 'text-indigo-400 border-b border-indigo-400' : 'text-gray-500 hover:text-white'
              }`}
            >
              Auditoría
            </button>
            <button
              onClick={() => setConsoleTab('diagnostic')}
              className={`pb-1 cursor-pointer transition-colors flex items-center space-x-1 ${
                consoleTab === 'diagnostic' ? 'text-indigo-400 border-b border-indigo-400' : 'text-gray-500 hover:text-white'
              }`}
            >
              <span>Diagnósticos</span>
              {activeDiagnostic && (
                <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-ping shrink-0" />
              )}
            </button>
          </div>
          <span className={`text-[9px] font-bold ${isPipelineRunning ? "text-indigo-400 animate-pulse" : "text-blue-400"}`}>
            {isPipelineRunning ? 'EJECUTANDO' : 'IDLE'}
          </span>
        </div>
        
        {consoleTab === 'audit' ? (
          <div 
            ref={logsContainerRef}
            className="flex-1 overflow-y-auto text-[10px] space-y-2 mt-3 font-mono leading-relaxed pr-1 select-text"
          >
            {pipelineLogs.map((log, i) => {
              let color = 'text-gray-400';
              if (log.includes('✅') || log.includes('🏆')) color = 'text-emerald-400 font-semibold';
              if (log.includes('❌') || log.includes('⚠️')) color = 'text-rose-400';
              if (log.includes('🧠') || log.includes('💻') || log.includes('🎨')) color = 'text-amber-300 mt-2.5 block';
              if (log.includes('🔎') || log.includes('⏱️')) color = 'text-blue-300 mt-2 block';
              return <div key={i} className={color}>{log}</div>;
            })}
            
            {pendingWrites && pendingWrites.map((pw: any, idx: number) => (
              <div key={`pw-${idx}`} className="mt-3 p-3 border border-pink-500/20 bg-pink-500/5 rounded font-sans animate-in fade-in duration-200">
                <div className="flex items-center gap-2 text-pink-400 font-bold text-[10px] uppercase mb-1">
                  <span>?</span>
                  <span>decisión: El archivo "{pw.file}" requiere aprobación humana.</span>
                </div>
                <div className="flex gap-2 mt-2">
                  <button 
                    onClick={() => resolvePendingWrites('confirm', [pw.file])}
                    className="bg-indigo-600 hover:bg-indigo-500 text-white text-[9px] font-bold uppercase tracking-wider px-3 py-1 rounded cursor-pointer transition-all"
                  >
                    Aprobar Escritura
                  </button>
                  <button 
                    onClick={() => resolvePendingWrites('reject', [pw.file])}
                    className="bg-transparent hover:bg-white/5 border border-white/10 text-gray-300 text-[9px] font-bold uppercase tracking-wider px-3 py-1 rounded cursor-pointer transition-all"
                  >
                    Rechazar
                  </button>
                </div>
              </div>
            ))}

            {pipelineLogs.length === 0 && (
              <div className="text-white/20 italic">{'>> Waiting for user target...'}</div>
            )}
          </div>
        ) : (
          <div className="flex-1 overflow-y-auto text-[10px] mt-3 space-y-3 font-sans leading-relaxed pr-1 select-text text-gray-300">
            {activeDiagnostic ? (
              <div className="space-y-3">
                <div className="bg-rose-950/25 border border-rose-500/20 rounded p-3 space-y-2">
                  <div className="flex items-center space-x-1.5 text-rose-400 font-bold font-mono text-[10px] uppercase">
                    <span>⚠️ Crash / Error Detectado</span>
                  </div>
                  <p className="text-[10px] text-gray-300 leading-relaxed font-mono whitespace-pre-wrap select-all">
                    {activeDiagnostic.error}
                  </p>
                </div>

                <div className="bg-black/40 border border-white/5 rounded p-2.5 space-y-2 font-mono text-[9px]">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Archivo:</span>
                    <span className="text-amber-400 select-all">{activeDiagnostic.file}</span>
                  </div>
                  <div className="flex justify-between border-t border-white/5 pt-1.5">
                    <span className="text-gray-500">Línea:</span>
                    <span className="text-amber-400 select-all">{activeDiagnostic.line}</span>
                  </div>
                  {activeDiagnostic.suggestion && (
                    <div className="border-t border-white/5 pt-1.5">
                      <span className="text-gray-500 block mb-1">Sugerencia:</span>
                      <span className="text-gray-400 leading-normal font-sans block">{activeDiagnostic.suggestion}</span>
                    </div>
                  )}
                </div>

                <div className="flex space-x-2 pt-1 font-mono">
                  <button
                    onClick={() => {
                      if (activeDiagnostic.file) {
                        setActiveTab(activeDiagnostic.file);
                        showToast(`📂 Abierto en editor: ${activeDiagnostic.file}`, "info");
                      }
                    }}
                    className="flex-1 bg-white/5 hover:bg-white/10 border border-white/10 text-white font-bold text-[8px] uppercase py-2 rounded transition-all cursor-pointer text-center"
                  >
                    📂 Ir al Archivo
                  </button>
                  <button
                    onClick={() => {
                      refactorCodeAction(activeDiagnostic.file, 'optimize');
                    }}
                    className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-black font-bold text-[8px] uppercase py-2 rounded transition-all cursor-pointer text-center"
                  >
                    🛠️ Autoreparar
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-8 text-white/20 select-none">
                <span className="text-2xl mb-1.5">✅</span>
                <span className="text-[9px] uppercase tracking-wider">Sin errores de ejecución</span>
                <span className="text-[8px] text-white/10 font-mono mt-1">El linter de pre-lanzamiento está limpio</span>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 2. SUBPROCESS RUNNING TERMINAL */}
      <div className="h-48 border border-white/5 bg-[#050507] rounded flex flex-col shrink-0 overflow-hidden shadow-2xl">
        <div className="h-8 border-b border-white/10 flex items-center px-3 bg-black/50 justify-between shrink-0 select-none">
          <span className="text-[9px] font-bold text-white/50 uppercase tracking-widest flex items-center">
            <Terminal size={11} className="mr-1.5" /> Output de Ejecución
          </span>
          <div className="flex space-x-3">
            <button 
              onClick={() => setLauncherLogs([])} 
              className="text-gray-500 hover:text-white text-[8px] font-bold uppercase cursor-pointer"
            >
              Limpiar
            </button>
            {isAppLaunching && (
              <button 
                onClick={terminateAppSystem} 
                className="text-rose-400 hover:text-rose-300 text-[8px] font-bold uppercase flex items-center space-x-1 cursor-pointer"
              >
                <Square size={8} /> <span>Detener</span>
              </button>
            )}
          </div>
        </div>

        <div 
          ref={terminalContainerRef}
          className="flex-1 p-3 overflow-y-auto text-[10px] text-gray-400 font-mono whitespace-pre-wrap leading-relaxed select-text"
        >
          {launcherLogs.map((log, i) => (
            <div key={i} className="mb-0.5">{log}</div>
          ))}
          {launcherLogs.length === 0 && (
            <div className="text-white/10 italic">{'>> Consola inactiva. Lanza el sistema para ver logs...'}</div>
          )}
        </div>
        
        {/* Interactive stdin input form */}
        {isAppLaunching && (
          <form onSubmit={sendStdin} className="h-8 border-t border-white/5 bg-black/40 flex items-center px-3 shrink-0">
            <span className="text-[10px] text-indigo-400 font-bold mr-2 select-none font-mono">$ STDIN &gt;</span>
            <input 
              type="text"
              value={stdinInput}
              onChange={(e) => setStdinInput(e.target.value)}
              placeholder="Escribe un comando o valor interactivo y presiona Enter..."
              className="flex-1 bg-transparent border-none text-[10px] text-white focus:outline-none font-mono"
              onKeyDown={handleKeyDown}
            />
          </form>
        )}
      </div>
    </div>
  );
}
