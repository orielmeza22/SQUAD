import React from 'react';
import { Shield, Sparkles } from 'lucide-react';

interface ConfidenceHeatmapProps {
  lines?: { text: string; confidence: 'high' | 'medium' | 'low' | 'none' }[];
}

export default function ConfidenceHeatmap({ lines }: ConfidenceHeatmapProps) {
  const mockLines = lines ?? [
    { text: 'import os', confidence: 'none' },
    { text: 'from fastapi import FastAPI, Depends', confidence: 'high' },
    { text: 'from pydantic import BaseModel', confidence: 'high' },
    { text: '', confidence: 'none' },
    { text: 'app = FastAPI(title="Sanatorio API")', confidence: 'high' },
    { text: '', confidence: 'none' },
    { text: 'def validate_user_role(role: str):', confidence: 'high' },
    { text: '    allowed_roles = {"doctor", "admin", "patient"}', confidence: 'high' },
    { text: '    return role in allowed_roles', confidence: 'high' }
  ];

  const getConfidenceStyle = (level: 'high' | 'medium' | 'low' | 'none') => {
    if (level === 'high') return 'border-l-2 border-emerald-500 bg-emerald-500/5';
    if (level === 'medium') return 'border-l-2 border-amber-500 bg-amber-500/5';
    if (level === 'low') return 'border-l-2 border-rose-500 bg-rose-500/5';
    return 'border-l-2 border-transparent';
  };

  return (
    <div className="w-full h-full flex flex-col space-y-3 text-white p-4 font-sans select-text">
      {/* Header */}
      <div className="flex items-center space-x-2 border-b border-white/5 pb-2">
        <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400 border border-indigo-500/20">
          <Shield size={16} />
        </div>
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider">Confidence Heatmap</h2>
          <span className="text-[9px] text-gray-400">Verificación de confianza heurística por línea de código</span>
        </div>
      </div>

      {/* Code heat list viewer */}
      <div className="flex-1 bg-black/45 border border-white/5 rounded-xl p-3 font-mono text-[10.5px] leading-relaxed overflow-y-auto space-y-1 select-text">
        {mockLines.map((line, idx) => (
          <div key={idx} className={`flex px-2 py-0.5 rounded transition-all ${getConfidenceStyle(line.confidence)}`}>
            <span className="text-[9px] text-gray-600 w-8 select-none font-mono text-right pr-2">{idx + 1}</span>
            <span className="flex-1 whitespace-pre select-text text-gray-200">{line.text}</span>
            {line.confidence !== 'none' && (
              <span className={`text-[7px] font-mono uppercase tracking-widest font-bold px-1 rounded select-none ${
                line.confidence === 'high' ? 'text-emerald-400 bg-emerald-500/15' :
                line.confidence === 'medium' ? 'text-amber-400 bg-amber-500/15' : 'text-rose-400 bg-rose-500/15'
              }`}>
                {line.confidence}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
