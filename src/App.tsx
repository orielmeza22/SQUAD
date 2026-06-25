import React, { useState } from 'react';
import { AppContextProvider, useApp } from './context/AppContext';
import { 
  Play, Square, Save, Folder, FolderOpen, File, FileCode, Settings, Search, 
  Trash2, Download, RefreshCw, Send, Terminal, Cpu, Layers, GitBranch, 
  Activity, ChevronRight, ChevronDown, Database, Sparkles, Clock, Coins, 
  Lock, ShieldAlert, CheckCircle, ExternalLink, Moon, Eye, EyeOff, Github
} from 'lucide-react';

// Import subcomponents
import TelemetryMonitor from './components/TelemetryMonitor';
import FileTree from './components/FileTree';
import MonacoEditorPanel from './components/MonacoEditorPanel';
import DatabaseVisualizer from './components/DatabaseVisualizer';
import AgentConsole from './components/AgentConsole';

const categories = {
  "Databases & Cache": [
    { name: "PostgreSQL + Vectorizer", desc: "Base de datos relacional con búsquedas vectoriales híbridas.", defaultChecked: true },
    { name: "Redis Cache Layer", desc: "Almacenamiento clave-valor ultrarrápido en memoria.", defaultChecked: false },
    { name: "Prisma ORM", desc: "Mapeo de datos para Node/TS con seguridad de tipos.", defaultChecked: true },
    { name: "Drizzle SQL Studio", desc: "ORM ligero y Edge-ready sin bloqueos (non-blocking).", defaultChecked: false }
  ],
  "APIs & Backend Logic": [
    { name: "GraphQL API Gateway", desc: "Punto de entrada unificado y tipado para clientes visuales.", defaultChecked: false },
    { name: "Stripe Webhooks", desc: "Recepción de eventos asíncronos y pagos en tiempo real.", defaultChecked: true },
    { name: "WebSockets Engine", desc: "Conexión bidireccional de baja latencia para streaming.", defaultChecked: false }
  ],
  "Security & Auth": [
    { name: "OAuth2 Social Login", desc: "Flujos de inicio de sesión de Google, Github, Apple, etc.", defaultChecked: true },
    { name: "JWT Fingerprinting", desc: "Tokens firmados sin estado con rastreo heurístico del cliente.", defaultChecked: true },
    { name: "Rate Limiter (DDOS)", desc: "Protección de Capa 7 contra bots impulsados por picos de tráfico.", defaultChecked: false },
    { name: "SQL & XSS Guards", desc: "Sanitización automática de cargas inyectadas en las capas REST.", defaultChecked: true }
  ]
};

const parseMarkdown = (mdText: string, hideTechnical: boolean = true) => {
  if (!mdText) return '';
  
  // Split by code blocks first
  const parts = mdText.split(/```/g);
  let html = '';
  
  for (let i = 0; i < parts.length; i++) {
    if (i % 2 === 1) {
      // Inside a code block
      if (hideTechnical) {
        // Skip rendering this technical code block entirely!
        continue;
      }
      // Otherwise, render a clean code block
      const content = parts[i];
      const lines = content.split('\n');
      const lang = lines[0].trim();
      const codeOnly = lines.slice(1).join('\n');
      html += `<div class="bg-black/50 rounded-lg p-3 my-3 border border-white/5 font-mono text-xs overflow-x-auto select-text">
        <div class="text-[8px] text-gray-500 uppercase tracking-widest border-b border-white/5 pb-1 mb-1.5 font-bold">${lang || 'CÓDIGO'}</div>
        <pre class="text-indigo-300 whitespace-pre">${codeOnly}</pre>
      </div>`;
    } else {
      // Outside a code block - standard markdown parsing
      let block = parts[i]
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

      // Headings
      block = block.replace(/^### (.*?)$/gm, '<h3 class="text-base font-bold text-amber-400 mt-4 mb-2 font-mono">$1</h3>');
      block = block.replace(/^## (.*?)$/gm, '<h2 class="text-lg font-bold text-indigo-400 mt-5 mb-3 border-b border-white/10 pb-1 font-mono">$1</h2>');
      block = block.replace(/^# (.*?)$/gm, '<h1 class="text-2xl font-bold text-white mt-6 mb-4 border-b border-indigo-500/30 pb-2 font-mono">$1</h1>');
      
      // Bold / Code tags
      block = block.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white">$1</strong>');
      block = block.replace(/`(.*?)`/g, '<code class="bg-[#141418] px-1.5 py-0.5 rounded text-rose-400 text-xs font-mono">$1</code>');
      
      // Lists
      block = block.replace(/^\- (.*?)$/gm, '<li class="list-disc ml-5 text-gray-300 text-xs leading-relaxed my-1">$1</li>');
      block = block.replace(/^\* (.*?)$/gm, '<li class="list-disc ml-5 text-gray-300 text-xs leading-relaxed my-1">$1</li>');

      // Paragraphs
      block = block.split('\n\n').map(p => {
        if (p.trim().startsWith('<h') || p.trim().startsWith('<li') || p.trim().startsWith('<ul') || p.trim() === '') return p;
        return `<p class="text-gray-300 text-sm leading-relaxed my-3 font-sans">${p}</p>`;
      }).join('\n');

      html += block;
    }
  }
  
  return html;
};

function MainLayout() {
  const {
    theme, setTheme,
    activeSidebarTab, setActiveSidebarTab,
    toasts, setToasts,
    showToast,
    promptDialog, setPromptDialog, promptInputText, setPromptInputText,
    confirmDialog, setConfirmDialog,
    settings, saveSettingsConfig,
    gitCommits, fetchGitHistory, revertGitCommit,
    isApplyingTemplate, applyProjectTemplate,
    models, selectedModel, setSelectedModel,
    promptInput, setPromptInput,
    pipelineLogs, isPipelineRunning, startBuildPipeline, clearWorkspaceAction,
    chatMessage, setChatMessage, chatHistory, isChatThinking, chatTarget, setChatTarget, sendChatMessage,
    vercelUrl, isDeployingVercel, deployToVercel,
    tokenIn, tokenOut, costUsd, cacheHits, saveToVault,
    vaultPrompts,
    temperature, setTemperature,
    pendingWrites, resolvePendingWrites, listeningPorts, killListeningPort,
    isAppLaunching, launchAppSystem,
    deployToRealProvider, refactorCodeAction, runDockerCompose,
    deleteVaultPrompt, providersList, pullOllamaModel,
    contextWindow, setContextWindow, systemPrompt, setSystemPrompt,
    envContent, setEnvContent, envEditMode, setEnvEditMode,
    preflightStatus, installingTools, fetchPreflightStatus, installSystemTool, saveEnvContent,
    isDiffMode, activeTab, editorFontSize, setEditorFontSize, currentFiles,
    dbSchemaData, fetchDbSchemaDiagram,
    githubToken, setGithubToken, githubRepoName, setGithubRepoName, githubPrivate, setGithubPrivate, isPublishingGithub, publishToGithub,
    isDbProvisioning, handleDbProvision,
    chatHistoryRef,
    fetchFiles, fetchListeningPorts, fetchTelemetry,
    tc,
    pipelineStatus, activePort, activeDiagnostic, designIdentity, setDesignIdentity, smartRouting, setSmartRouting,
    optimizePrompt, adjustSpec, approveSpec, seedDb, runUxAudit, runUxFix, extractUxStyle, gitCheckout, gitRestoreHead
  } = useApp();

  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [deployProvider, setDeployProvider] = useState<'vercel' | 'netlify'>('vercel');
  const [configPanelWidth, setConfigPanelWidth] = useState(320);
  const [fileTreeWidth, setFileTreeWidth] = useState(256);
  const [deployToken, setDeployToken] = useState('');
  const [isRealDeploying, setIsRealDeploying] = useState(false);
  const [specFeedback, setSpecFeedback] = useState('');
  const [isRefiningSpec, setIsRefiningSpec] = useState(false);
  const [showRightPanel, setShowRightPanel] = useState(true);
  const [activeRightTab, setActiveRightTab] = useState<'prompt' | 'chat' | 'settings' | 'ux'>('prompt');
  const [showBottomPanel, setShowBottomPanel] = useState(true);
  const [bottomPanelHeight, setBottomPanelHeight] = useState(260);
  const [activeBottomTab, setActiveBottomTab] = useState<'console' | 'database' | 'infra' | 'deploy'>('console');
  const [showTechnicalSpec, setShowTechnicalSpec] = useState(false);

  const startResizingConfig = (mouseDownEvent: React.MouseEvent) => {
    mouseDownEvent.preventDefault();
    const startWidth = configPanelWidth;
    const startX = mouseDownEvent.clientX;

    const doDrag = (mouseMoveEvent: MouseEvent) => {
      const newWidth = startWidth + (mouseMoveEvent.clientX - startX);
      if (newWidth > 220 && newWidth < 800) {
        setConfigPanelWidth(newWidth);
      }
    };

    const stopDrag = () => {
      document.removeEventListener('mousemove', doDrag);
      document.removeEventListener('mouseup', stopDrag);
    };

    document.addEventListener('mousemove', doDrag);
    document.addEventListener('mouseup', stopDrag);
  };

  const startResizingFileTree = (mouseDownEvent: React.MouseEvent) => {
    mouseDownEvent.preventDefault();
    const startWidth = fileTreeWidth;
    const startX = mouseDownEvent.clientX;

    const doDrag = (mouseMoveEvent: MouseEvent) => {
      const newWidth = startWidth + (mouseMoveEvent.clientX - startX);
      if (newWidth > 180 && newWidth < 600) {
        setFileTreeWidth(newWidth);
      }
    };

    const stopDrag = () => {
      document.removeEventListener('mousemove', doDrag);
      document.removeEventListener('mouseup', stopDrag);
    };

    document.addEventListener('mousemove', doDrag);
    document.addEventListener('mouseup', stopDrag);
  };

  const startResizingRightPanel = (mouseDownEvent: React.MouseEvent) => {
    mouseDownEvent.preventDefault();
    const startWidth = configPanelWidth;
    const startX = mouseDownEvent.clientX;

    const doDrag = (mouseMoveEvent: MouseEvent) => {
      const newWidth = startWidth - (mouseMoveEvent.clientX - startX);
      if (newWidth > 240 && newWidth < 800) {
        setConfigPanelWidth(newWidth);
      }
    };

    const stopDrag = () => {
      document.removeEventListener('mousemove', doDrag);
      document.removeEventListener('mouseup', stopDrag);
    };

    document.addEventListener('mousemove', doDrag);
    document.addEventListener('mouseup', stopDrag);
  };

  const startResizingBottomPanel = (mouseDownEvent: React.MouseEvent) => {
    mouseDownEvent.preventDefault();
    const startHeight = bottomPanelHeight;
    const startY = mouseDownEvent.clientY;

    const doDrag = (mouseMoveEvent: MouseEvent) => {
      const newHeight = startHeight - (mouseMoveEvent.clientY - startY);
      if (newHeight > 150 && newHeight < 600) {
        setBottomPanelHeight(newHeight);
      }
    };

    const stopDrag = () => {
      document.removeEventListener('mousemove', doDrag);
      document.removeEventListener('mouseup', stopDrag);
    };

    document.addEventListener('mousemove', doDrag);
    document.addEventListener('mouseup', stopDrag);
  };
  // LLM sub-tabs
  const [llmSubTab, setLlmSubTab] = useState<'provider' | 'params' | 'system' | 'vault' | 'ux'>('provider');
  // CI/CD state
  const [cicdPlatform, setCicdPlatform] = useState<'github' | 'gitlab'>('github');
  const [cicdYaml, setCicdYaml] = useState('');
  const [isGeneratingCicd, setIsGeneratingCicd] = useState(false);
  // Docker Push state
  const [dockerRegistry, setDockerRegistry] = useState<'dockerhub' | 'ghcr'>('dockerhub');
  const [dockerUsername, setDockerUsername] = useState('');
  const [dockerToken, setDockerToken] = useState('');
  const [dockerImageName, setDockerImageName] = useState('squad-app');
  const [dockerTag, setDockerTag] = useState('latest');
  const [isPushingDocker, setIsPushingDocker] = useState(false);
  const [activeCatalogItems, setActiveCatalogItems] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    Object.values(categories).forEach(cat => {
      cat.forEach(item => {
        initial[item.name] = item.defaultChecked;
      });
    });
    return initial;
  });

  const parseEnv = (raw: string): { key: string, val: string }[] => {
    return raw.split('\n').map(line => {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#') || !trimmed.includes('=')) return null;
      const [k, ...vParts] = trimmed.split('=');
      return { key: k.trim(), val: vParts.join('=').trim().replace(/^["']|["']$/g, '') };
    }).filter((item): item is { key: string, val: string } => item !== null);
  };

  const updateEnvFromList = (list: { key: string, val: string }[]) => {
    const newRaw = list.map(item => `${item.key}=${item.val}`).join('\n');
    setEnvContent(newRaw);
  };

  const API_BASE = window.location.port === '3000' ? 'http://localhost:8000' : '';

  const exportZipWorkspace = () => {
    fetch(API_BASE + '/api/infra/zip', { method: 'POST' })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          alert(`📦 Proyecto comprimido exitosamente. Iniciando descarga...`);
          window.location.href = API_BASE + '/api/infra/download-zip';
        } else {
          alert(`❌ Error exportando zip: ${d.message}`);
        }
      })
      .catch(e => alert("Error: " + e));
  };

  const destroyEnvironment = () => {
    if (!confirm("⚠️ ¿ATENCIÓN? Esto borrará TODO el contenido del workspace local. No podrás recuperarlo. ¿Continuar?")) return;
    fetch(API_BASE + '/api/infra/destroy', { method: 'POST' })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          alert("Workspace destruido.");
          fetchFiles();
        } else {
          alert("Error destruyendo workspace: " + d.message);
        }
      })
      .catch(e => alert("Error: " + e));
  };

  const triggerTimeTravelRevert = () => {
    if (!confirm("⏱️ ¿Deseas revertir el workspace al snapshot inmediato anterior guardado en Shadow Git?")) return;
    fetch(API_BASE + '/api/infra/timetravel', { method: 'POST' })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          alert("Reversión exitosa. Recargando archivos...");
          fetchFiles();
        } else {
          alert("Fallo al revertir: " + d.message);
        }
      })
      .catch(() => alert("Error de comunicación de Time Travel."));
  };

  return (
    <div className={`h-screen flex flex-col overflow-hidden font-mono ${tc.bg} ${tc.text} select-none`}>
      
      {/* 1. Header Banner */}
      <header className={`h-14 border-b ${tc.border} ${tc.card} flex items-center justify-between px-6 shrink-0 z-10`}>
        <div className="flex items-center space-x-4">
          <div className={`w-3 h-3 rounded ${tc.accentBg} ${tc.accentGlow} animate-pulse`}></div>
          <span className={`font-bold ${tc.accentText} uppercase tracking-widest text-[11px]`}>
            SQUAD_BUILDER // CORE V6 ASYNC FASTAPI
          </span>
          {isPipelineRunning && (
            <span className="bg-amber-500/20 text-amber-400 px-3 py-1 rounded text-[10px] border border-amber-500/50 font-bold animate-pulse">
              ⚙️ OPERANDO ENJAMBRE
            </span>
          )}
        </div>
        
        <div className="flex space-x-4 text-[9px] text-white/50 uppercase tracking-wider items-center">
          <div className="flex items-center space-x-2 bg-black/20 px-2.5 py-1.5 rounded border border-white/5">
            <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping"></span>
            <span>Ollama: <b className="text-emerald-400">Online</b></span>
          </div>
          <div className="flex items-center space-x-2 bg-black/20 px-2.5 py-1.5 rounded border border-white/5">
            <GitBranch size={10} className="text-blue-400" />
            <span>Shadow Git: <b className="text-blue-400">Activo</b></span>
          </div>
          
          <div className="flex items-center space-x-1 border-l border-white/10 pl-3">
            {/* View toggles */}
            <button 
              onClick={() => setShowBottomPanel(!showBottomPanel)}
              className={`p-1.5 rounded cursor-pointer flex items-center space-x-1 ${showBottomPanel ? 'bg-amber-500/20 text-amber-400' : 'text-gray-500 hover:text-white'}`}
              title="Alternar Panel Inferior (Consola/Base de Datos)"
            >
              <Terminal size={10} />
              <span className="text-[8px] font-bold">Consola</span>
            </button>
            <button 
              onClick={() => setShowRightPanel(!showRightPanel)}
              className={`p-1.5 rounded cursor-pointer flex items-center space-x-1 ${showRightPanel ? 'bg-indigo-500/20 text-indigo-400' : 'text-gray-500 hover:text-white'}`}
              title="Alternar Panel Derecho (Copilot/IA)"
            >
              <Sparkles size={10} />
              <span className="text-[8px] font-bold">Copilot</span>
            </button>

            <button 
              onClick={() => setTheme('dark')} 
              className={`p-1.5 rounded cursor-pointer ${theme === 'dark' ? 'bg-white/10 text-white' : 'text-gray-500 hover:text-white'}`}
              title="Tema Oscuro"
            >
              <Moon size={12} />
            </button>
            <button 
              onClick={() => setTheme('cyberpunk')} 
              className={`p-1.5 rounded font-bold text-[8px] cursor-pointer ${theme === 'cyberpunk' ? 'bg-pink-500/20 text-pink-400' : 'text-gray-500 hover:text-white'}`}
              title="Tema Cyberpunk"
            >
              CYBER
            </button>
            <button 
              onClick={() => setTheme('glass')} 
              className={`p-1.5 rounded font-bold text-[8px] cursor-pointer ${theme === 'glass' ? 'bg-sky-500/20 text-sky-400' : 'text-gray-500 hover:text-white'}`}
              title="Tema Glass"
            >
              GLASS
            </button>

          </div>
        </div>
      </header>

      {/* 2. Main Area */}
      <main className="flex-1 flex min-h-0 overflow-hidden">
        
        {/* Left Navigation Sidebar Menu */}
        <nav className={`w-16 border-r ${tc.border} bg-black/20 flex flex-col items-center py-4 space-y-6 shrink-0`}>
          <button 
            onClick={() => {
              setActiveSidebarTab('build');
              setActiveRightTab('prompt');
              setActiveBottomTab('console');
              setShowRightPanel(true);
              setShowBottomPanel(true);
            }}
            className={`p-2.5 rounded-lg transition-all cursor-pointer ${activeRightTab === 'prompt' && showRightPanel ? 'text-amber-500 bg-amber-500/10' : 'text-gray-500 hover:text-white'}`}
            title="Prompt & Constructor"
          >
            <Sparkles size={18} />
          </button>
          <button 
            onClick={() => {
              setActiveSidebarTab('chat');
              setActiveRightTab('chat');
              setShowRightPanel(true);
            }}
            className={`p-2.5 rounded-lg transition-all cursor-pointer ${activeRightTab === 'chat' && showRightPanel ? 'text-amber-500 bg-amber-500/10' : 'text-gray-500 hover:text-white'}`}
            title="Chat de Agentes"
          >
            <Send size={18} />
          </button>
          <button 
            onClick={() => {
              setActiveSidebarTab('infra');
              setActiveBottomTab('database');
              setShowBottomPanel(true);
            }}
            className={`p-2.5 rounded-lg transition-all cursor-pointer ${activeBottomTab === 'database' && showBottomPanel ? 'text-amber-500 bg-amber-500/10' : 'text-gray-500 hover:text-white'}`}
            title="Base de Datos SQLite"
          >
            <Database size={18} />
          </button>
          <button 
            onClick={() => {
              setActiveSidebarTab('infra');
              setActiveBottomTab('infra');
              setShowBottomPanel(true);
            }}
            className={`p-2.5 rounded-lg transition-all cursor-pointer ${activeBottomTab === 'infra' && showBottomPanel ? 'text-amber-500 bg-amber-500/10' : 'text-gray-500 hover:text-white'}`}
            title="Variables & Docker"
          >
            <Layers size={18} />
          </button>
          <button 
            onClick={() => {
              setActiveSidebarTab('llm');
              setActiveRightTab('settings');
              setShowRightPanel(true);
            }}
            className={`p-2.5 rounded-lg transition-all cursor-pointer ${activeRightTab === 'settings' && showRightPanel ? 'text-amber-500 bg-amber-500/10' : 'text-gray-500 hover:text-white'}`}
            title="Parámetros de IA"
          >
            <Cpu size={18} />
          </button>
          <button 
            onClick={() => {
              setActiveSidebarTab('deploy');
              setActiveBottomTab('deploy');
              setShowBottomPanel(true);
            }}
            className={`p-2.5 rounded-lg transition-all cursor-pointer ${activeBottomTab === 'deploy' && showBottomPanel ? 'text-amber-500 bg-amber-500/10' : 'text-gray-500 hover:text-white'}`}
            title="Despliegue Cloud / Timeline"
          >
            <GitBranch size={18} />
          </button>
        </nav>

        {/* Left Workspace Panel: File Explorer + Shadow Git History */}
        <section 
          style={{ width: `${fileTreeWidth}px` }}
          className={`border-r ${tc.border} ${tc.card} flex flex-col shrink-0 overflow-hidden`}
        >
          {/* File Tree Section */}
          <div className="flex-1 min-h-0 flex flex-col overflow-hidden">
            <FileTree />
          </div>

          {/* Divider */}
          <div className="h-[1px] bg-white/5 border-t border-black" />

          {/* Shadow Git History Section */}
          <div className="h-64 flex flex-col overflow-hidden shrink-0 bg-black/20">
            <div className="h-8 bg-black/40 border-b border-white/5 flex items-center justify-between px-3 shrink-0 select-none">
              <span className="text-[9px] font-bold text-blue-400 uppercase tracking-widest font-mono flex items-center">
                <GitBranch size={10} className="mr-1.5 text-blue-400" />
                Línea Temporal Shadow Git
              </span>
              <div className="flex space-x-2">
                <button
                  onClick={fetchGitHistory}
                  className="text-[8px] text-gray-500 hover:text-white font-mono cursor-pointer"
                >
                  ↻
                </button>
                <button
                  onClick={triggerTimeTravelRevert}
                  className="text-[8px] text-amber-400 hover:text-amber-300 font-mono cursor-pointer"
                  title="Retroceder 1 Snapshot"
                >
                  ⏪ Revert
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto p-2 min-h-0">
              {gitCommits.length === 0 ? (
                <div className="flex flex-col items-center py-6 space-y-2 text-white/20">
                  <GitBranch size={20} />
                  <span className="text-[8px] italic">No hay commits en la línea temporal.</span>
                </div>
              ) : (
                <div className="relative pl-3.5 space-y-0">
                  {/* Vertical timeline line */}
                  <div className="absolute left-[9px] top-1.5 bottom-1.5 w-[1px] bg-blue-500/20"></div>

                  {gitCommits.map((c, i) => (
                    <div key={i} className="relative flex items-start space-x-2 py-1 group">
                      {/* Timeline node dot */}
                      <div className={`relative z-10 w-3 h-3 rounded-full border flex-shrink-0 flex items-center justify-center mt-1 transition-all ${
                        i === 0
                          ? 'bg-blue-500 border-blue-400 shadow-md shadow-blue-500/20'
                          : 'bg-[#0d0d11] border-blue-500/30 group-hover:border-blue-400'
                      }`}>
                        <div className={`w-1 h-1 rounded-full ${i === 0 ? 'bg-white' : 'bg-blue-500/60'}`}></div>
                      </div>

                      {/* Commit info card */}
                      <div className="flex-1 min-w-0 bg-black/30 border border-white/5 rounded p-1.5 group-hover:border-blue-500/20 transition-all">
                        <div className="flex justify-between items-start">
                          <div className="min-w-0 pr-1">
                            <span className={`text-[9px] font-bold block truncate font-mono ${
                              i === 0 ? 'text-blue-300' : 'text-gray-300'
                            }`}>
                              {c.message || 'Auto-commit'}
                            </span>
                            <div className="flex items-center space-x-1.5 mt-0.5 text-[7px] text-gray-600 font-mono">
                              <span>{c.hash?.slice(0, 7) || '???????'}</span>
                              <span>·</span>
                              <span className="truncate">{c.time || 'N/A'}</span>
                              {i === 0 && (
                                <span className="text-[6px] bg-blue-500/20 text-blue-400 border border-blue-500/30 px-1 py-0.2 rounded font-bold">HEAD</span>
                              )}
                            </div>
                          </div>
                          <button
                            onClick={() => revertGitCommit(c.hash)}
                            className="text-[7px] bg-blue-500/10 text-blue-300 border border-blue-500/20 px-1 py-0.2 rounded hover:bg-blue-500/25 shrink-0 cursor-pointer font-mono transition-all opacity-0 group-hover:opacity-100"
                          >
                            Go
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Drag handle for Left Sidebar */}
        <div
          onMouseDown={startResizingFileTree}
          className="w-1 cursor-col-resize hover:bg-amber-500/40 active:bg-amber-500 transition-colors z-20 shrink-0 -ml-[2px]"
          title="Arrastra para regular el tamaño del explorador"
        />

        {/* Editor & Console Central Column */}
        <section className="flex-1 flex flex-col min-h-0 overflow-hidden">
          
          {/* Top Panel: Monaco Editor */}
          <div className="flex-1 min-h-0 flex flex-col relative">
            <MonacoEditorPanel />
          </div>

          {/* Drag handle for Bottom Panel */}
          {showBottomPanel && (
            <div
              onMouseDown={startResizingBottomPanel}
              className="h-1 cursor-row-resize hover:bg-amber-500/40 active:bg-amber-500 transition-colors z-20 shrink-0"
              title="Arrastra para regular la altura de la consola"
            />
          )}

          {/* Bottom Panel Drawer */}
          {showBottomPanel && (
            <div 
              style={{ height: `${bottomPanelHeight}px` }}
              className={`border-t ${tc.border} ${tc.card} flex flex-col shrink-0 overflow-hidden bg-[#0A0A0C]`}
            >
              {/* Bottom Tab Bar */}
              <div className="h-9 bg-black/40 border-b border-white/5 flex items-center justify-between px-4 shrink-0 select-none">
                <div className="flex items-center space-x-4">
                  <button 
                    onClick={() => setActiveBottomTab('console')}
                    className={`text-[9px] uppercase tracking-wider font-bold transition-all cursor-pointer pb-1.5 mt-2 border-b-2 ${activeBottomTab === 'console' ? 'text-amber-400 border-amber-400' : 'text-gray-500 border-transparent hover:text-white'}`}
                  >
                    💻 Consola & Logs
                  </button>
                  <button 
                    onClick={() => setActiveBottomTab('database')}
                    className={`text-[9px] uppercase tracking-wider font-bold transition-all cursor-pointer pb-1.5 mt-2 border-b-2 ${activeBottomTab === 'database' ? 'text-amber-400 border-amber-400' : 'text-gray-500 border-transparent hover:text-white'}`}
                  >
                    🗄️ Base de Datos
                  </button>
                  <button 
                    onClick={() => setActiveBottomTab('infra')}
                    className={`text-[9px] uppercase tracking-wider font-bold transition-all cursor-pointer pb-1.5 mt-2 border-b-2 ${activeBottomTab === 'infra' ? 'text-amber-400 border-amber-400' : 'text-gray-500 border-transparent hover:text-white'}`}
                  >
                    🔌 Variables & Docker
                  </button>
                  <button 
                    onClick={() => setActiveBottomTab('deploy')}
                    className={`text-[9px] uppercase tracking-wider font-bold transition-all cursor-pointer pb-1.5 mt-2 border-b-2 ${activeBottomTab === 'deploy' ? 'text-amber-400 border-amber-400' : 'text-gray-500 border-transparent hover:text-white'}`}
                  >
                    🚀 Despliegue Cloud
                  </button>
                </div>
                <button 
                  onClick={() => setShowBottomPanel(false)}
                  className="text-gray-500 hover:text-rose-400 text-[10px] font-bold"
                  title="Cerrar Panel"
                >
                  ✕
                </button>
              </div>

              {/* Bottom Tab Content */}
              <div className="flex-1 overflow-y-auto p-4 min-h-0">
                {activeBottomTab === 'console' && (
                  <AgentConsole />
                )}

                {activeBottomTab === 'database' && (
                  <DatabaseVisualizer />
                )}

                {activeBottomTab === 'infra' && (
                  <div className="space-y-4 max-w-4xl">
                    {/* Visual .env Editor */}
                    <div className="bg-black/30 border border-white/5 rounded-lg p-3.5 space-y-2 shadow-lg">
                      <span className="text-[10px] font-bold text-amber-500 uppercase tracking-widest block flex justify-between items-center border-b border-white/5 pb-2">
                        <span>Editor de Variables (.env)</span>
                        <button 
                          onClick={() => setEnvEditMode(envEditMode === 'visual' ? 'raw' : 'visual')} 
                          className="text-amber-400 hover:text-amber-300 text-[8px] font-bold font-mono"
                        >
                          MODO: {envEditMode.toUpperCase()}
                        </button>
                      </span>
                      
                      {envEditMode === 'raw' ? (
                        <div className="space-y-2 pt-2">
                          <textarea 
                            value={envContent} 
                            onChange={(e) => setEnvContent(e.target.value)}
                            rows={4}
                            className="w-full bg-[#0A0A0C] border border-white/10 rounded p-1.5 text-white font-mono text-[9px] outline-none focus:border-amber-500/50 resize-none"
                          />
                          <button 
                            onClick={saveEnvContent}
                            className="w-full bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 text-[9px] uppercase font-bold py-1.5 rounded transition-all cursor-pointer"
                          >
                            Guardar .env raw
                          </button>
                        </div>
                      ) : (
                        <div className="space-y-2 pt-2">
                          <div className="space-y-1.5 max-h-[140px] overflow-y-auto pr-0.5">
                            {parseEnv(envContent).length === 0 ? (
                              <span className="text-[9px] text-gray-500 italic block text-center py-2">No hay variables configuradas en .env.</span>
                            ) : (
                              parseEnv(envContent).map((item, idx) => (
                                <div key={idx} className="flex space-x-1.5 items-center">
                                  <input 
                                    type="text" 
                                    value={item.key} 
                                    disabled
                                    className="w-1/3 bg-black/40 border border-white/5 rounded p-1 text-[9px] text-gray-400 font-mono"
                                  />
                                  <input 
                                    type="text" 
                                    value={item.val} 
                                    onChange={(e) => {
                                      const list = parseEnv(envContent);
                                      list[idx].val = e.target.value;
                                      updateEnvFromList(list);
                                    }}
                                    className="flex-1 bg-[#0A0A0C] border border-white/10 rounded p-1 text-[9px] text-white font-mono outline-none focus:border-amber-500/50"
                                  />
                                  <button 
                                    onClick={() => {
                                      const list = parseEnv(envContent).filter((_, i) => i !== idx);
                                      updateEnvFromList(list);
                                    }}
                                    className="text-rose-500 hover:text-rose-400 text-[10px] font-bold px-1"
                                  >
                                    ✕
                                  </button>
                                </div>
                              ))
                            )}
                          </div>
                          
                          {/* Add variable form */}
                          <div className="flex space-x-1.5 border-t border-white/5 pt-2">
                            <input 
                              type="text" 
                              placeholder="NUEVA_CLAVE" 
                              id="new-env-key"
                              className="w-1/2 bg-[#0A0A0C] border border-white/10 rounded p-1 text-[9px] text-white font-mono outline-none focus:border-amber-500/50"
                            />
                            <input 
                              type="text" 
                              placeholder="valor" 
                              id="new-env-value"
                              className="flex-1 bg-[#0A0A0C] border border-white/10 rounded p-1 text-[9px] text-white font-mono outline-none focus:border-amber-500/50"
                            />
                            <button 
                              onClick={() => {
                                const keyInput = document.getElementById('new-env-key') as HTMLInputElement;
                                const valInput = document.getElementById('new-env-value') as HTMLInputElement;
                                if (keyInput && keyInput.value.trim()) {
                                  const list = [...parseEnv(envContent), { key: keyInput.value.trim().toUpperCase(), val: valInput.value.trim() }];
                                  updateEnvFromList(list);
                                  keyInput.value = '';
                                  valInput.value = '';
                                }
                              }}
                              className="bg-amber-600 hover:bg-amber-500 text-white font-bold text-[9px] uppercase px-2.5 rounded transition-all cursor-pointer"
                            >
                              +
                            </button>
                          </div>

                          <button 
                            onClick={saveEnvContent}
                            className="w-full bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 text-[9px] uppercase font-bold py-1 rounded transition-all cursor-pointer"
                          >
                            Guardar Cambios .env
                          </button>
                        </div>
                      )}
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      {/* Docker Compose Control */}
                      <div className="bg-black/30 border border-white/5 rounded-lg p-3.5 space-y-2 shadow-lg">
                        <span className="text-[10px] font-bold text-amber-500 uppercase tracking-widest block border-b border-white/5 pb-2">
                          Docker Compose Orchestrator
                        </span>
                        <div className="flex space-x-2 pt-1">
                          <button 
                            onClick={() => runDockerCompose('up')}
                            className="flex-1 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 text-[8px] uppercase font-bold py-1.5 rounded transition-all cursor-pointer text-center"
                          >
                            Start (Up)
                          </button>
                          <button 
                            onClick={() => runDockerCompose('down')}
                            className="flex-1 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[8px] uppercase font-bold py-1.5 rounded transition-all cursor-pointer text-center"
                          >
                            Stop (Down)
                          </button>
                          <button 
                            onClick={() => runDockerCompose('build')}
                            className="flex-1 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/30 text-[8px] uppercase font-bold py-1.5 rounded transition-all cursor-pointer text-center"
                          >
                            Rebuild
                          </button>
                        </div>
                      </div>

                      {/* Physical Telemetry Monitor component */}
                      <TelemetryMonitor />
                    </div>

                    {/* Danger Zone panel */}
                    <div className="bg-black/30 border border-rose-500/10 rounded-lg p-3.5 space-y-2.5">
                      <span className="text-[10px] font-bold text-rose-500 uppercase tracking-widest block border-b border-rose-500/5 pb-1">Acciones Administrativas</span>
                      <div className="flex space-x-3">
                        <button 
                          onClick={exportZipWorkspace}
                          className="flex-1 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 border border-blue-500/30 text-[9px] uppercase font-bold py-2 rounded transition-colors cursor-pointer"
                        >
                          📦 Exportar Workspace a .ZIP
                        </button>
                        <button 
                          onClick={destroyEnvironment}
                          className="flex-1 bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-[9px] uppercase font-bold py-2 rounded transition-colors cursor-pointer animate-pulse"
                        >
                          🧹 Destruir Workspace
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {activeBottomTab === 'deploy' && (
                  <div className="space-y-4 max-w-4xl">
                    <div className="grid grid-cols-2 gap-4">
                      {/* Real Cloud Deployment Panel */}
                      <div className="bg-black/30 border border-indigo-500/10 rounded-lg p-3.5 space-y-3 shadow-lg">
                        <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest block border-b border-white/5 pb-2 flex items-center justify-between">
                          <span>🚀 Despliegue Real a Producción</span>
                          <span className="text-[8px] text-gray-500 font-normal">CLI automático</span>
                        </span>

                        <div className="flex space-x-2">
                          {(['vercel', 'netlify'] as const).map(p => (
                            <button
                              key={p}
                              onClick={() => setDeployProvider(p)}
                              className={`flex-1 py-1.5 rounded text-[9px] font-bold uppercase border transition-all cursor-pointer ${
                                deployProvider === p
                                  ? p === 'vercel'
                                    ? 'bg-sky-500/20 text-sky-400 border-sky-500/40'
                                    : 'bg-teal-500/20 text-teal-400 border-teal-500/40'
                                  : 'bg-white/5 text-gray-500 border-white/10 hover:text-white'
                              }`}
                            >
                              {p === 'vercel' ? '▲ Vercel' : '◆ Netlify'}
                            </button>
                          ))}
                        </div>

                        <div>
                          <label className="text-[8px] text-gray-500 uppercase block mb-1">
                            {deployProvider === 'vercel' ? 'Vercel API Token' : 'Netlify Personal Token'}
                          </label>
                          <input
                            type="password"
                            value={deployToken}
                            onChange={(e) => setDeployToken(e.target.value)}
                            placeholder={deployProvider === 'vercel' ? 'vc_...' : 'nfp_...'}
                            className="w-full bg-[#0A0A0C] border border-white/10 rounded p-1.5 text-white font-mono text-[10px] outline-none focus:border-indigo-500/50"
                          />
                        </div>

                        <button
                          onClick={() => {
                            if (!deployToken.trim()) { showToast('❌ Introduce un token de autenticación.', 'error'); return; }
                            setIsRealDeploying(true);
                            showToast(`🚀 Iniciando despliegue real con ${deployProvider}...`, 'info');
                            deployToRealProvider(deployProvider, deployToken);
                            setTimeout(() => setIsRealDeploying(false), 5000);
                          }}
                          disabled={isRealDeploying}
                          className={`w-full font-bold text-[10px] uppercase py-2 rounded transition-all cursor-pointer disabled:opacity-50 ${
                            deployProvider === 'vercel'
                              ? 'bg-sky-600 hover:bg-sky-500 text-white'
                              : 'bg-teal-600 hover:bg-teal-500 text-white'
                          }`}
                        >
                          {isRealDeploying ? '⚙️ Desplegando...' : `Desplegar con ${deployProvider.charAt(0).toUpperCase() + deployProvider.slice(1)}`}
                        </button>
                      </div>

                      {/* GitHub Graduation Form */}
                      <div className="bg-black/30 border border-white/5 rounded-lg p-3.5 space-y-3 shadow-lg">
                        <span className="text-[10px] font-bold text-[#2ea44f] uppercase tracking-widest block flex items-center space-x-1.5 border-b border-white/5 pb-2">
                          <Github size={12} />
                          <span>Graduación a GitHub</span>
                        </span>

                        <div className="space-y-2 text-[10px]">
                          <div>
                            <label className="text-[8px] text-gray-500 uppercase block mb-1">GitHub Personal Token</label>
                            <input
                              type="password"
                              value={githubToken}
                              onChange={(e) => setGithubToken(e.target.value)}
                              placeholder="ghp_..."
                              className="w-full bg-[#0A0A0C] border border-white/10 rounded p-1.5 text-white font-mono outline-none focus:border-emerald-500/50"
                            />
                          </div>
                          <div>
                            <label className="text-[8px] text-gray-500 uppercase block mb-1">Nombre del Repositorio</label>
                            <input
                              type="text"
                              value={githubRepoName}
                              onChange={(e) => setGithubRepoName(e.target.value)}
                              placeholder="mi-proyecto-squad"
                              className="w-full bg-[#0A0A0C] border border-white/10 rounded p-1.5 text-white font-mono outline-none focus:border-emerald-500/50"
                            />
                          </div>
                          <div className="flex items-center space-x-2 py-1">
                            <input
                              type="checkbox"
                              id="github-private-chk"
                              checked={githubPrivate}
                              onChange={(e) => setGithubPrivate(e.target.checked)}
                              className="accent-emerald-500 h-3.5 w-3.5"
                            />
                            <label htmlFor="github-private-chk" className="text-gray-400 select-none cursor-pointer">
                              Repositorio Privado
                            </label>
                          </div>

                          <button
                            onClick={publishToGithub}
                            disabled={isPublishingGithub}
                            className="w-full bg-[#2ea44f] hover:bg-[#2c974b] text-black font-bold py-1.5 rounded text-center transition-colors cursor-pointer disabled:opacity-50 uppercase tracking-wider"
                          >
                            {isPublishingGithub ? 'Graduando...' : 'Publicar Repositorio'}
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Vercel Quick Deploy */}
                    <div className="bg-black/30 border border-white/5 rounded-lg p-3.5 space-y-2 shadow-lg">
                      <span className="text-[10px] font-bold text-sky-400 uppercase tracking-widest block border-b border-white/5 pb-2">Despliegue Rápido Vercel (CLI Local)</span>
                      <p className="text-[9px] text-gray-400 leading-relaxed font-sans">
                        Exporta la build estática y la publica con el CLI de Vercel preinstalado.
                      </p>
                      <button
                        onClick={deployToVercel}
                        disabled={isDeployingVercel}
                        className="w-full bg-sky-500/10 hover:bg-sky-500/20 text-sky-400 border border-sky-500/30 text-[9px] uppercase font-bold py-2 rounded transition-all cursor-pointer"
                      >
                        {isDeployingVercel ? 'Desplegando...' : '▲ Despliegue Estático en Vercel'}
                      </button>
                      {vercelUrl && (
                        <div className="bg-emerald-950/20 border border-emerald-500/20 p-2.5 rounded text-[10px] space-y-1 mt-2">
                          <span className="text-emerald-400 font-bold block">✅ URL del Deploy:</span>
                          <a href={vercelUrl} target="_blank" rel="noreferrer" className="text-sky-400 hover:underline break-all font-mono">
                            {vercelUrl}
                          </a>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

        </section>

        {/* Drag handle for Right Sidebar */}
        {showRightPanel && (
          <div
            onMouseDown={startResizingRightPanel}
            className="w-1 cursor-col-resize hover:bg-amber-500/40 active:bg-amber-500 transition-colors z-20 shrink-0 -ml-[2px]"
            title="Arrastra para regular el tamaño del panel de IA"
          />
        )}

        {/* Right Sidebar Panel: AI Assistant */}
        {showRightPanel && (
          <section 
            style={{ width: `${configPanelWidth}px` }}
            className={`border-l ${tc.border} ${tc.card} flex flex-col shrink-0 overflow-hidden bg-[#0A0A0C]`}
          >
            {/* Right Tab Bar */}
            <div className="h-9 bg-black/40 border-b border-white/5 flex items-center justify-between px-3 shrink-0 select-none">
              <div className="flex space-x-3">
                <button 
                  onClick={() => setActiveRightTab('prompt')}
                  className={`text-[9px] uppercase tracking-wider font-bold transition-all cursor-pointer pb-1.5 mt-2 border-b-2 ${activeRightTab === 'prompt' ? 'text-indigo-400 border-indigo-400' : 'text-gray-500 border-transparent hover:text-white'}`}
                >
                  ✨ Prompt
                </button>
                <button 
                  onClick={() => setActiveRightTab('chat')}
                  className={`text-[9px] uppercase tracking-wider font-bold transition-all cursor-pointer pb-1.5 mt-2 border-b-2 ${activeRightTab === 'chat' ? 'text-indigo-400 border-indigo-400' : 'text-gray-500 border-transparent hover:text-white'}`}
                >
                  💬 Chat
                </button>
                <button 
                  onClick={() => setActiveRightTab('settings')}
                  className={`text-[9px] uppercase tracking-wider font-bold transition-all cursor-pointer pb-1.5 mt-2 border-b-2 ${activeRightTab === 'settings' ? 'text-indigo-400 border-indigo-400' : 'text-gray-500 border-transparent hover:text-white'}`}
                >
                  ⚙️ Ajustes IA
                </button>
                <button 
                  onClick={() => setActiveRightTab('ux')}
                  className={`text-[9px] uppercase tracking-wider font-bold transition-all cursor-pointer pb-1.5 mt-2 border-b-2 ${activeRightTab === 'ux' ? 'text-indigo-400 border-indigo-400' : 'text-gray-500 border-transparent hover:text-white'}`}
                >
                  🎨 UI/UX
                </button>
              </div>
              <button 
                onClick={() => setShowRightPanel(false)}
                className="text-gray-500 hover:text-rose-400 text-[10px] font-bold"
                title="Cerrar Panel"
              >
                ✕
              </button>
            </div>

            {/* Right Tab Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0">
              
              {/* Tab: Prompt & swarm controllers */}
              {activeRightTab === 'prompt' && (
                <div className="space-y-4">
                  <div className="bg-black/30 border border-white/5 rounded-lg p-3.5 space-y-2 shadow-lg shrink-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className={`text-[10px] font-bold ${tc.accentText} uppercase tracking-widest block`}>
                        Requisitos del Prompt
                      </span>
                      <div className="flex space-x-1.5">
                        <button
                          onClick={clearWorkspaceAction}
                          disabled={isPipelineRunning || isAppLaunching}
                          className="text-[8px] bg-rose-500/20 hover:bg-rose-500/35 border border-rose-500/30 text-rose-300 px-2 py-0.5 rounded transition-all cursor-pointer font-bold flex items-center space-x-1"
                          title="Limpiar Workspace y reiniciar proyecto"
                        >
                          <span>🧹 Limpiar</span>
                        </button>
                        <button
                          onClick={() => optimizePrompt(promptInput)}
                          disabled={isPipelineRunning || !promptInput.trim()}
                          className="text-[8px] bg-indigo-500/20 hover:bg-indigo-500/35 border border-indigo-500/30 text-indigo-300 px-2 py-0.5 rounded transition-all cursor-pointer font-bold flex items-center space-x-1"
                          title="Optimizar prompt con IA para hacerlo detallado"
                        >
                          <span>✨ Optimizar</span>
                        </button>
                      </div>
                    </div>
                    <textarea 
                      value={promptInput}
                      onChange={(e) => setPromptInput(e.target.value)}
                      className="w-full h-36 bg-[#0A0A0C]/80 border border-white/10 rounded p-2.5 text-xs text-emerald-100 focus:outline-none focus:border-indigo-500 resize-none font-sans leading-relaxed" 
                      placeholder="Ej: Crea una API en Express con una base de datos SQLite para llevar inventario, y un frontend animado..."
                    />
                    <div className="flex space-x-2 pt-1">
                      <button 
                        onClick={startBuildPipeline}
                        disabled={isPipelineRunning || !promptInput.trim()}
                        className={`flex-1 ${tc.accentBg} ${tc.accentHoverBg} text-black font-bold text-[10px] uppercase tracking-widest py-3 rounded transition-all disabled:opacity-50 disabled:cursor-not-allowed ${tc.accentGlow}`}
                      >
                        {isPipelineRunning ? 'Orquestando...' : 'Ejecutar Enjambre'}
                      </button>
                      <button
                        onClick={launchAppSystem}
                        disabled={isAppLaunching || isPipelineRunning}
                        className="bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-black font-bold text-[10px] uppercase tracking-widest px-3 rounded transition-all cursor-pointer flex items-center justify-center space-x-1"
                        title="Lanzar aplicación local (Ejecutar scripts de inicio / Ctrl+Enter)"
                      >
                        <Play size={10} className="fill-black mr-0.5" />
                        <span>{isAppLaunching ? 'Lanzando' : 'Lanzar'}</span>
                      </button>
                      <button 
                        onClick={saveToVault}
                        className="bg-white/5 hover:bg-white/10 border border-white/15 px-3 rounded text-[10px] cursor-pointer"
                        title="Guardar Prompt en Bóveda"
                      >
                        📥
                      </button>
                    </div>
                  </div>

                  {/* Project Templates Gallery */}
                  <div className="bg-black/30 border border-white/5 rounded-lg p-3.5 space-y-3 shadow-lg shrink-0">
                    <span className={`text-[10px] font-bold ${tc.accentText} uppercase tracking-widest block`}>
                      Plantillas Rápidas
                    </span>
                    <div className="grid grid-cols-2 gap-2">
                      <button 
                        disabled={isApplyingTemplate || isPipelineRunning}
                        onClick={() => applyProjectTemplate('fastapi')}
                        className="bg-white/5 hover:bg-white/10 border border-white/10 text-[9px] py-2 rounded text-left px-2.5 transition-all text-emerald-400 font-mono disabled:opacity-50 cursor-pointer"
                      >
                        🐍 FastAPI + SQLite
                      </button>
                      <button 
                        disabled={isApplyingTemplate || isPipelineRunning}
                        onClick={() => applyProjectTemplate('express')}
                        className="bg-white/5 hover:bg-white/10 border border-white/10 text-[9px] py-2 rounded text-left px-2.5 transition-all text-amber-400 font-mono disabled:opacity-50 cursor-pointer"
                      >
                        ⚡ Express.js Node
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab: Debates chatbot */}
              {activeRightTab === 'chat' && (
                <div className="flex flex-col h-[calc(100vh-120px)]">
                  {/* Chat history — 2-column for debate mode */}
                  {chatTarget === 'debate' ? (
                    <div className="flex-1 overflow-y-auto mb-4 min-h-0 space-y-2">
                      <div className="text-[9px] text-center text-white/30 uppercase tracking-widest mb-3 font-mono border-b border-white/5 pb-2">
                        Modo Debate Activo
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        {/* Model A Column */}
                        <div className="flex flex-col space-y-2">
                          <div className="text-[8px] font-bold text-rose-400 uppercase tracking-widest px-2 py-1 bg-rose-500/10 border border-rose-500/20 rounded text-center">🔴 Perspectiva A</div>
                          {chatHistory.filter((_, i) => i % 2 === 1 && chatHistory[i]?.role === 'assistant').map((m, i) => (
                            <div key={i} className="bg-rose-950/20 border border-rose-500/15 rounded-lg p-2 text-[9px] text-rose-100 leading-relaxed font-sans select-text">
                              <p className="whitespace-pre-wrap">{m.content}</p>
                            </div>
                          ))}
                        </div>
                        {/* Model B Column */}
                        <div className="flex flex-col space-y-2">
                          <div className="text-[8px] font-bold text-blue-400 uppercase tracking-widest px-2 py-1 bg-blue-500/10 border border-blue-500/20 rounded text-center">🔵 Perspectiva B</div>
                          {chatHistory.filter((_, i) => i % 2 === 0 && chatHistory[i]?.role === 'assistant').map((m, i) => (
                            <div key={i} className="bg-blue-950/20 border border-blue-500/15 rounded-lg p-2 text-[9px] text-blue-100 leading-relaxed font-sans select-text">
                              <p className="whitespace-pre-wrap">{m.content}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="flex-1 overflow-y-auto mb-4 min-h-0 space-y-3 pr-1">
                      {chatHistory.map((m, i) => (
                        <div 
                          key={i} 
                          className={`rounded-lg p-3 text-[10px] leading-relaxed font-sans select-text border ${
                            m.role === 'user' 
                              ? 'bg-amber-500/10 border-amber-500/20 text-amber-100 ml-6' 
                              : m.role === 'system'
                                ? 'bg-white/3 border-white/5 text-gray-500 italic text-[9px]'
                                : 'bg-black/30 border-white/5 text-gray-200 mr-6'
                          }`}
                        >
                          <div className="flex justify-between items-center mb-1 font-mono text-[8px] text-white/30 uppercase tracking-widest">
                            <span>{m.role === 'user' ? 'Tú (Usuario)' : m.role === 'system' ? 'Sistema' : `Agente: ${chatTarget.toUpperCase()}`}</span>
                          </div>
                          <p className="whitespace-pre-wrap">{m.content}</p>
                        </div>
                      ))}
                      {isChatThinking && (
                        <div className="bg-white/5 border border-white/5 rounded-lg p-3 text-[10px] text-gray-400 italic mr-6 animate-pulse font-sans">
                          <div>El enjambre está analizando y respondiendo...</div>
                          {pipelineLogs.length > 0 && (
                            <div className="text-[9px] text-amber-400 font-mono border-t border-white/5 pt-1.5 mt-1.5 break-all not-italic">
                              {pipelineLogs[pipelineLogs.length - 1]}
                            </div>
                          )}
                        </div>
                      )}
                      <div ref={chatHistoryRef} />
                    </div>
                  )}

                  {/* Input form */}
                  <div className="mt-auto border-t border-white/5 pt-3">
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[8px] text-gray-500 uppercase font-bold font-mono">Modelo / IA Activa:</span>
                      <select 
                        value={selectedModel}
                        onChange={(e) => setSelectedModel(e.target.value)}
                        className="bg-black border border-white/10 rounded text-[9px] text-emerald-400 font-mono px-2 py-0.5 outline-none max-w-[170px] truncate"
                      >
                        {models.map(m => <option key={m} value={m}>{m}</option>)}
                      </select>
                    </div>

                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[8px] text-gray-500 uppercase font-bold font-mono">Destinatario del Chat:</span>
                      <select 
                        value={chatTarget}
                        onChange={(e) => setChatTarget(e.target.value as any)}
                        className="bg-black border border-white/10 rounded text-[9px] text-amber-400 font-mono px-2 py-0.5 outline-none"
                      >
                        <option value="general">Enjambre General</option>
                        <option value="architect">Arquitecto (Planificador)</option>
                        <option value="qa">QA Agent (Verificador)</option>
                        <option value="devops">DevOps Cloud</option>
                        <option value="debate">Debate Multi-Modelo</option>
                      </select>
                    </div>

                    <div className="flex space-x-1.5">
                      <input 
                        type="text" 
                        value={chatMessage}
                        onChange={(e) => setChatMessage(e.target.value)}
                        onKeyDown={(e) => { if (e.key === 'Enter' && !isChatThinking) sendChatMessage(); }}
                        placeholder={chatTarget === 'debate' ? "Escribe la tesis a debatir..." : "Pregunta sobre el código, arquitectura..."}
                        className="flex-1 bg-black border border-white/10 rounded-lg p-2 text-xs text-white outline-none focus:border-amber-500/50 font-sans"
                      />
                      <button 
                        onClick={sendChatMessage}
                        disabled={isChatThinking || !chatMessage.trim()}
                        className="bg-amber-500 hover:bg-amber-400 disabled:opacity-50 text-black font-bold text-[10px] uppercase px-3.5 rounded-lg transition-colors cursor-pointer"
                      >
                        Enviar
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab: Settings */}
              {activeRightTab === 'settings' && (
                <div className="space-y-4">
                  {/* LLM Sub-tab nav */}
                  <div className="flex border-b border-white/5 bg-black/20 shrink-0">
                    {([
                      { id: 'provider', label: '🤖 IA' },
                      { id: 'params', label: '⚙️ Params' },
                      { id: 'system', label: '🧠 System' },
                      { id: 'vault', label: '💾 Vault' }
                    ] as const).map(tab => (
                      <button
                        key={tab.id}
                        onClick={() => setLlmSubTab(tab.id as any)}
                        className={`flex-1 py-1.5 text-[8px] font-bold uppercase tracking-wide transition-all border-b-2 cursor-pointer ${
                          llmSubTab === tab.id
                            ? 'border-fuchsia-500 text-fuchsia-400 bg-fuchsia-500/5'
                            : 'border-transparent text-gray-500 hover:text-white'
                        }`}
                      >
                        {tab.label}
                      </button>
                    ))}
                  </div>

                  {/* Provider Settings */}
                  {llmSubTab === 'provider' && (
                    <div className="space-y-3.5">
                      <div className="bg-black/30 border border-white/5 rounded-lg p-3 shadow-lg">
                        <span className="text-[9px] font-bold text-fuchsia-400 uppercase tracking-widest block border-b border-white/5 pb-1.5 mb-2">📊 Telemetría de Uso</span>
                        <div className="grid grid-cols-2 gap-2 text-[9px] font-mono">
                          <div>En: <b className="text-white">{tokenIn.toLocaleString()}</b></div>
                          <div>Out: <b className="text-white">{tokenOut.toLocaleString()}</b></div>
                          <div>Costo: <b className="text-emerald-400">${costUsd.toFixed(4)}</b></div>
                          <div>Cache Hits: <b className="text-sky-400">{cacheHits}</b></div>
                        </div>
                      </div>

                      <div className="bg-black/30 border border-white/5 rounded-lg p-3 shadow-lg space-y-3">
                        <span className="text-[9px] font-bold text-fuchsia-400 uppercase tracking-widest block border-b border-white/5 pb-1.5">🤖 Selección de Modelo</span>
                        <select 
                          value={selectedModel}
                          onChange={(e) => setSelectedModel(e.target.value)}
                          className="w-full bg-black border border-white/10 rounded p-1.5 text-[10px] text-emerald-400 font-mono focus:border-indigo-500"
                        >
                          {models.map(m => <option key={m} value={m}>{m}</option>)}
                        </select>

                        {/* API Keys Configuration */}
                        <div className="border-t border-white/5 pt-2.5 space-y-2">
                          <span className="text-[8px] font-bold text-gray-400 uppercase block">🔑 Claves de API (IAs Online)</span>
                          <div className="space-y-1.5">
                            <div>
                              <div className="flex justify-between items-center mb-0.5">
                                <span className="text-[7px] text-gray-500 block uppercase font-mono">Google Gemini API Key (AI Studio)</span>
                                <a 
                                  href="https://aistudio.google.com/" 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-[7px] text-fuchsia-400 hover:underline font-mono"
                                >
                                  Obtener Gratis ↗
                                </a>
                              </div>
                              <input
                                type="password"
                                value={parseEnv(envContent).find(x => x.key === 'GEMINI_API_KEY')?.val || ''}
                                onChange={(e) => {
                                  const list = parseEnv(envContent);
                                  const found = list.find(x => x.key === 'GEMINI_API_KEY');
                                  if (found) found.val = e.target.value;
                                  else list.push({ key: 'GEMINI_API_KEY', val: e.target.value });
                                  updateEnvFromList(list);
                                }}
                                placeholder="AIzaSy..."
                                className="w-full bg-[#0A0A0C] border border-white/10 rounded p-1 text-[9px] text-white font-mono outline-none focus:border-indigo-500/50"
                              />
                            </div>
                            <div>
                              <span className="text-[7px] text-gray-500 block uppercase font-mono mb-0.5">OpenAI API Key (De pago)</span>
                              <input
                                type="password"
                                value={parseEnv(envContent).find(x => x.key === 'OPENAI_API_KEY')?.val || ''}
                                onChange={(e) => {
                                  const list = parseEnv(envContent);
                                  const found = list.find(x => x.key === 'OPENAI_API_KEY');
                                  if (found) found.val = e.target.value;
                                  else list.push({ key: 'OPENAI_API_KEY', val: e.target.value });
                                  updateEnvFromList(list);
                                }}
                                placeholder="sk-proj-..."
                                className="w-full bg-[#0A0A0C] border border-white/10 rounded p-1 text-[9px] text-white font-mono outline-none focus:border-indigo-500/50"
                              />
                            </div>
                            <div>
                              <div className="flex justify-between items-center mb-0.5">
                                <span className="text-[7px] text-gray-500 block uppercase font-mono">OpenRouter API Key (IAs Gratis/De Pago)</span>
                                <a 
                                  href="https://openrouter.ai/keys" 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-[7px] text-fuchsia-400 hover:underline font-mono"
                                >
                                  Obtener Clave ↗
                                </a>
                              </div>
                              <input
                                type="password"
                                value={parseEnv(envContent).find(x => x.key === 'OPENROUTER_API_KEY')?.val || ''}
                                onChange={(e) => {
                                  const list = parseEnv(envContent);
                                  const found = list.find(x => x.key === 'OPENROUTER_API_KEY');
                                  if (found) found.val = e.target.value;
                                  else list.push({ key: 'OPENROUTER_API_KEY', val: e.target.value });
                                  updateEnvFromList(list);
                                }}
                                placeholder="sk-or-v1-..."
                                className="w-full bg-[#0A0A0C] border border-white/10 rounded p-1 text-[9px] text-white font-mono outline-none focus:border-indigo-500/50"
                              />
                            </div>
                            <button
                              onClick={saveEnvContent}
                              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-[8px] uppercase py-1 rounded cursor-pointer transition-all"
                            >
                              Guardar Claves API
                            </button>
                          </div>
                        </div>

                        {/* Ollama Pull */}
                        <div className="bg-black/20 p-2 rounded border border-white/5 space-y-2">
                          <span className="text-[8px] font-bold text-gray-400 uppercase block">⬇️ Descargar Modelo Ollama</span>
                          <div className="flex space-x-1.5">
                            <input
                              type="text"
                              placeholder="ej. qwen2.5-coder:7b"
                              id="ollama-pull-input"
                              className="flex-1 bg-[#0A0A0C] border border-white/10 rounded p-1 text-[9px] text-white outline-none focus:border-indigo-500/50 font-mono"
                            />
                            <button
                              onClick={() => {
                                const input = document.getElementById('ollama-pull-input') as HTMLInputElement;
                                if (input && input.value.trim()) {
                                  pullOllamaModel(input.value.trim());
                                  showToast(`⬇️ Descargando ${input.value.trim()}...`, 'info');
                                  input.value = '';
                                }
                              }}
                              className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-[8px] uppercase px-2 rounded cursor-pointer shrink-0"
                            >
                              Pull
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Params Settings */}
                  {llmSubTab === 'params' && (
                    <div className="space-y-3">
                      <div className="bg-black/30 border border-white/5 rounded-lg p-3 shadow-lg space-y-2">
                        <span className="text-[9px] font-bold text-indigo-400 uppercase tracking-widest block border-b border-white/5 pb-1">🌡️ Temperatura: {temperature.toFixed(1)}</span>
                        <input
                          type="range" min="0" max="1" step="0.1"
                          value={temperature}
                          onChange={(e) => setTemperature(parseFloat(e.target.value))}
                          className="w-full accent-indigo-500 cursor-pointer"
                        />
                        <div className="flex justify-between text-[6px] text-gray-600">
                          <span>Preciso (0.0)</span>
                          <span>Balanceado (0.5)</span>
                          <span>Creativo (1.0)</span>
                        </div>
                      </div>

                      <div className="bg-black/30 border border-white/5 rounded-lg p-3 shadow-lg space-y-2">
                        <span className="text-[9px] font-bold text-indigo-400 uppercase tracking-widest block border-b border-white/5 pb-1">🪟 Contexto: {contextWindow}</span>
                        <div className="grid grid-cols-2 gap-1.5">
                          {['4096', '8192', '16384', '32768'].map(v => (
                            <button
                              key={v}
                              onClick={() => setContextWindow(v)}
                              className={`p-1 border rounded text-[9px] font-mono cursor-pointer ${contextWindow === v ? 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30' : 'bg-white/3 text-gray-400 border-white/5 hover:border-white/15'}`}
                            >
                              {v}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Smart routing */}
                      <div className="bg-black/30 border border-white/5 rounded-lg p-3 shadow-lg space-y-2">
                        <span className="text-[9px] font-bold text-indigo-400 uppercase block border-b border-white/5 pb-1">🔌 Enrutamiento Inteligente</span>
                        <div className="flex items-center space-x-2">
                          <input
                            type="checkbox"
                            id="smart-routing-chk"
                            checked={smartRouting}
                            onChange={(e) => {
                              const val = e.target.checked;
                              setSmartRouting(val);
                              saveSettingsConfig({ smart_routing: val });
                              showToast(val ? '🔌 Enrutamiento inteligente activado.' : '🔌 Enrutamiento inteligente desactivado.', 'info');
                            }}
                            className="accent-indigo-500 cursor-pointer"
                          />
                          <label htmlFor="smart-routing-chk" className="text-[9px] text-gray-300 font-sans cursor-pointer">
                            Enrutamiento Inteligente Multi-Modelo
                          </label>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* System Settings */}
                  {llmSubTab === 'system' && (
                    <div className="space-y-3">
                      <div className="bg-black/30 border border-white/5 rounded-lg p-3 shadow-lg space-y-2">
                        <span className="text-[9px] font-bold text-indigo-400 block border-b border-white/5 pb-1">🧠 System Prompt Global</span>
                        <textarea
                          value={systemPrompt}
                          onChange={(e) => setSystemPrompt(e.target.value)}
                          rows={6}
                          placeholder="Instrucciones del sistema..."
                          className="w-full bg-[#0A0A0C] border border-white/10 rounded p-2 text-white font-mono text-[9px] outline-none focus:border-indigo-500/50 resize-none leading-relaxed"
                        />
                        <button
                          onClick={() => { saveSettingsConfig({ default_model: selectedModel, temperature, system_prompt: systemPrompt, context_window: parseInt(contextWindow) }); showToast('🧠 System Prompt guardado.', 'success'); }}
                          className="w-full bg-indigo-600/80 hover:bg-indigo-600 text-white font-bold text-[8px] uppercase py-1.5 rounded cursor-pointer"
                        >
                          Guardar System Prompt
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Vault Settings */}
                  {llmSubTab === 'vault' && (
                    <div className="bg-black/30 border border-white/5 rounded-lg p-3 shadow-lg space-y-2">
                      <span className="text-[9px] font-bold text-fuchsia-400 block border-b border-white/5 pb-1">💾 Bóveda de Prompts</span>
                      <div className="flex space-x-1">
                        <input
                          type="text"
                          placeholder="Añadir prompt..."
                          id="new-vault-prompt-input"
                          className="flex-1 bg-[#0A0A0C] border border-white/10 rounded p-1 text-[9px] text-white outline-none focus:border-fuchsia-500/50 font-mono"
                        />
                        <button
                          onClick={() => {
                            const input = document.getElementById('new-vault-prompt-input') as HTMLInputElement;
                            if (input && input.value.trim()) {
                              fetch(API_BASE + '/api/llm/vault', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ prompt: input.value.trim() })
                              }).then(r => r.json()).then(d => {
                                if (d.success) { fetchTelemetry(); input.value = ''; showToast('💾 Prompt añadido.', 'success'); }
                              });
                            }
                          }}
                          className="bg-fuchsia-600/80 hover:bg-fuchsia-500 text-white font-bold text-[8px] px-2 rounded cursor-pointer shrink-0"
                        >
                          + Add
                        </button>
                      </div>

                      <div className="space-y-1.5 max-h-[140px] overflow-y-auto pr-0.5 pt-1">
                        {vaultPrompts.map((p, idx) => (
                          <div key={idx} className="bg-black/40 border border-white/5 rounded p-1.5 text-[8px] space-y-1 text-gray-300 font-sans">
                            <p className="line-clamp-2">{p}</p>
                            <div className="flex justify-end space-x-1.5 text-[7px] font-mono">
                              <button onClick={() => { setPromptInput(p); setActiveRightTab('prompt'); showToast('⚡ Cargado.', 'success'); }} className="text-fuchsia-400 hover:underline">Cargar</button>
                              <button onClick={() => deleteVaultPrompt(p)} className="text-rose-400 hover:underline">Borrar</button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Tab: UI/UX Audit */}
              {activeRightTab === 'ux' && (
                <div className="space-y-4">
                  <div className="bg-black/30 border border-white/5 rounded-lg p-3.5 shadow-lg space-y-2">
                    <span className="text-[10px] font-bold text-fuchsia-400 uppercase tracking-widest block border-b border-white/5 pb-1">🎨 Auditoría y Mejoras Visuales</span>
                    <p className="text-[8px] text-gray-400 font-sans leading-relaxed">
                      Analiza semánticamente index.html y styles.css en busca de inconsistencias estéticas, problemas de contraste o responsividad.
                    </p>
                    <div className="grid grid-cols-2 gap-2">
                      <button
                        onClick={runUxAudit}
                        className="bg-indigo-600/20 hover:bg-indigo-600/35 border border-indigo-500/30 text-indigo-300 font-bold text-[9px] py-1.5 rounded transition-all cursor-pointer text-center"
                      >
                        🔍 Auditar
                      </button>
                      <button
                        onClick={runUxFix}
                        className="bg-emerald-600 hover:bg-emerald-500 text-black font-bold text-[9px] py-1.5 rounded transition-all cursor-pointer text-center"
                      >
                        ✨ Reparar
                      </button>
                    </div>
                  </div>

                  {/* Design Identity Memory */}
                  <div className="bg-black/30 border border-white/5 rounded-lg p-3.5 shadow-lg space-y-3">
                    <span className="text-[10px] font-bold text-fuchsia-400 uppercase tracking-widest block border-b border-white/5 pb-1">💾 Identidad Visual</span>
                    
                    <div className="space-y-2 text-[9px]">
                      <div>
                        <label className="text-[7px] text-gray-500 block mb-0.5 uppercase">Preset de Estilo</label>
                        <select
                          value={designIdentity?.preset || 'dark_glass'}
                          onChange={(e) => setDesignIdentity((prev: any) => ({ ...prev, preset: e.target.value }))}
                          className="w-full bg-[#0A0A0C] border border-white/10 text-[9px] p-1 rounded outline-none text-indigo-300"
                        >
                          <option value="glassmorphism">Glassmorphism</option>
                          <option value="neo_brutalism">Neo-Brutalism</option>
                          <option value="sleek_dark">Sleek Dark Mode</option>
                          <option value="clean_light">Minimalist Light Mode</option>
                        </select>
                      </div>

                      <div>
                        <label className="text-[7px] text-gray-500 block mb-0.5 uppercase">Colores Primarios</label>
                        <input
                          type="text"
                          value={designIdentity?.colors || ''}
                          onChange={(e) => setDesignIdentity((prev: any) => ({ ...prev, colors: e.target.value }))}
                          placeholder="#ff0055, #00ffcc"
                          className="w-full bg-[#0A0A0C] border border-white/10 text-[9px] p-1 rounded outline-none text-indigo-300"
                        />
                      </div>

                      <div>
                        <label className="text-[7px] text-gray-500 block mb-0.5 uppercase">Tipografía</label>
                        <input
                          type="text"
                          value={designIdentity?.fonts || ''}
                          onChange={(e) => setDesignIdentity((prev: any) => ({ ...prev, fonts: e.target.value }))}
                          placeholder="Inter, Outfit"
                          className="w-full bg-[#0A0A0C] border border-white/10 text-[9px] p-1 rounded outline-none text-indigo-300"
                        />
                      </div>

                      <div>
                        <label className="text-[7px] text-gray-500 block mb-0.5 uppercase">Bordes y Sombras</label>
                        <input
                          type="text"
                          value={designIdentity?.style || ''}
                          onChange={(e) => setDesignIdentity((prev: any) => ({ ...prev, style: e.target.value }))}
                          placeholder="border-radius: 8px;"
                          className="w-full bg-[#0A0A0C] border border-white/10 text-[9px] p-1 rounded outline-none text-indigo-300"
                        />
                      </div>

                      <div className="flex space-x-2 pt-1">
                        <button
                          onClick={extractUxStyle}
                          className="flex-1 text-[7px] bg-white/5 hover:bg-white/10 border border-white/10 rounded py-1.5 transition-all cursor-pointer font-bold text-gray-300"
                        >
                          📥 Extraer del CSS
                        </button>
                        <button
                          onClick={() => {
                            saveSettingsConfig({ design_identity: designIdentity });
                            showToast("💾 Identidad visual guardada", "success");
                          }}
                          className="flex-1 text-[7px] bg-amber-500 hover:bg-amber-600 text-black rounded py-1.5 transition-all cursor-pointer font-bold"
                        >
                          💾 Guardar
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Visual Report */}
                  {currentFiles["VISUAL_REPORT.md"] && (
                    <div className="bg-black/30 border border-white/5 rounded-lg p-3 shadow-lg space-y-1.5">
                      <span className="text-[9px] font-bold text-amber-400 block border-b border-white/5 pb-1">📄 Último Reporte Visual</span>
                      <div className="bg-black/50 border border-white/5 rounded p-2 text-[8px] font-sans leading-relaxed text-gray-300 max-h-44 overflow-y-auto select-text prose prose-invert">
                        <div dangerouslySetInnerHTML={{ __html: parseMarkdown(currentFiles["VISUAL_REPORT.md"]) }} />
                      </div>
                    </div>
                  )}
                </div>
              )}

            </div>
          </section>
        )}

      </main>

      {/* 🛡️ Critical File Interceptor Approval Modal */}
      {pendingWrites && pendingWrites.length > 0 && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-[60] p-4 animate-in fade-in zoom-in-95 duration-200">
          <div className="bg-[#0B0B10] border border-amber-500/30 rounded-xl max-w-lg w-full shadow-2xl overflow-hidden">
            <div className="bg-amber-500/10 border-b border-amber-500/20 px-5 py-3 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <ShieldAlert size={16} className="text-amber-400" />
                <span className="text-[11px] font-bold text-amber-400 uppercase tracking-widest font-mono">
                  🚨 Interceptor de Archivos Críticos
                </span>
              </div>
              <span className="text-[9px] bg-amber-500/20 text-amber-300 border border-amber-500/30 px-2 py-0.5 rounded font-bold font-mono">
                {pendingWrites.length} PENDIENTE{pendingWrites.length > 1 ? 'S' : ''}
              </span>
            </div>

            <div className="p-5 space-y-4">
              <p className="text-[10px] text-gray-400 font-sans leading-relaxed">
                El enjambre solicita modificar archivos críticos del sistema. Revisa los cambios y aprueba o deniega cada escritura.
              </p>

              <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
                {pendingWrites.map((pw: any, idx: number) => (
                  <div key={idx} className="bg-black/40 border border-white/10 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between bg-amber-950/20 px-3 py-2 border-b border-white/5">
                      <div className="flex items-center space-x-2 min-w-0">
                        <Lock size={10} className="text-amber-400 shrink-0" />
                        <span className="text-[10px] font-bold text-amber-300 font-mono truncate">{pw.file}</span>
                      </div>
                      <span className={`text-[8px] font-bold px-1.5 py-0.5 rounded font-mono ${
                        pw.status === 'PENDING'
                          ? 'bg-amber-500/20 text-amber-400'
                          : pw.status === 'APPROVED'
                            ? 'bg-emerald-500/20 text-emerald-400'
                            : 'bg-rose-500/20 text-rose-400'
                      }`}>
                        {pw.status || 'PENDING'}
                      </span>
                    </div>

                    {pw.diff && (
                      <div className="p-3">
                        <div className="text-[8px] text-gray-500 uppercase font-bold mb-1.5 font-mono">Cambios Propuestos:</div>
                        <div className="bg-black/50 rounded p-2 max-h-28 overflow-y-auto">
                          <pre className="text-[9px] font-mono text-gray-300 whitespace-pre-wrap leading-relaxed select-text">{pw.diff}</pre>
                        </div>
                      </div>
                    )}
                    {!pw.diff && pw.content && (
                      <div className="p-3">
                        <div className="text-[8px] text-gray-500 uppercase font-bold mb-1.5 font-mono">Contenido a Escribir:</div>
                        <div className="bg-black/50 rounded p-2 max-h-24 overflow-y-auto">
                          <pre className="text-[9px] font-mono text-emerald-400/80 whitespace-pre-wrap leading-relaxed select-text">{typeof pw.content === 'string' ? pw.content.slice(0, 400) : JSON.stringify(pw.content, null, 2).slice(0, 400)}{(pw.content?.length || 0) > 400 ? '\n... (truncado)' : ''}</pre>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="px-5 py-4 border-t border-white/10 flex space-x-3">
              <button
                onClick={() => {
                  const files = pendingWrites.map((pw: any) => pw.file);
                  resolvePendingWrites('reject', files);
                }}
                className="flex-1 bg-rose-500/10 hover:bg-rose-500/25 text-rose-400 border border-rose-500/30 font-bold text-[10px] uppercase py-2.5 rounded transition-all cursor-pointer flex items-center justify-center space-x-1.5 font-mono"
              >
                <span>✕</span>
                <span>Denegar Todo</span>
              </button>
              <button
                onClick={() => {
                  const files = pendingWrites.map((pw: any) => pw.file);
                  resolvePendingWrites('confirm', files);
                }}
                className="flex-1 bg-emerald-500/10 hover:bg-emerald-500/25 text-emerald-400 border border-emerald-500/30 font-bold text-[10px] uppercase py-2.5 rounded transition-all cursor-pointer flex items-center justify-center space-x-1.5 font-mono"
              >
                <CheckCircle size={12} />
                <span>Aprobar Todo</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 🏗️ Spec-Driven Workflow Approval Modal */}
      {pipelineStatus === 'waiting_spec_approval' && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-md flex items-center justify-center z-[60] p-6 animate-in fade-in zoom-in-95 duration-200">
          <div className="bg-[#0B0B10] border border-indigo-500/30 rounded-xl max-w-4xl w-full h-[85vh] shadow-2xl flex flex-col overflow-hidden">
            <div className="bg-indigo-500/10 border-b border-indigo-500/20 px-6 py-4 flex items-center justify-between shrink-0">
              <div className="flex items-center space-x-2">
                <span className="text-lg">🏗️</span>
                <span className="text-xs font-bold text-indigo-400 uppercase tracking-widest font-mono">
                  Flujo Basado en Especificaciones (Fase 1: Especificación Generada)
                </span>
              </div>
              <span className="text-[9px] bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 px-2 py-0.5 rounded font-bold font-mono">
                PAUSADO - ESPERANDO APROBACIÓN
              </span>
            </div>

            <div className="flex-1 flex min-h-0 divide-x divide-white/5">
              <div className="w-2/5 p-4 flex flex-col gap-3 h-full bg-black/20 overflow-y-auto">
                {(() => {
                  const raw = currentFiles["SPEC.md"] || currentFiles["ARCHITECTURE.md"] || '';
                  let parsed: Record<string, any> | null = null;
                  try {
                    const jsonMatch = raw.match(/```json([\s\S]*?)```/) || raw.match(/({[\s\S]+})/);
                    if (jsonMatch) parsed = JSON.parse(jsonMatch[1].trim());
                  } catch {}
                  
                  // Extract user-friendly fields
                  const objGeneral = parsed?.objetivo_general || parsed?.descripcion;
                  const vistas = parsed?.vistas_y_diseño_de_la_ui?.vistas || parsed?.vistas_y_diseño_frontend?.vistas || parsed?.vistas || [];
                  const dbSQLite = parsed?.base_de_datos_sqlite_requerida || parsed?.base_datos_sqlite || {};
                  const tablas = dbSQLite.tablas || (parsed?.base_de_datos ? Object.keys(parsed.base_de_datos.tables || {}) : []);
                  const etapas: any[] = parsed?.etapas ? Object.values(parsed.etapas) : [];
                  const validaciones = parsed?.reglas_de_negocio_y_flujos_de_validación?.validaciones || parsed?.reglas_de_negocio_y_flujos_validacion?.validaciones || [];

                  const hasParsed = !!objGeneral || vistas.length > 0 || etapas.length > 0;
                  
                  return (
                    <div className="rounded-lg border border-indigo-500/20 bg-indigo-950/30 p-4 space-y-4 shrink-0 font-sans">
                      <div className="flex items-center gap-2 border-b border-indigo-500/10 pb-2">
                        <span className="text-xl">🗺️</span>
                        <span className="text-xs font-bold text-indigo-300 uppercase tracking-wider font-mono">Plan de tu Aplicación</span>
                      </div>
                      
                      {!hasParsed ? (
                        <p className="text-[10px] text-gray-400 italic">El plano de la aplicación se está cargando...</p>
                      ) : (
                        <div className="space-y-3.5 text-xs text-gray-300">
                          {/* Objetivo General */}
                          {objGeneral && (
                            <div className="space-y-1">
                              <span className="text-[9px] uppercase tracking-wider text-indigo-400 font-mono font-bold block">Objetivo</span>
                              <p className="text-[10px] leading-relaxed text-gray-200">{objGeneral}</p>
                            </div>
                          )}

                          {/* Pantallas diseñadas */}
                          {vistas.length > 0 && (
                            <div className="space-y-1">
                              <span className="text-[9px] uppercase tracking-wider text-indigo-400 font-mono font-bold block">Pantallas de la App</span>
                              <div className="flex flex-wrap gap-1.5 pt-0.5">
                                {vistas.map((v: string, i: number) => (
                                  <span key={i} className="bg-amber-500/10 border border-amber-500/25 text-amber-300 text-[9px] px-2 py-0.5 rounded-full font-bold">
                                    📺 {v}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Datos a Registrar */}
                          {tablas.length > 0 && (
                            <div className="space-y-1">
                              <span className="text-[9px] uppercase tracking-wider text-indigo-400 font-mono font-bold block">Información a Guardar</span>
                              <p className="text-[10px] text-gray-300 leading-normal">
                                Guardaremos información de: <b className="text-white">{tablas.join(', ')}</b>.
                              </p>
                            </div>
                          )}

                          {/* Reglas de Control */}
                          {validaciones.length > 0 && (
                            <div className="space-y-1">
                              <span className="text-[9px] uppercase tracking-wider text-indigo-400 font-mono font-bold block">Reglas de Control</span>
                              <ul className="list-disc pl-4 space-y-0.5 text-[10px] text-gray-400">
                                {validaciones.slice(0, 4).map((val: string, i: number) => (
                                  <li key={i}>{val}</li>
                                ))}
                              </ul>
                            </div>
                          )}

                          {/* Fases del desarrollo */}
                          {etapas.length > 0 && (
                            <div className="space-y-1 border-t border-indigo-500/15 pt-2.5">
                              <span className="text-[9px] uppercase tracking-wider text-indigo-400 font-mono font-bold block">{etapas.length} Pasos del Enjambre</span>
                              <div className="space-y-1.5 pt-1">
                                {etapas.map((etapa: any, i: number) => (
                                  <div key={i} className="flex items-start gap-2">
                                    <span className="shrink-0 w-4.5 h-4.5 rounded-full bg-indigo-500/20 border border-indigo-500/30 text-indigo-300 text-[8px] font-bold font-mono flex items-center justify-center mt-0.5">{i + 1}</span>
                                    <span className="text-[10px] text-gray-300 leading-tight">{etapa.descripcion || etapa.description || `Fase ${i + 1}`}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })()}

                <div className="space-y-2">
                  <h3 className="text-[10px] font-mono font-bold text-indigo-300 uppercase tracking-wider">🧠 ¿Quieres cambiar algo?</h3>
                  <p className="text-[9px] text-gray-400 leading-relaxed font-sans">
                    Escríbelo en tus palabras y el Arquitecto adaptará los planos antes de empezar a construir.
                  </p>
                  <textarea
                    value={specFeedback}
                    onChange={(e) => setSpecFeedback(e.target.value)}
                    rows={4}
                    placeholder="Ej: Agrega una pantalla para ver el stock de productos..."
                    className="w-full bg-[#0A0A0C] border border-white/10 rounded-lg p-3 text-xs text-gray-300 focus:outline-none focus:border-indigo-500 resize-none font-sans leading-relaxed"
                  />
                </div>

                <button
                  onClick={async () => {
                    if (!specFeedback.trim()) return;
                    setIsRefiningSpec(true);
                    await adjustSpec(specFeedback);
                    setSpecFeedback('');
                    setIsRefiningSpec(false);
                  }}
                  disabled={isRefiningSpec || !specFeedback.trim()}
                  className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-bold text-[10px] uppercase tracking-widest py-2.5 rounded transition-all font-mono shrink-0"
                >
                  {isRefiningSpec ? 'Refinando Plan...' : '💬 Enviar Feedback al Arquitecto'}
                </button>
              </div>

              <div className="w-3/5 p-6 flex flex-col h-full bg-black/40">
                <h3 className="text-xs font-mono font-bold text-indigo-300 uppercase tracking-wider mb-3 shrink-0 flex items-center justify-between">
                  <span>📄 Vista Previa de los Planos</span>
                  <button
                    onClick={() => setShowTechnicalSpec(!showTechnicalSpec)}
                    className="text-[8px] bg-indigo-500/20 hover:bg-indigo-500/35 border border-indigo-500/30 text-indigo-300 px-2 py-0.5 rounded transition-all cursor-pointer font-bold font-mono"
                    title="Alternar entre vista simple para usuarios y especificación JSON técnica"
                  >
                    {showTechnicalSpec ? 'Ocultar Datos Técnicos' : 'Ver Datos Técnicos (JSON)'}
                  </button>
                </h3>
                
                <div className="flex-1 overflow-y-auto bg-black/60 rounded-lg border border-white/5 p-5 prose prose-invert font-sans select-text">
                  <div 
                    dangerouslySetInnerHTML={{ 
                      __html: parseMarkdown(currentFiles["SPEC.md"] || currentFiles["ARCHITECTURE.md"] || "# Cargando planos del Arquitecto...", !showTechnicalSpec) 
                    }} 
                  />
                </div>
              </div>
            </div>

            <div className="bg-black/60 border-t border-white/5 px-6 py-4 flex items-center justify-between shrink-0 font-mono">
              <button
                onClick={async () => {
                  if (confirm("¿Estás seguro de que deseas cancelar el pipeline de agentes?")) {
                    saveSettingsConfig({ pipeline_status: 'idle' });
                    window.location.reload();
                  }
                }}
                className="bg-rose-500/10 hover:bg-rose-500/25 border border-rose-500/30 text-rose-400 font-bold text-[10px] uppercase tracking-widest py-2.5 px-4 rounded transition-all"
              >
                ❌ Cancelar Pipeline
              </button>

              <button
                onClick={async () => {
                  await approveSpec();
                }}
                className="bg-emerald-500 hover:bg-emerald-400 text-black font-bold text-[10px] uppercase tracking-widest py-3 px-6 rounded transition-all shadow-[0_0_15px_rgba(16,185,129,0.2)]"
              >
                🚀 Aprobar y Construir (Iniciar Fase 2)
              </button>
            </div>
          </div>
        </div>
      )}
      {/* 🟢 Custom Prompt Dialog Modal */}
      {promptDialog.isOpen && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center z-[100] p-4 animate-in fade-in duration-200">
          <div className="bg-[#0A0A0F] border border-white/10 rounded-lg max-w-sm w-full shadow-2xl p-4 space-y-4">
            <div className="text-[10px] font-bold text-amber-500 uppercase tracking-widest font-mono">
              {promptDialog.title}
            </div>
            <input 
              type="text"
              value={promptInputText}
              onChange={(e) => setPromptInputText(e.target.value)}
              placeholder={promptDialog.placeholder}
              className="w-full bg-black border border-white/10 rounded p-2 text-xs text-white font-mono outline-none focus:border-amber-500/50"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  promptDialog.onSubmit(promptInputText);
                  setPromptDialog(prev => ({ ...prev, isOpen: false }));
                }
              }}
            />
            <div className="flex space-x-2 justify-end text-[9px] uppercase font-bold font-mono">
              <button 
                onClick={() => setPromptDialog(prev => ({ ...prev, isOpen: false }))}
                className="bg-white/5 hover:bg-white/10 text-white px-3 py-1.5 rounded transition-all cursor-pointer"
              >
                Cancelar
              </button>
              <button 
                onClick={() => {
                  promptDialog.onSubmit(promptInputText);
                  setPromptDialog(prev => ({ ...prev, isOpen: false }));
                }}
                className="bg-amber-500 hover:bg-amber-400 text-black px-3.5 py-1.5 rounded transition-all cursor-pointer"
              >
                Aceptar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 🔴 Custom Confirm Dialog Modal */}
      {confirmDialog.isOpen && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm flex items-center justify-center z-[100] p-4 animate-in fade-in duration-200">
          <div className="bg-[#0A0A0F] border border-white/10 rounded-lg max-w-sm w-full shadow-2xl p-4 space-y-4">
            <div className="text-[10px] font-bold text-rose-500 uppercase tracking-widest font-mono">
              {confirmDialog.title}
            </div>
            <p className="text-[10px] text-gray-300 font-mono leading-relaxed">
              {confirmDialog.message}
            </p>
            <div className="flex space-x-2 justify-end text-[9px] uppercase font-bold font-mono">
              <button 
                onClick={() => setConfirmDialog(prev => ({ ...prev, isOpen: false }))}
                className="bg-white/5 hover:bg-white/10 text-white px-3 py-1.5 rounded transition-all cursor-pointer"
              >
                Cancelar
              </button>
              <button 
                onClick={() => {
                  confirmDialog.onConfirm();
                  setConfirmDialog(prev => ({ ...prev, isOpen: false }));
                }}
                className="bg-rose-500 hover:bg-rose-400 text-white px-3.5 py-1.5 rounded transition-all cursor-pointer"
              >
                Confirmar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function App() {
  return (
    <AppContextProvider>
      <MainLayout />
    </AppContextProvider>
  );
}
