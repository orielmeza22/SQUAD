import React from 'react';
import { X, Check, Trash2, FileCode } from 'lucide-react';
import { DiffEditor } from '@monaco-editor/react';

interface DiffViewerProps {
  isOpen: boolean;
  onClose: () => void;
  fileName: string;
  originalContent: string;
  modifiedContent: string;
  onAccept: () => void;
  onReject: () => void;
  agentName?: string;
}

export default function DiffViewer({
  isOpen,
  onClose,
  fileName,
  originalContent,
  modifiedContent,
  onAccept,
  onReject,
  agentName = 'Agente Linter Autónomo'
}: DiffViewerProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-md flex items-center justify-center p-6 transition-all duration-300">
      <div className="bg-[#0E0E12]/95 border border-white/10 rounded-2xl w-full max-w-6xl h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-white/10 bg-black/30">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400 border border-indigo-500/20">
              <FileCode size={18} />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white tracking-wide">{fileName}</h2>
              <span className="text-[10px] text-gray-400">
                Cambios sugeridos por: <strong className="text-indigo-400">{agentName}</strong>
              </span>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 hover:bg-white/10 rounded-lg text-gray-400 hover:text-white transition-all cursor-pointer"
          >
            <X size={16} />
          </button>
        </div>

        {/* Diff Editor Container */}
        <div className="flex-1 min-h-0 bg-[#060608]">
          <DiffEditor
            height="100%"
            language={fileName.endsWith('.py') ? 'python' : fileName.endsWith('.js') ? 'javascript' : 'html'}
            theme="vs-dark"
            original={originalContent}
            modified={modifiedContent}
            options={{
              readOnly: true,
              renderSideBySide: true,
              minimap: { enabled: false },
              fontSize: 12,
              fontFamily: 'Fira Code, monospace',
              scrollBeyondLastLine: false,
              lineNumbers: 'on',
              scrollbar: {
                verticalScrollbarSize: 8,
                horizontalScrollbarSize: 8
              }
            }}
          />
        </div>

        {/* Action Footer */}
        <div className="flex items-center justify-between px-6 py-4 border-t border-white/10 bg-black/30">
          <span className="text-[10px] font-mono text-gray-400">
            Split-screen: Original (Izquierda) vs Modificado (Derecha)
          </span>
          <div className="flex space-x-3">
            <button
              onClick={() => {
                onReject();
                onClose();
              }}
              className="flex items-center space-x-1.5 px-4 py-2 text-[10px] font-bold text-rose-400 border border-rose-500/20 bg-rose-500/10 hover:bg-rose-500/25 rounded-lg uppercase tracking-wider transition-all cursor-pointer"
            >
              <Trash2 size={12} />
              <span>Descartar Cambios</span>
            </button>
            <button
              onClick={() => {
                onAccept();
                onClose();
              }}
              className="flex items-center space-x-1.5 px-5 py-2 text-[10px] font-bold text-white bg-indigo-600 hover:bg-indigo-500 rounded-lg uppercase tracking-wider transition-all cursor-pointer shadow-lg shadow-indigo-600/20"
            >
              <Check size={12} />
              <span>Aceptar y Aplicar</span>
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
