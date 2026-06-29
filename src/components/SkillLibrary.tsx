import React, { useState } from 'react';
import { Search, Sparkles, BookOpen, Clock, Activity, Check } from 'lucide-react';

interface Skill {
  name: string;
  desc: string;
  version: string;
  usageCount: number;
  successRate: number;
  lastUsed: string;
}

export default function SkillLibrary() {
  const [search, setSearch] = useState('');
  const [injectedSkill, setInjectedSkill] = useState<string | null>(null);

  // Mock list of 47 skills
  const skills: Skill[] = [
    { name: 'FastAPI Router Maker', desc: 'Genera routers REST modularizados en FastAPI con tipado y documentación automáticas.', version: 'v1.4', usageCount: 142, successRate: 98.5, lastUsed: 'Hace 5m' },
    { name: 'SQL Schema Consensus', desc: 'Consensa el esquema SQL inicial entre el Arquitecto y el DBA evitando loops de sintaxis.', version: 'v2.1', usageCount: 98, successRate: 100, lastUsed: 'Hace 12m' },
    { name: 'Async Pytest Generator', desc: 'Produce suites de pruebas asíncronas con pytest-asyncio y mocks del motor DB.', version: 'v1.2', usageCount: 65, successRate: 92.4, lastUsed: 'Hace 23m' },
    { name: 'Tailwind Glassmorphic Injector', desc: 'Aplica clases de blur y opacidad estilo glassmorphism determinísticamente en layouts CSS/Tailwind.', version: 'v3.0', usageCount: 204, successRate: 99.0, lastUsed: 'Hace 1h' },
    { name: 'SQLite Mock Seeder', desc: 'Rellena tablas SQL con datos de prueba realistas generados sintéticamente en lote.', version: 'v1.1', usageCount: 42, successRate: 95.2, lastUsed: 'Hace 2h' },
    { name: 'Pydantic Model Validator', desc: 'Verifica y corrige schemas de Pydantic v2 contra la arquitectura especificada.', version: 'v2.0', usageCount: 119, successRate: 97.8, lastUsed: 'Hace 4h' }
  ];

  const filteredSkills = skills.filter(sk => 
    sk.name.toLowerCase().includes(search.toLowerCase()) || 
    sk.desc.toLowerCase().includes(search.toLowerCase())
  );

  const handleInject = (name: string) => {
    setInjectedSkill(name);
    setTimeout(() => setInjectedSkill(null), 2000);
  };

  return (
    <div className="w-full h-full flex flex-col space-y-4 text-white p-4 font-sans select-text">
      {/* Header and Search */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center space-x-2">
          <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400 border border-indigo-500/20">
            <BookOpen size={16} />
          </div>
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider">Skill Library Explorer</h2>
            <span className="text-[9px] text-gray-400">47 Habilidades descubiertas y listas para inyectar</span>
          </div>
        </div>
        <div className="flex items-center space-x-2 bg-black/30 border border-white/10 rounded-lg px-2.5 py-1.5 w-full sm:w-64">
          <Search size={14} className="text-gray-500" />
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Buscar habilidad semánticamente..."
            className="bg-transparent text-xs text-white focus:outline-none w-full placeholder-gray-600"
          />
        </div>
      </div>

      {/* Grid */}
      <div className="flex-1 overflow-y-auto grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pr-1 select-text">
        {filteredSkills.map((sk, idx) => (
          <div 
            key={idx} 
            className="group relative bg-[#0E0E12]/50 border border-white/5 hover:border-indigo-500/30 rounded-xl p-4 flex flex-col justify-between shadow-lg backdrop-blur-md transition-all duration-300"
          >
            <div className="space-y-2">
              {/* Card Header */}
              <div className="flex items-start justify-between">
                <h3 className="text-xs font-bold text-gray-200 group-hover:text-white transition-colors">{sk.name}</h3>
                <span className="bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 px-1 rounded text-[8px] tracking-wider uppercase font-mono">
                  {sk.version}
                </span>
              </div>
              {/* Card Desc */}
              <p className="text-[10px] text-gray-400 leading-relaxed font-sans line-clamp-3 select-text">
                {sk.desc}
              </p>
            </div>

            {/* Metrics and Action */}
            <div className="mt-4 pt-3 border-t border-white/5 flex items-end justify-between">
              <div className="flex space-x-3 text-[8px] text-gray-500 font-mono">
                <div className="flex items-center space-x-1" title="Contador de Usos">
                  <Activity size={10} />
                  <span>{sk.usageCount}</span>
                </div>
                <div className="flex items-center space-x-1" title="Tasa de Éxito">
                  <Sparkles size={10} className="text-indigo-400" />
                  <span>{sk.successRate}%</span>
                </div>
                <div className="flex items-center space-x-1" title="Último Uso">
                  <Clock size={10} />
                  <span>{sk.lastUsed}</span>
                </div>
              </div>
              
              <button
                onClick={() => handleInject(sk.name)}
                className={`px-2 py-1 rounded text-[8px] font-bold uppercase tracking-wider transition-all cursor-pointer ${
                  injectedSkill === sk.name
                    ? 'bg-emerald-500/20 border border-emerald-500/30 text-emerald-400'
                    : 'bg-white/5 hover:bg-indigo-500/20 hover:text-indigo-300 border border-white/10 hover:border-indigo-500/30 text-gray-300'
                }`}
              >
                {injectedSkill === sk.name ? (
                  <span className="flex items-center space-x-1">
                    <Check size={8} />
                    <span>Inyectada</span>
                  </span>
                ) : (
                  <span>Inyectar</span>
                )}
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
