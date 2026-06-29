import React from 'react';
import { Send, Cpu, Database, UserCheck, MessageSquare } from 'lucide-react';

interface ChatBubble {
  sender: 'Architect' | 'DBA' | 'Backend' | 'QA' | 'Reviewer';
  avatar: React.ReactNode;
  message: string;
  timestamp: string;
  confidence: number;
}

export default function AgentConversation() {
  const dialogues: ChatBubble[] = [
    { sender: 'Architect', avatar: <Cpu size={12} />, message: 'He diseñado el SPEC.md de la aplicación de turnos para el Sanatorio. Integraremos SQLite con rutas REST en FastAPI y un frontend responsivo.', timestamp: '12:30', confidence: 0.96 },
    { sender: 'DBA', avatar: <Database size={12} />, message: 'Perfecto. He implementado el schema de base de datos con 8 tablas relacionales principales (pacientes, doctores, turnos, salas, etc.) y activado las llaves foráneas.', timestamp: '12:32', confidence: 0.94 },
    { sender: 'Backend', avatar: <Send size={12} />, message: 'El backend está listo. Integré los modelos de datos de Pydantic, los controladores CRUD de turnos y levanté el servidor en localhost:5000.', timestamp: '12:33', confidence: 0.91 },
    { sender: 'Reviewer', avatar: <UserCheck size={12} />, message: 'Código auditado y revisado. Validé la seguridad de las consultas SQL contra inyecciones y verifiqué los middlewares CORS. Todo aprobado.', timestamp: '12:34', confidence: 0.98 }
  ];

  return (
    <div className="w-full h-full flex flex-col space-y-4 text-white p-4 font-sans select-text">
      {/* Header */}
      <div className="flex items-center space-x-2 border-b border-white/5 pb-3">
        <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-400 border border-indigo-500/20">
          <MessageSquare size={16} />
        </div>
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider">Agent Conversation View</h2>
          <span className="text-[9px] text-gray-400">Interacciones en lenguaje natural del enjambre durante el ciclo</span>
        </div>
      </div>

      {/* Dialog Chat Stream */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1 select-text">
        {dialogues.map((chat, idx) => (
          <div key={idx} className="flex items-start space-x-3 text-xs select-text">
            {/* Avatar Circle */}
            <div className="w-8 h-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0 select-none">
              {chat.avatar}
            </div>

            {/* Bubble wrapper */}
            <div className="flex-1 bg-[#0E0E12]/40 border border-white/5 rounded-xl p-3.5 space-y-1.5 backdrop-blur-md">
              <div className="flex items-center justify-between text-[9px] text-gray-500 select-none">
                <div className="flex items-center space-x-2">
                  <strong className="text-gray-300 font-sans">{chat.sender} Agent</strong>
                  <span className="text-[8px] px-1 bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 rounded font-mono uppercase tracking-wider">
                    conf {(chat.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <span>{chat.timestamp}</span>
              </div>
              <p className="text-[10px] text-gray-300 leading-relaxed font-sans select-text">
                {chat.message}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
