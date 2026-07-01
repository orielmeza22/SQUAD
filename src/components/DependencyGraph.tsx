import React from 'react';
import { GitBranch, FileCode, Database } from 'lucide-react';
import { useApp } from '../context/AppContext';

interface FileNode {
  name: string;
  type: 'backend' | 'frontend' | 'database' | 'config';
  imports: string[];
}

function parseDependencies(currentFiles: Record<string, string>): FileNode[] {
  const filepaths = Object.keys(currentFiles);
  if (filepaths.length === 0) {
    return [
      { name: 'Ningún archivo generado aún en el Workspace.', type: 'config', imports: [] }
    ];
  }

  return filepaths.map(filepath => {
    const filename = filepath.split('/').pop() || filepath;
    const content = currentFiles[filepath] || '';
    
    // Determine type by extension
    let type: 'backend' | 'frontend' | 'database' | 'config' = 'config';
    const ext = filename.split('.').pop()?.toLowerCase();
    if (['py'].includes(ext || '')) {
      type = 'backend';
    } else if (['html', 'css', 'js', 'ts', 'jsx', 'tsx', 'json'].includes(ext || '')) {
      // package.json is config, but index.html is frontend
      if (filename === 'package.json') {
        type = 'config';
      } else {
        type = 'frontend';
      }
    } else if (['sql', 'db', 'sqlite', 'sqlite3'].includes(ext || '')) {
      type = 'database';
    }
    
    // Scan imports matching other files in the workspace
    const imports: string[] = [];
    const lines = content.split('\n');
    lines.forEach(line => {
      const trimmed = line.trim();
      filepaths.forEach(otherPath => {
        const otherName = otherPath.split('/').pop() || otherPath;
        if (otherName === filename) return;
        
        // Remove extension for matching base import statements
        const otherBase = otherName.split('.').slice(0, -1).join('.');
        if (!otherBase) return;
        
        if (type === 'backend') {
          // e.g. import models or from models import ...
          const pyImportRegex = new RegExp(`\\b(import|from)\\s+${otherBase}\\b`);
          if (pyImportRegex.test(trimmed) && !imports.includes(otherName)) {
            imports.push(otherName);
          }
        } else if (type === 'frontend') {
          // e.g. import ... from './models' or require('./models')
          if (trimmed.includes(otherBase) && !imports.includes(otherName)) {
            imports.push(otherName);
          }
        }
      });
    });

    return { name: filename, type, imports };
  });
}

export default function DependencyGraph() {
  const { currentFiles } = useApp();
  const files = parseDependencies(currentFiles);

  const getColor = (type: 'backend' | 'frontend' | 'database' | 'config') => {
    if (type === 'backend') return 'border-indigo-500 bg-indigo-500/10 text-indigo-300';
    if (type === 'frontend') return 'border-amber-500 bg-amber-500/10 text-amber-300';
    if (type === 'database') return 'border-purple-500 bg-purple-500/10 text-purple-300';
    return 'border-gray-500 bg-gray-500/10 text-gray-300';
  };

  return (
    <div className="w-full h-full flex flex-col space-y-4 text-white p-4 font-sans select-text">
      {/* Header */}
      <div className="flex items-center space-x-2 border-b border-white/5 pb-3">
        <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400 border border-indigo-500/20">
          <GitBranch size={16} />
        </div>
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider">Dependency Graph (File-level)</h2>
          <span className="text-[9px] text-gray-400">Estructura e importaciones de los archivos del Workspace en tiempo real</span>
        </div>
      </div>

      {/* SVG Canvas Map */}
      <div className="flex-1 bg-black/40 border border-white/5 rounded-xl p-4 flex flex-col justify-center items-center overflow-auto min-h-[260px] relative select-none">
        
        {/* Legendary Badge Legends */}
        <div className="absolute top-3 left-3 flex flex-wrap gap-2 text-[8px] font-mono uppercase tracking-wider">
          <span className="flex items-center space-x-1"><span className="w-1.5 h-1.5 rounded bg-indigo-500" /> <span>Backend</span></span>
          <span className="flex items-center space-x-1"><span className="w-1.5 h-1.5 rounded bg-amber-500" /> <span>Frontend</span></span>
          <span className="flex items-center space-x-1"><span className="w-1.5 h-1.5 rounded bg-purple-500" /> <span>Database</span></span>
          <span className="flex items-center space-x-1"><span className="w-1.5 h-1.5 rounded bg-gray-500" /> <span>Config</span></span>
        </div>

        {/* Custom interactive flow render */}
        <div className="flex flex-wrap items-center justify-center gap-6 max-w-lg">
          {files.map((file, idx) => (
            <div 
              key={idx} 
              className={`px-3 py-2 border rounded-lg text-[10px] flex items-center space-x-2 font-mono hover:scale-105 transition-all cursor-pointer ${getColor(file.type)}`}
              title={file.imports.length > 0 ? `Importa: ${file.imports.join(', ')}` : 'Sin dependencias internas'}
            >
              {file.type === 'database' ? <Database size={10} /> : <FileCode size={10} />}
              <span>{file.name}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
