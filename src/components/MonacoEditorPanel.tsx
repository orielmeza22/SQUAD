import React from 'react';
import Editor, { DiffEditor } from '@monaco-editor/react';
import { useApp } from '../context/AppContext';
import { useGraphStore } from '../stores/graphStore';
import { Save, Eye, EyeOff, GitBranch, RefreshCw, Play } from 'lucide-react';

export default function MonacoEditorPanel() {
  const {
    currentFiles,
    setCurrentFiles,
    openTabs,
    setOpenTabs,
    activeTab,
    setActiveTab,
    saveActiveFile,
    isDiffMode,
    setIsDiffMode,
    diffOriginalContent,
    fetchFileOriginalContent,
    showPreview,
    setShowPreview,
    editorFontSize,
    setEditorFontSize,
    launchAppSystem,
    isAppLaunching,
    theme,
    tc,
    refactorCodeAction,
    setChatMessage,
    setActiveSidebarTab,
    openCustomConfirm,
    activePort,
    gitCommits,
    gitCheckout,
    gitRestoreHead
  } = useApp();

  // LangGraph HITL diff state (Zustand)
  const graphShowDiff = useGraphStore((s) => s.showDiffPanel);
  const graphDiffData = useGraphStore((s) => s.diffData);
  const graphApproveHitl = useGraphStore((s) => s.approveHitl);
  const graphSetDiffData = useGraphStore((s) => s.setDiffData);

  const [previewUrl, setPreviewUrl] = React.useState(`http://localhost:${activePort}`);
  const [selectedText, setSelectedText] = React.useState('');

  React.useEffect(() => {
    setPreviewUrl(`http://localhost:${activePort}`);
  }, [activePort]);

  const handleRefactor = (action: 'docstrings' | 'optimize' | 'typescript' | 'tests') => {
    if (activeTab) {
      refactorCodeAction(activeTab, action);
    }
  };

  const closeTab = (e: React.MouseEvent, path: string) => {
    e.stopPropagation();
    const filtered = openTabs.filter(t => t !== path);
    setOpenTabs(filtered);
    if (activeTab === path) {
      setActiveTab(filtered.length > 0 ? filtered[Math.max(0, filtered.length - 1)] : null);
    }
  };

  const getFileLanguage = (filename: string) => {
    const ext = filename.split('.').pop() || '';
    switch (ext) {
      case 'py': return 'python';
      case 'js':
      case 'jsx': return 'javascript';
      case 'ts':
      case 'tsx': return 'typescript';
      case 'json': return 'json';
      case 'html': return 'html';
      case 'css': return 'css';
      case 'md': return 'markdown';
      case 'sql': return 'sql';
      default: return 'plaintext';
    }
  };

  const parseMarkdown = (mdText: string) => {
    if (!mdText) return '';
    let html = mdText
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Headings
    html = html.replace(/^### (.*?)$/gm, '<h3 class="text-base font-bold text-amber-400 mt-4 mb-2 font-mono">$1</h3>');
    html = html.replace(/^## (.*?)$/gm, '<h2 class="text-lg font-bold text-indigo-400 mt-5 mb-3 border-b border-white/10 pb-1 font-mono">$1</h2>');
    html = html.replace(/^# (.*?)$/gm, '<h1 class="text-2xl font-bold text-white mt-6 mb-4 border-b border-indigo-500/30 pb-2 font-mono">$1</h1>');
    
    // Bold / Code tags
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="text-white">$1</strong>');
    html = html.replace(/`(.*?)`/g, '<code class="bg-[#141418] px-1.5 py-0.5 rounded text-rose-400 text-xs font-mono">$1</code>');
    
    // Lists
    html = html.replace(/^\- (.*?)$/gm, '<li class="list-disc ml-5 text-gray-300 text-xs leading-relaxed my-1">$1</li>');
    html = html.replace(/^\* (.*?)$/gm, '<li class="list-disc ml-5 text-gray-300 text-xs leading-relaxed my-1">$1</li>');

    // Paragraphs
    html = html.split('\n\n').map(p => {
      if (p.trim().startsWith('<h') || p.trim().startsWith('<li') || p.trim().startsWith('<ul')) return p;
      return `<p class="text-gray-300 text-sm leading-relaxed my-3 font-sans">${p}</p>`;
    }).join('\n');

    return html;
  };

  const handleEditorDidMount = (editorInstance: any) => {
    // Bind keyboard shortcut Ctrl + S to saveActiveFile
    editorInstance.addCommand(2048 | 49, () => {
      saveActiveFile();
    });
    // Bind keyboard shortcut Ctrl + Enter to launchAppSystem
    editorInstance.addCommand(2048 | 3, () => {
      launchAppSystem();
    });

    // Listen to selection changes
    editorInstance.onDidChangeCursorSelection((e: any) => {
      const model = editorInstance.getModel();
      if (model) {
        const text = model.getValueInRange(e.selection);
        setSelectedText(text);
      }
    });
  };

  const handleDiffEditorDidMount = (editor: any) => {
    const modifiedEditor = editor.getModifiedEditor();
    modifiedEditor.onDidChangeModelContent(() => {
      if (activeTab) {
        setCurrentFiles(prev => ({ ...prev, [activeTab]: modifiedEditor.getValue() }));
      }
    });
  };

  if (!activeTab) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center text-white/20 select-none">
        <span className="text-3xl mb-3">📂</span>
        <span className="text-xs uppercase tracking-widest">No hay archivos abiertos en el editor</span>
        <span className="text-[10px] text-white/10 mt-1.5 font-mono">Selecciona un archivo del árbol a la izquierda</span>
      </div>
    );
  }

  // Check if we are viewing a special ER diagram tab or similar
  const isSpecialTab = activeTab.startsWith('SCHEMA_SQLITE_') || activeTab === 'SCHEMA_POSTGRES';
  const showMdPreview = showPreview && activeTab.endsWith('.md');
  const currentContent = currentFiles[activeTab] || '';

  return (
    <div className="flex-1 flex flex-col min-h-0 bg-[#0B0B0D]">
      {/* Editor Tabs Row */}
      <div className="h-10 bg-black/40 border-b border-white/5 flex items-center justify-between px-3.5 shrink-0 select-none">
        <div className="flex items-center space-x-1.5 overflow-x-auto min-w-0 pr-4">
          {openTabs.map(tab => {
            const isActive = activeTab === tab;
            const isTabSpecial = tab.startsWith('SCHEMA_SQLITE_') || tab === 'SCHEMA_POSTGRES';
            const displayTitle = isTabSpecial 
              ? `📊 ER: ${tab.replace('SCHEMA_SQLITE_', '')}` 
              : tab;

            return (
              <div 
                key={tab}
                onClick={() => {
                  setActiveTab(tab);
                  if (!isTabSpecial && isDiffMode) {
                    fetchFileOriginalContent(tab);
                  }
                }}
                className={`h-7 px-2.5 rounded-t text-[10px] font-mono flex items-center space-x-2 border-t cursor-pointer transition-all shrink-0 ${
                  isActive 
                    ? 'bg-[#0B0B0D] border-amber-500 text-amber-400 font-bold' 
                    : 'bg-black/20 border-transparent text-gray-500 hover:text-white'
                }`}
              >
                <span className="truncate max-w-[120px]">{displayTitle}</span>
                <button 
                  onClick={(e) => closeTab(e, tab)}
                  className="text-gray-600 hover:text-rose-400 font-bold text-[8px]"
                  title="Cerrar pestaña"
                >
                  ✕
                </button>
              </div>
            );
          })}
        </div>

        {/* Editor Controls Toolbar */}
        {!isSpecialTab && (
          <div className="flex items-center space-x-3 shrink-0">
            {/* Font Size controls */}
            <div className="flex items-center space-x-1.5 border-r border-white/10 pr-3">
              <span className="text-[9px] text-white/30 uppercase tracking-widest font-mono">Font:</span>
              <button 
                onClick={() => setEditorFontSize(Math.max(10, editorFontSize - 1))}
                className="text-[10px] hover:text-white text-gray-400 font-bold font-mono w-4 text-center cursor-pointer"
                title="Reducir fuente"
              >
                -
              </button>
              <span className="text-[10px] text-indigo-400 font-bold font-mono">{editorFontSize}</span>
              <button 
                onClick={() => setEditorFontSize(Math.min(24, editorFontSize + 1))}
                className="text-[10px] hover:text-white text-gray-400 font-bold font-mono w-4 text-center cursor-pointer"
                title="Aumentar fuente"
              >
                +
              </button>
            </div>

            {/* Git Timetravel Dropdown */}
            {gitCommits && gitCommits.length > 0 && (
              <div className="flex items-center space-x-1.5 border-r border-white/10 pr-3">
                <span className="text-[9px] text-white/30 uppercase tracking-widest font-mono">Git Time:</span>
                <select
                  onChange={(e) => {
                    const val = e.target.value;
                    if (val === 'head') {
                      gitRestoreHead();
                    } else {
                      gitCheckout(val);
                    }
                  }}
                  className="bg-black/50 border border-white/10 text-[9px] text-indigo-400 px-1 py-0.5 rounded outline-none cursor-pointer max-w-[125px] font-mono"
                  defaultValue="head"
                  title="Viaje en el Tiempo (Checkout temporal de Shadow Git)"
                >
                  <option value="head">🔴 Presente (HEAD)</option>
                  {gitCommits.map((c: any) => (
                    <option key={c.hash} value={c.hash}>
                      ⏱️ {c.message.slice(0, 15)}... ({c.hash.slice(0, 7)})
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Monaco Mode Diff Toggle */}
            <button 
              onClick={() => {
                const nextDiff = !isDiffMode;
                setIsDiffMode(nextDiff);
                if (nextDiff) {
                  fetchFileOriginalContent(activeTab);
                }
              }}
              className={`text-[9px] uppercase font-bold py-1 px-2.5 rounded flex items-center space-x-1 transition-all border cursor-pointer ${
                isDiffMode 
                  ? 'bg-amber-500/20 text-amber-400 border-amber-500/50' 
                  : 'bg-white/5 text-gray-400 border-white/10 hover:bg-white/10 hover:text-white'
              }`}
              title="Comparar cambios con HEAD Git"
            >
              <GitBranch size={10} />
              <span>{isDiffMode ? 'Ver Código' : 'Ver Cambios'}</span>
            </button>

            {/* Markdown preview toggle */}
            {activeTab.endsWith('.md') && (
              <button 
                onClick={() => setShowPreview(!showPreview)}
                className="bg-white/5 hover:bg-white/10 border border-white/10 p-1 rounded text-gray-400 hover:text-white transition-colors cursor-pointer"
                title={showPreview ? "Ocultar Vista Previa" : "Mostrar Vista Previa"}
              >
                {showPreview ? <EyeOff size={12} /> : <Eye size={12} />}
              </button>
            )}

            {/* Live Web Preview toggle */}
            {!activeTab.endsWith('.md') && (
              <button 
                onClick={() => setShowPreview(!showPreview)}
                className={`text-[9px] uppercase font-bold py-1 px-2 rounded flex items-center space-x-1 transition-all border cursor-pointer ${
                  showPreview 
                    ? 'bg-indigo-500/25 text-indigo-400 border-indigo-500/50' 
                    : 'bg-white/5 text-gray-400 border-white/10 hover:bg-white/10'
                }`}
                title={showPreview ? "Ocultar Previsualización de App" : "Mostrar Previsualización de App"}
              >
                <Eye size={10} className="mr-0.5" />
                <span>{showPreview ? 'Ocultar Web' : 'Previsualizar App'}</span>
              </button>
            )}

            {/* Lanzar Aplicación (Always visible button) */}
            <button 
              onClick={launchAppSystem}
              disabled={isAppLaunching}
              className="bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-black font-bold text-[9px] uppercase py-1.5 px-2.5 rounded flex items-center space-x-1 transition-all cursor-pointer font-mono"
              title="Lanzar aplicación local (Ejecutar scripts de inicio / Ctrl+Enter)"
            >
              <Play size={10} className="fill-black mr-0.5" />
              <span>{isAppLaunching ? 'Lanzando...' : 'Lanzar App'}</span>
            </button>

            {/* Save Button */}
            <button 
              onClick={saveActiveFile}
              className="bg-emerald-600 hover:bg-emerald-500 text-black font-bold p-1 rounded transition-colors flex items-center cursor-pointer"
              title="Guardar y Formatear (Ctrl+S)"
            >
              <Save size={12} />
            </button>
          </div>
        )}
      </div>{/* close Editor Tabs Row */}

      {/* IA Refactor Toolkit Banner */}
      {!isSpecialTab && !activeTab.endsWith('.md') && (
        <div className="h-8 bg-indigo-950/20 border-b border-indigo-500/10 flex items-center justify-between px-3.5 shrink-0 select-none font-mono">
          <span className="text-[9px] font-bold text-indigo-400 flex items-center space-x-1">
            <span>✨ IA Refactor:</span>
          </span>
          <div className="flex space-x-2">
            <button
              onClick={() => handleRefactor('docstrings')}
              className="text-[8px] bg-indigo-500/10 hover:bg-indigo-500/25 border border-indigo-500/20 text-indigo-300 font-bold px-2 py-0.5 rounded cursor-pointer transition-all"
              title="Generar docstrings y documentación de funciones"
            >
              📝 Docstrings
            </button>
            <button
              onClick={() => handleRefactor('typescript')}
              className="text-[8px] bg-indigo-500/10 hover:bg-indigo-500/25 border border-indigo-500/20 text-indigo-300 font-bold px-2 py-0.5 rounded cursor-pointer transition-all"
              title="Añadir tipado estricto de TypeScript o anotaciones de tipo Python"
            >
              🛡️ Tipar Tipos
            </button>
            <button
              onClick={() => handleRefactor('tests')}
              className="text-[8px] bg-indigo-500/10 hover:bg-indigo-500/25 border border-indigo-500/20 text-indigo-300 font-bold px-2 py-0.5 rounded cursor-pointer transition-all"
              title="Generar Tests Unitarios automáticos"
            >
              🧪 Crear Tests
            </button>
            <button
              onClick={() => handleRefactor('optimize')}
              className="text-[8px] bg-amber-500/10 hover:bg-amber-500/25 border border-amber-500/20 text-amber-300 font-bold px-2 py-0.5 rounded cursor-pointer transition-all"
              title="Optimizar rendimiento del código seleccionado/archivo"
            >
              ⚡ Optimizar
            </button>
          </div>
        </div>
      )}

      {/* Editor Content Area */}
      <div className="flex-1 flex min-h-0 relative">

        {/* HITL Diff Panel (LangGraph) — shown when a destructive patch needs approval */}
        {graphShowDiff && graphDiffData && (
          <div className="absolute inset-0 z-40 flex flex-col bg-[#0A0A0C]">
            <div className="flex items-center justify-between px-4 py-2.5 bg-black/60 border-b border-amber-500/30 shrink-0">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 bg-amber-400 rounded-full animate-ping"></span>
                <span className="text-[10px] font-bold text-amber-400 uppercase tracking-widest font-mono">
                  ⚠️ HITL — Revisión de parche: {graphDiffData.filename}
                </span>
              </div>
              <div className="flex space-x-2">
                <button
                  onClick={() => graphApproveHitl()}
                  className="bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-400 border border-emerald-500/40 px-3 py-1 rounded text-[9px] font-bold cursor-pointer transition-all"
                >
                  ✅ Aprobar parche
                </button>
                <button
                  onClick={() => graphSetDiffData(null)}
                  className="bg-rose-500/20 hover:bg-rose-500/30 text-rose-400 border border-rose-500/40 px-3 py-1 rounded text-[9px] font-bold cursor-pointer transition-all"
                >
                  ❌ Rechazar
                </button>
              </div>
            </div>
            <div className="flex-1 min-h-0">
              <DiffEditor
                original={graphDiffData.original}
                modified={graphDiffData.modified}
                language={getFileLanguage(graphDiffData.filename)}
                theme="vs-dark"
                options={{
                  minimap: { enabled: false },
                  wordWrap: 'on',
                  renderSideBySide: true,
                  readOnly: true,
                }}
              />
            </div>
          </div>
        )}

        {isSpecialTab ? (
          <div className="flex-1 flex items-center justify-center text-white/30 text-xs italic">
            Visualizador especial cargado. Dirígete a la barra de herramientas de infraestructura.
          </div>
        ) : (
          <div className="flex-1 flex min-h-0">
            {/* Monaco Editor Component */}
            <div className={`h-full min-h-0 flex-1 relative ${(showMdPreview || (showPreview && !activeTab.endsWith('.md'))) ? 'w-1/2 border-r border-white/5' : 'w-full'}`}>
              {isDiffMode ? (
                <DiffEditor
                  original={diffOriginalContent}
                  modified={currentContent}
                  language={getFileLanguage(activeTab)}
                  theme={theme === 'light' ? 'light' : 'vs-dark'}
                  onMount={handleDiffEditorDidMount}
                  options={{
                    fontSize: editorFontSize,
                    minimap: { enabled: false },
                    wordWrap: 'on',
                    renderSideBySide: true,
                    readOnly: false
                  }}
                />
              ) : (
                <Editor
                  value={currentContent}
                  onChange={(val) => {
                    if (val !== undefined) {
                      setCurrentFiles(prev => ({ ...prev, [activeTab]: val }));
                    }
                  }}
                  language={getFileLanguage(activeTab)}
                  theme={theme === 'light' ? 'light' : 'vs-dark'}
                  onMount={handleEditorDidMount}
                  options={{
                    fontSize: editorFontSize,
                    minimap: { enabled: false },
                    wordWrap: 'on',
                    lineNumbers: 'on',
                    scrollbar: { vertical: 'visible', horizontal: 'visible' }
                  }}
                />
              )}

              {/* Code Lens selection badge */}
              {selectedText.trim() && (
                <div className="absolute bottom-4 right-4 bg-[#0a0a0f]/95 backdrop-blur-md border border-indigo-500/30 px-3 py-2 rounded-lg shadow-2xl flex items-center space-x-3 z-30 font-mono animate-in fade-in slide-in-from-bottom-2 duration-300 select-none">
                  <span className="text-[9px] font-bold text-indigo-400">✨ Selección ({selectedText.length} chs):</span>
                  <button
                    onClick={() => {
                      setChatMessage(`Por favor explica este fragmento de código:\n\n\`\`\`\n${selectedText}\n\`\`\``);
                      setActiveSidebarTab('chat');
                    }}
                    className="text-[8px] bg-indigo-500/25 hover:bg-indigo-500/45 text-white font-bold px-2 py-1 rounded cursor-pointer transition-colors"
                  >
                    Explicar
                  </button>
                  <button
                    onClick={() => {
                      openCustomConfirm(
                        "Optimizar Bloque con IA",
                        "¿Quieres pedirle al enjambre que optimice el bloque de código seleccionado?",
                        () => {
                          handleRefactor('optimize');
                        }
                      );
                    }}
                    className="text-[8px] bg-amber-500/25 hover:bg-amber-500/45 text-amber-300 font-bold px-2 py-1 rounded cursor-pointer transition-colors"
                  >
                    Optimizar
                  </button>
                </div>
              )}
            </div>

            {/* Live Markdown Preview Column */}
            {showMdPreview && (
              <div className="w-1/2 h-full overflow-y-auto p-6 bg-[#0E0E11] text-gray-200 select-text prose prose-invert font-sans border-l border-white/5">
                <div dangerouslySetInnerHTML={{ __html: parseMarkdown(currentContent) }} />
              </div>
            )}

            {/* Live Web Sandbox Preview Column */}
            {showPreview && !activeTab.endsWith('.md') && (
              <div className="w-1/2 h-full flex flex-col bg-[#050507] border-l border-white/5 select-none">
                {/* Control bar */}
                <div className="h-8 border-b border-white/5 bg-black/40 flex items-center justify-between px-3 shrink-0 font-mono">
                  <div className="flex items-center space-x-2 flex-1">
                    <span className="text-[8px] font-bold text-gray-500 uppercase tracking-widest">Sandbox Port:</span>
                    <input 
                      type="text" 
                      value={previewUrl} 
                      onChange={(e) => setPreviewUrl(e.target.value)}
                      className="bg-black/50 border border-white/10 text-[9px] text-indigo-400 px-2 py-0.5 rounded focus:outline-none w-full max-w-[180px]"
                    />
                  </div>
                  <button 
                    onClick={() => {
                      const iframe = document.getElementById('sandbox-iframe') as HTMLIFrameElement;
                      if (iframe) iframe.src = previewUrl;
                    }}
                    className="text-gray-400 hover:text-white text-[8px] uppercase font-bold flex items-center space-x-1 cursor-pointer"
                  >
                    <RefreshCw size={8} />
                    <span>Recargar</span>
                  </button>
                </div>
                {/* Iframe */}
                <div className="flex-1 bg-white relative">
                  <iframe 
                    id="sandbox-iframe"
                    src={previewUrl}
                    className="w-full h-full border-none bg-white"
                    title="Live App Sandbox"
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
