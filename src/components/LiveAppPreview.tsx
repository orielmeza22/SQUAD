import React, { useState } from 'react';
import { Monitor, Tablet, Smartphone, ExternalLink, RefreshCw } from 'lucide-react';

export default function LiveAppPreview() {
  const [device, setDevice] = useState<'desktop' | 'tablet' | 'mobile'>('desktop');
  const [key, setKey] = useState(0);

  const getDeviceWidth = () => {
    if (device === 'mobile') return 'w-[375px] h-[667px]';
    if (device === 'tablet') return 'w-[768px] h-[1024px]';
    return 'w-full h-full';
  };

  return (
    <div className="w-full h-full flex flex-col space-y-4 text-white p-4 font-sans select-text">
      {/* Header Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-white/5 pb-3">
        <div className="flex items-center space-x-2">
          <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400 border border-indigo-500/20">
            <Monitor size={16} />
          </div>
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider">Live App Preview</h2>
            <span className="text-[9px] text-gray-400">Interactúa con la aplicación en tiempo real en localhost:5000</span>
          </div>
        </div>

        {/* View Switchers */}
        <div className="flex items-center space-x-2 bg-black/40 border border-white/10 rounded-lg p-1">
          <button
            onClick={() => setDevice('desktop')}
            className={`p-1.5 rounded cursor-pointer transition-all ${device === 'desktop' ? 'bg-indigo-500/20 text-indigo-400' : 'text-gray-500 hover:text-white'}`}
            title="Desktop view"
          >
            <Monitor size={14} />
          </button>
          <button
            onClick={() => setDevice('tablet')}
            className={`p-1.5 rounded cursor-pointer transition-all ${device === 'tablet' ? 'bg-indigo-500/20 text-indigo-400' : 'text-gray-500 hover:text-white'}`}
            title="Tablet view"
          >
            <Tablet size={14} />
          </button>
          <button
            onClick={() => setDevice('mobile')}
            className={`p-1.5 rounded cursor-pointer transition-all ${device === 'mobile' ? 'bg-indigo-500/20 text-indigo-400' : 'text-gray-500 hover:text-white'}`}
            title="Mobile view"
          >
            <Smartphone size={14} />
          </button>
          <div className="w-[1px] h-4 bg-white/10 mx-1" />
          <button
            onClick={() => setKey(prev => prev + 1)}
            className="p-1.5 rounded text-gray-500 hover:text-white cursor-pointer transition-all"
            title="Recargar iframe"
          >
            <RefreshCw size={14} />
          </button>
          <a
            href="http://localhost:5000"
            target="_blank"
            rel="noopener noreferrer"
            className="p-1.5 rounded text-gray-500 hover:text-white cursor-pointer transition-all"
            title="Abrir en pestaña nueva"
          >
            <ExternalLink size={14} />
          </a>
        </div>
      </div>

      {/* Iframe Viewport wrapper */}
      <div className="flex-1 flex items-center justify-center bg-black/35 rounded-xl border border-white/5 p-4 overflow-auto">
        <div className={`transition-all duration-300 shadow-2xl border border-white/10 rounded-lg overflow-hidden bg-white ${getDeviceWidth()}`}>
          <iframe
            key={key}
            src="http://localhost:5000"
            title="Localhost Preview"
            className="w-full h-full border-none bg-white"
            sandbox="allow-scripts allow-same-origin allow-forms"
          />
        </div>
      </div>
    </div>
  );
}
