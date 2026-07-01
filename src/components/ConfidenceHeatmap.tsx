import React from 'react';
import { Shield } from 'lucide-react';
import { useApp } from '../context/AppContext';

interface ScannedLine {
  text: string;
  confidence: 'high' | 'medium' | 'low' | 'none';
}

function scanCode(code: string, filename: string): ScannedLine[] {
  if (!code) {
    return [{ text: 'Selecciona un archivo activo en el editor para ver el mapa de confianza heurístico en tiempo real.', confidence: 'none' }];
  }
  
  const isPython = filename.endsWith('.py');
  const isJSOrTS = filename.endsWith('.js') || filename.endsWith('.ts') || filename.endsWith('.jsx') || filename.endsWith('.tsx');
  
  const lines = code.split('\n');
  return lines.map(line => {
    const trimmed = line.trim();
    if (!trimmed) {
      return { text: line, confidence: 'none' };
    }
    
    // 1. Low Confidence Indicators (TODOs, Placeholders, Hardcoded secrets, unhandled errors, formatting leftovers)
    const hasTodo = /\b(TODO|FIXME|XXX)\b/i.test(trimmed);
    const hasPlaceholder = /\b(implementar|completar|\.\.\.|implement\s+here)\b/i.test(trimmed);
    const hasSecret = /\b(secret|passwd|password|api_key|token|auth_key|private_key)\b/i.test(trimmed) && /['"`][a-zA-Z0-9_\-]{4,}['"`]/.test(trimmed);
    const hasExceptPass = isPython 
      ? /except\b.*:\s*pass/i.test(trimmed) 
      : isJSOrTS ? /catch\b.*\{\s*\}/i.test(trimmed) : false;
      
    if (hasTodo || hasPlaceholder || hasSecret || hasExceptPass) {
      return { text: line, confidence: 'low' };
    }
    
    // 2. High Confidence Indicators (Imports, Config setups, standard packages)
    const isImport = /^(import\b|from\b|const\s+.*\s*=\s*require\(|import\s+.*\s+from\s+['"])/.test(trimmed);
    if (isImport) {
      return { text: line, confidence: 'high' };
    }
    
    // 3. Functions and class definitions (Checking for type hints and docstrings)
    const isFunctionOrClass = /^(def\b|class\b|function\b|const\s+.*\s*=\s*\(.*\)\s*=>)/.test(trimmed);
    if (isFunctionOrClass) {
      // If it contains type annotations (colon or arrow)
      const hasTypeHints = /:\s*[a-zA-Z_]+|->\s*[a-zA-Z_]+/.test(trimmed);
      return { text: line, confidence: hasTypeHints ? 'high' : 'medium' };
    }
    
    // 4. Default return / business logic
    // Comments are usually none, actual logic is high
    const isComment = isPython ? trimmed.startsWith('#') : isJSOrTS ? trimmed.startsWith('//') || trimmed.startsWith('/*') || trimmed.startsWith('*') : false;
    if (isComment) {
      return { text: line, confidence: 'none' };
    }
    
    return { text: line, confidence: 'high' };
  });
}

export default function ConfidenceHeatmap() {
  const { currentFiles, activeTab } = useApp();
  
  const filename = activeTab ? activeTab.split('/').pop() || activeTab : '';
  const fileContent = activeTab ? (currentFiles[activeTab] || '') : '';
  const scannedLines = scanCode(fileContent, filename);

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
        <div className="flex-1">
          <h2 className="text-xs font-bold uppercase tracking-wider">Confidence Heatmap</h2>
          <span className="text-[9px] text-gray-400">
            {activeTab ? `Análisis heurístico en tiempo real de: ${filename}` : 'Verificación de confianza heurística por línea de código'}
          </span>
        </div>
      </div>

      {/* Code heat list viewer */}
      <div className="flex-1 bg-black/45 border border-white/5 rounded-xl p-3 font-mono text-[10.5px] leading-relaxed overflow-y-auto space-y-1 select-text">
        {scannedLines.map((line, idx) => (
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
