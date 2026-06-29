import React, { useState, useEffect, useRef } from 'react';
import { Search, Terminal, Play, Square, Pause, RefreshCw, Layers } from 'lucide-react';

interface Command {
  key: string;
  name: string;
  desc: string;
  icon: React.ReactNode;
  action: () => void;
}

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onExecuteCommand: (action: string) => void;
}

export default function CommandPalette({ isOpen, onClose, onExecuteCommand }: CommandPaletteProps) {
  const [search, setSearch] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setSearch('');
      setActiveIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const commands: Command[] = [
    { key: 'run', name: 'Iniciar Pipeline', desc: 'Lanza la ejecución del enjambre SQUAD', icon: <Play size={14} />, action: () => onExecuteCommand('run') },
    { key: 'pause', name: 'Pausar Pipeline', desc: 'Pone en pausa temporal el grafo de agentes', icon: <Pause size={14} />, action: () => onExecuteCommand('pause') },
    { key: 'resume', name: 'Reanudar Pipeline', desc: 'Aprueba y continúa la tarea suspendida', icon: <Play size={14} />, action: () => onExecuteCommand('resume') },
    { key: 'kill', name: 'Detener Pipeline', desc: 'Cancela la ejecución de todos los procesos activos', icon: <Square size={14} />, action: () => onExecuteCommand('kill') },
    { key: 'clear', name: 'Limpiar Workspace', desc: 'Borra archivos del workspace y reinicia el estado', icon: <RefreshCw size={14} />, action: () => onExecuteCommand('clear') },
    { key: 'workspace', name: 'Cambiar Workspace', desc: 'Cambia a otro proyecto/directorio activo', icon: <Layers size={14} />, action: () => onExecuteCommand('workspace') }
  ];

  const filteredCommands = commands.filter(cmd =>
    cmd.name.toLowerCase().includes(search.toLowerCase()) ||
    cmd.desc.toLowerCase().includes(search.toLowerCase())
  );

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(prev => (prev + 1) % filteredCommands.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(prev => (prev - 1 + filteredCommands.length) % filteredCommands.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredCommands[activeIndex]) {
        filteredCommands[activeIndex].action();
        onClose();
      }
    } else if (e.key === 'Escape') {
      onClose();
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 bg-black/60 backdrop-blur-md flex items-start justify-center pt-[15vh] px-4"
      onClick={onClose}
    >
      <div 
        className="bg-[#0E0E12]/90 border border-white/10 w-full max-w-lg rounded-xl overflow-hidden shadow-2xl flex flex-col backdrop-blur-xl animate-in fade-in slide-in-from-top-4 duration-200"
        onClick={e => e.stopPropagation()}
      >
        {/* Search Input */}
        <div className="flex items-center space-x-3 px-4 py-3.5 border-b border-white/10 bg-black/20">
          <Search size={16} className="text-gray-400" />
          <input
            ref={inputRef}
            type="text"
            value={search}
            onChange={e => {
              setSearch(e.target.value);
              setActiveIndex(0);
            }}
            onKeyDown={handleKeyDown}
            placeholder="Escribe un comando o busca acciones... (Linear style)"
            className="flex-1 bg-transparent text-sm text-white focus:outline-none placeholder-gray-500 font-sans"
          />
          <kbd className="bg-white/5 border border-white/10 rounded px-1.5 py-0.5 text-[9px] text-gray-400 font-mono select-none">
            ESC
          </kbd>
        </div>

        {/* Commands List */}
        <div className="max-h-[300px] overflow-y-auto p-2 space-y-1">
          {filteredCommands.length > 0 ? (
            filteredCommands.map((cmd, idx) => (
              <div
                key={cmd.key}
                onClick={() => {
                  cmd.action();
                  onClose();
                }}
                className={`flex items-center justify-between px-3 py-2.5 rounded-lg cursor-pointer transition-all ${
                  idx === activeIndex 
                    ? 'bg-indigo-500/20 border border-indigo-500/30 text-white' 
                    : 'border border-transparent text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                <div className="flex items-center space-x-3 text-xs">
                  <div className={`p-1.5 rounded-md ${idx === activeIndex ? 'bg-indigo-500/20 text-indigo-400' : 'bg-white/5 text-gray-400'}`}>
                    {cmd.icon}
                  </div>
                  <div>
                    <div className="font-bold text-gray-200">{cmd.name}</div>
                    <div className="text-[10px] text-gray-500 font-sans mt-0.5">{cmd.desc}</div>
                  </div>
                </div>
                {idx === activeIndex && (
                  <span className="text-[9px] font-mono text-indigo-300 bg-indigo-500/10 px-1.5 py-0.5 rounded">
                    ENTER
                  </span>
                )}
              </div>
            ))
          ) : (
            <div className="p-8 text-center text-xs text-gray-500 flex flex-col items-center justify-center space-y-2">
              <Terminal size={24} className="text-gray-600 animate-pulse" />
              <span>No se encontraron comandos coincidentes.</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
