import React from 'react';
import { useApp } from '../context/AppContext';

export default function TelemetryMonitor() {
  const {
    hwTime,
    hwCpuTemp,
    hwCpuUsage,
    hwRamUsage,
    hwRamPercentage,
    hwDiskUsage,
    hwDiskPercentage
  } = useApp();

  return (
    <div className="bg-black/30 border border-white/5 rounded p-4 space-y-4 shadow-lg">
      <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-widest block flex justify-between items-center border-b border-white/5 pb-2">
        <span className="flex items-center space-x-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
          <span>Monitor Físico del Servidor</span>
        </span>
        <span className="text-[10px] text-white/50 font-mono">{hwTime}</span>
      </span>
      
      <div className="space-y-3 pt-1">
        <div>
          <div className="flex justify-between text-[10px] uppercase mb-1 font-mono">
            <span className="text-gray-400">Temperatura CPU</span>
            <span className="text-rose-400 font-bold">{hwCpuTemp}</span>
          </div>
          <div className="w-full bg-black/50 h-1.5 rounded-full overflow-hidden border border-white/5">
            <div 
              className="bg-gradient-to-r from-emerald-500 via-amber-500 to-rose-500 h-full transition-all duration-1000" 
              style={{ width: `${hwCpuUsage}%` }}
            ></div>
          </div>
        </div>

        <div>
          <div className="flex justify-between text-[10px] uppercase mb-1 font-mono">
            <span className="text-gray-400">RAM Utilizada</span>
            <span className="text-amber-400 font-bold">{hwRamUsage}</span>
          </div>
          <div className="w-full bg-black/50 h-1.5 rounded-full overflow-hidden border border-white/5">
            <div 
              className="bg-amber-500 h-full transition-all duration-1000" 
              style={{ width: `${hwRamPercentage}%` }}
            ></div>
          </div>
        </div>

        <div>
          <div className="flex justify-between text-[10px] uppercase mb-1 font-mono">
            <span className="text-gray-400">Disco / Storage</span>
            <span className="text-blue-400 font-bold">{hwDiskUsage}</span>
          </div>
          <div className="w-full bg-black/50 h-1.5 rounded-full overflow-hidden border border-white/5">
            <div 
              className="bg-blue-500 h-full transition-all duration-1000" 
              style={{ width: `${hwDiskPercentage}%` }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  );
}
