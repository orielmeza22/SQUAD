import React, { useState } from 'react';
import { Clock, Play, RotateCcw, ChevronLeft, ChevronRight } from 'lucide-react';

interface Milestone {
  id: number;
  label: string;
  time: string;
  desc: string;
}

export default function TimelineScrubber() {
  const [currentVal, setCurrentVal] = useState(2);

  const milestones: Milestone[] = [
    { id: 0, label: 'Inicialización', time: '12:30', desc: 'Workspace inicial creado con SPEC.md.' },
    { id: 1, label: 'Esquema de BD', time: '12:32', desc: 'El DBA generó el archivo db/schema.sql.' },
    { id: 2, label: 'Backend API', time: '12:33', desc: 'Rutas y modelos REST de turnos inyectados en main_output.py.' },
    { id: 3, label: 'Revision Linter', time: '12:34', desc: 'Auditoría del Code Reviewer e inyección del linter autónomo.' }
  ];

  const activeMilestone = milestones[currentVal] || milestones[milestones.length - 1];

  return (
    <div className="w-full h-full flex flex-col space-y-3 text-white p-4 font-sans select-text">
      {/* Header */}
      <div className="flex items-center space-x-2 border-b border-white/5 pb-2">
        <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400 border border-indigo-500/20">
          <Clock size={16} />
        </div>
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider">Timeline Scrubber</h2>
          <span className="text-[9px] text-gray-400">Viaja en el tiempo para ver estados anteriores del Workspace</span>
        </div>
      </div>

      {/* Scrubber slider and controls */}
      <div className="bg-[#0E0E12]/40 border border-white/5 p-4 rounded-xl flex flex-col space-y-4 backdrop-blur-md">
        
        {/* Slider bar */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between text-[9px] text-gray-500 font-mono select-none">
            <span>{milestones[0].time}</span>
            <span>{milestones[milestones.length - 1].time}</span>
          </div>
          <div className="relative flex items-center select-none">
            <input
              type="range"
              min={0}
              max={milestones.length - 1}
              value={currentVal}
              onChange={e => setCurrentVal(parseInt(e.target.value))}
              className="w-full accent-indigo-500 bg-white/10 rounded-lg h-1.5 cursor-pointer outline-none"
            />
          </div>
        </div>

        {/* Action Indicators */}
        <div className="bg-black/35 border border-white/5 p-3 rounded-lg flex items-start justify-between text-[10px]">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="font-bold text-gray-200 uppercase tracking-wider text-[9px]">{activeMilestone.label}</span>
              <span className="font-mono text-indigo-400 text-[8px]">{activeMilestone.time}</span>
            </div>
            <p className="text-gray-400 text-[9.5px] font-sans leading-relaxed">{activeMilestone.desc}</p>
          </div>
          {currentVal < milestones.length - 1 && (
            <button
              onClick={() => setCurrentVal(milestones.length - 1)}
              className="px-2 py-1 bg-indigo-500/15 hover:bg-indigo-500/25 border border-indigo-500/20 text-indigo-400 hover:text-indigo-300 text-[8px] font-bold uppercase rounded flex items-center space-x-1 transition-all cursor-pointer select-none"
            >
              <RotateCcw size={8} />
              <span>Restaurar actual</span>
            </button>
          )}
        </div>

      </div>
    </div>
  );
}
