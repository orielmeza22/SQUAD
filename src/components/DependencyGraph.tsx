import React from 'react';
import { GitBranch, FileCode, Database, Layers } from 'lucide-react';

interface FileNode {
  name: string;
  type: 'backend' | 'frontend' | 'database' | 'config';
  imports: string[];
}

export default function DependencyGraph() {
  const files: FileNode[] = [
    { name: 'main_output.py', type: 'backend', imports: ['models.py', 'database.py'] },
    { name: 'models.py', type: 'backend', imports: ['database.py'] },
    { name: 'database.py', type: 'database', imports: [] },
    { name: 'templates/index.html', type: 'frontend', imports: ['static/app.css'] },
    { name: 'static/app.css', type: 'frontend', imports: [] },
    { name: 'requirements.txt', type: 'config', imports: [] }
  ];

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
          <span className="text-[9px] text-gray-400">Estructura e importaciones de los archivos del Workspace</span>
        </div>
      </div>

      {/* SVG Canvas Map */}
      <div className="flex-1 bg-black/40 border border-white/5 rounded-xl p-4 flex flex-col justify-center items-center overflow-auto min-h-[260px] relative select-none">
        
        {/* Legendary Badge Legends */}
        <div className="absolute top-3 left-3 flex flex-wrap gap-2 text-[8px] font-mono uppercase tracking-wider">
          <span className="flex items-center space-x-1"><span className="w-1.5 h-1.5 rounded bg-indigo-500" /> <span>Backend</span></span>
          <span className="flex items-center space-x-1"><span className="w-1.5 h-1.5 rounded bg-amber-500" /> <span>Frontend</span></span>
          <span className="flex items-center space-x-1"><span className="w-1.5 h-1.5 rounded bg-purple-500" /> <span>Database</span></span>
        </div>

        {/* Custom interactive flow render */}
        <div className="flex flex-wrap items-center justify-center gap-6 max-w-lg">
          {files.map((file, idx) => (
            <div 
              key={idx} 
              className={`px-3 py-2 border rounded-lg text-[10px] flex items-center space-x-2 font-mono hover:scale-105 transition-all cursor-pointer ${getColor(file.type)}`}
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
