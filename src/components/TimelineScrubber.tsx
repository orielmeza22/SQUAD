import React, { useState, useEffect } from 'react';
import { Clock, RotateCcw, RefreshCw } from 'lucide-react';
import { useApp } from '../context/AppContext';

const API_BASE = window.location.port === '3000' ? 'http://localhost:8000' : '';

interface Commit {
  hash: string;
  message: string;
  time: string;
}

export default function TimelineScrubber() {
  const { gitCheckout, gitRestoreHead, fetchFiles } = useApp();
  const [commits, setCommits] = useState<Commit[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  const fetchCommits = async () => {
    try {
      const resp = await fetch(`${API_BASE}/api/git/history`);
      const data = await resp.json();
      if (data.success && data.commits && data.commits.length > 0) {
        // Reverse commits so oldest is at index 0 and newest (HEAD) is at the end
        const sortedCommits = [...data.commits].reverse();
        setCommits(sortedCommits);
        
        // Only override index if it's the first fetch or currently at the head
        setCurrentIndex(prev => {
          if (prev === 0 || prev >= sortedCommits.length - 1) {
            return sortedCommits.length - 1;
          }
          return prev;
        });
      }
    } catch (e) {
      console.error('Error fetching git history:', e);
    }
  };

  useEffect(() => {
    fetchCommits();
    const interval = setInterval(fetchCommits, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleScrub = async (index: number) => {
    setCurrentIndex(index);
    const commit = commits[index];
    if (commit) {
      setIsLoading(true);
      await gitCheckout(commit.hash);
      await fetchFiles();
      setIsLoading(false);
    }
  };

  const handleRestore = async () => {
    setIsLoading(true);
    await gitRestoreHead();
    await fetchFiles();
    setCurrentIndex(commits.length - 1);
    setIsLoading(false);
  };

  const activeCommit = commits[currentIndex];
  const isTimeTraveling = currentIndex < commits.length - 1;

  return (
    <div className="w-full h-full flex flex-col space-y-3 text-white p-4 font-sans select-text">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-white/5 pb-2">
        <div className="flex items-center space-x-2">
          <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400 border border-indigo-500/20">
            <Clock size={16} />
          </div>
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider">Timeline Scrubber (VCS Time Travel)</h2>
            <span className="text-[9px] text-gray-400">Desplázate por el historial del repositorio Git en tiempo real</span>
          </div>
        </div>
        <button 
          onClick={fetchCommits}
          className={`p-1.5 hover:bg-white/5 text-gray-400 hover:text-white rounded transition-colors ${isLoading ? 'animate-spin' : ''}`}
          title="Sincronizar commits"
        >
          <RefreshCw size={13} />
        </button>
      </div>

      {/* Scrubber slider and controls */}
      <div className="bg-[#0E0E12]/40 border border-white/5 p-4 rounded-xl flex flex-col space-y-4 backdrop-blur-md">
        
        {commits.length <= 1 ? (
          <div className="text-white/20 italic text-[10px] py-4 text-center">
            Historial del Workspace vacío o insuficiente para el viaje en el tiempo (mínimo 2 commits).
          </div>
        ) : (
          <>
            {/* Slider bar */}
            <div className="space-y-1.5 select-none">
              <div className="flex items-center justify-between text-[9px] text-gray-500 font-mono">
                <span>Antiguo ({commits[0].time})</span>
                <span>Actual ({commits[commits.length - 1].time})</span>
              </div>
              <div className="relative flex items-center">
                <input
                  type="range"
                  min={0}
                  max={commits.length - 1}
                  value={currentIndex}
                  onChange={e => handleScrub(parseInt(e.target.value))}
                  disabled={isLoading}
                  className="w-full accent-indigo-500 bg-white/10 rounded-lg h-1.5 cursor-pointer outline-none disabled:opacity-50"
                />
              </div>
            </div>

            {/* Action Indicators */}
            <div className={`p-3 border rounded-lg flex items-start justify-between text-[10px] transition-all ${
              isTimeTraveling ? 'bg-indigo-500/5 border-indigo-500/20 animate-pulse' : 'bg-black/35 border-white/5'
            }`}>
              <div className="space-y-1">
                <div className="flex items-center space-x-2">
                  <span className="font-bold text-gray-200 uppercase tracking-wider text-[9px]">
                    {isTimeTraveling ? `🕰️ Snapshot: ${activeCommit?.hash}` : '💻 HEAD actual'}
                  </span>
                  <span className="font-mono text-indigo-400 text-[8px]">{activeCommit?.time}</span>
                </div>
                <p className="text-gray-400 text-[9.5px] font-sans leading-relaxed select-text">
                  {activeCommit?.message}
                </p>
              </div>
              
              {isTimeTraveling && (
                <button
                  onClick={handleRestore}
                  disabled={isLoading}
                  className="px-2 py-1 bg-indigo-500/15 hover:bg-indigo-500/25 border border-indigo-500/20 text-indigo-400 hover:text-indigo-300 text-[8px] font-bold uppercase rounded flex items-center space-x-1 transition-all cursor-pointer select-none disabled:opacity-50"
                >
                  <RotateCcw size={8} />
                  <span>Volver al presente</span>
                </button>
              )}
            </div>
          </>
        )}

      </div>
    </div>
  );
}
