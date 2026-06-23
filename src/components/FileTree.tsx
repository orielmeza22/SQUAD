import React from 'react';
import { useApp } from '../context/AppContext';
import { 
  Folder, FolderOpen, File, FileCode, ChevronRight, ChevronDown, 
  Search, Trash2, FolderPlus, FilePlus, ExternalLink 
} from 'lucide-react';

interface TreeNode {
  name: string;
  path: string;
  type: 'file' | 'folder';
  children: Record<string, TreeNode>;
}

export default function FileTree() {
  const {
    currentFiles,
    openTabs,
    setOpenTabs,
    activeTab,
    setActiveTab,
    expandedFolders,
    setExpandedFolders,
    fileSearchQuery,
    setFileSearchQuery,
    globalSearchQuery,
    setGlobalSearchQuery,
    openCustomPrompt,
    openCustomConfirm,
    fetchFiles,
    showToast,
    tc
  } = useApp();

  const API_BASE = window.location.port === '3000' ? 'http://localhost:8000' : '';

  const getFileIcon = (filename: string) => {
    const ext = filename.split('.').pop() || '';
    switch (ext) {
      case 'py': return <FileCode size={13} className="text-amber-500 mr-2 shrink-0" />;
      case 'js':
      case 'jsx':
      case 'ts':
      case 'tsx': return <FileCode size={13} className="text-cyan-400 mr-2 shrink-0" />;
      case 'json': return <FileCode size={13} className="text-yellow-400 mr-2 shrink-0" />;
      case 'html': return <FileCode size={13} className="text-orange-500 mr-2 shrink-0" />;
      case 'css': return <FileCode size={13} className="text-teal-400 mr-2 shrink-0" />;
      case 'md': return <File size={13} className="text-indigo-400 mr-2 shrink-0" />;
      default: return <File size={13} className="text-gray-400 mr-2 shrink-0" />;
    }
  };

  const selectTab = (path: string) => {
    if (!openTabs.includes(path)) {
      setOpenTabs(prev => [...prev, path]);
    }
    setActiveTab(path);
  };

  const openWorkspaceInExplorer = () => {
    fetch(API_BASE + '/api/fs/open-explorer', { method: 'POST' })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          showToast("Explorador abierto en el Workspace", "success");
        } else {
          showToast("Error abriendo explorador: " + d.message, "error");
        }
      })
      .catch(e => showToast("Error de red: " + e, "error"));
  };

  const handleCreateFile = () => {
    openCustomPrompt(
      "Crear Nuevo Archivo",
      "Introduce el nombre (ej: app/server.js)",
      "",
      (name) => {
        if (!name.trim()) return;
        fetch(API_BASE + '/api/fs/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path: name, is_dir: false })
        })
          .then(r => r.json())
          .then(d => {
            if (d.success) {
              showToast(`Archivo creado: ${name}`, "success");
              fetchFiles();
              selectTab(name);
            } else {
              showToast("Error al crear archivo: " + d.message, "error");
            }
          })
          .catch(e => showToast("Error de red: " + e, "error"));
      }
    );
  };

  const handleCreateFolder = () => {
    openCustomPrompt(
      "Crear Nueva Carpeta",
      "Introduce el nombre (ej: app/controllers)",
      "",
      (name) => {
        if (!name.trim()) return;
        fetch(API_BASE + '/api/fs/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path: name, is_dir: true })
        })
          .then(r => r.json())
          .then(d => {
            if (d.success) {
              showToast(`Carpeta creada: ${name}`, "success");
              fetchFiles();
            } else {
              showToast("Error al crear carpeta: " + d.message, "error");
            }
          })
          .catch(e => showToast("Error de red: " + e, "error"));
      }
    );
  };
  const handleDestroyWorkspace = () => {
    openCustomConfirm(
      "Destruir Workspace",
      "⚠️ ¿ATENCIÓN? Esto borrará TODO el contenido del workspace local de forma física y permanente. No podrás recuperarlo. ¿Deseas continuar?",
      () => {
        fetch(API_BASE + '/api/infra/destroy', { method: 'POST' })
          .then(r => r.json())
          .then(d => {
            if (d.success) {
              showToast("Workspace destruido y limpiado", "success");
              setOpenTabs([]);
              setActiveTab(null);
              fetchFiles();
            } else {
              showToast("Error al destruir: " + d.message, "error");
            }
          })
          .catch(e => showToast("Error de red: " + e, "error"));
      }
    );
  };

  const handleRenameItem = (oldPath: string) => {
    openCustomPrompt(
      "Renombrar Elemento",
      "Introduce la nueva ruta del elemento",
      oldPath,
      (newName) => {
        if (!newName.trim() || newName === oldPath) return;
        fetch(API_BASE + '/api/fs/rename', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ old_path: oldPath, new_path: newName })
        })
          .then(r => r.json())
          .then(d => {
            if (d.success) {
              showToast(`Renombrado exitosamente: ${newName}`, "success");
              setOpenTabs(prev => prev.map(t => t === oldPath ? newName : t));
              if (activeTab === oldPath) setActiveTab(newName);
              fetchFiles();
            } else {
              showToast("Error al renombrar: " + d.message, "error");
            }
          })
          .catch(e => showToast("Error de red: " + e, "error"));
      }
    );
  };

  const handleDeleteItem = (path: string) => {
    openCustomConfirm(
      "Eliminar Elemento",
      `¿Estás seguro de que deseas eliminar permanentemente '${path}'? Esta acción confirmará el borrado físico y es irreversible.`,
      () => {
        fetch(API_BASE + '/api/fs/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ path })
        })
          .then(r => r.json())
          .then(d => {
            if (d.success) {
              showToast(`Eliminado: ${path}`, "success");
              setOpenTabs(prev => prev.filter(t => t !== path));
              if (activeTab === path) setActiveTab(null);
              fetchFiles();
            } else {
              showToast("Error al eliminar: " + d.message, "error");
            }
          })
          .catch(e => showToast("Error de red: " + e, "error"));
      }
    );
  };

  const buildFileTree = () => {
    const root: TreeNode = { name: 'root', path: '', type: 'folder', children: {} };
    const filePaths = Object.keys(currentFiles);

    filePaths.forEach(path => {
      // Global full-text search filter
      if (globalSearchQuery.trim()) {
        const content = currentFiles[path] || '';
        if (!content.toLowerCase().includes(globalSearchQuery.toLowerCase())) {
          return;
        }
      }
      // Filename query filter
      if (fileSearchQuery.trim() && !path.toLowerCase().includes(fileSearchQuery.toLowerCase())) {
        return;
      }

      const parts = path.split('/');
      let current = root;
      parts.forEach((part, index) => {
        if (!current.children[part]) {
          const isFile = index === parts.length - 1;
          current.children[part] = {
            name: part,
            path: parts.slice(0, index + 1).join('/'),
            type: isFile ? 'file' : 'folder',
            children: {}
          };
        }
        current = current.children[part];
      });
    });
    return root;
  };

  const renderTree = (node: TreeNode, level = 0) => {
    const sortedChildren = Object.values(node.children).sort((a, b) => {
      if (a.type === 'folder' && b.type === 'file') return -1;
      if (a.type === 'file' && b.type === 'folder') return 1;
      return a.name.localeCompare(b.name);
    });

    return sortedChildren.map(child => {
      const isFolder = child.type === 'folder';
      const isExpanded = expandedFolders[child.path];
      const isActive = activeTab === child.path;

      if (isFolder) {
        return (
          <div key={child.path} className="w-full group/item">
            <div className="flex items-center justify-between hover:bg-white/5 pr-2 transition-colors">
              <button
                onClick={() => setExpandedFolders(prev => ({ ...prev, [child.path]: !prev[child.path] }))}
                style={{ paddingLeft: `${level * 6 + 6}px` }}
                className="flex-1 flex items-center py-1 text-[11px] font-mono text-gray-400 hover:text-white transition-colors text-left"
              >
                {isExpanded ? <ChevronDown size={11} className="mr-1 shrink-0" /> : <ChevronRight size={11} className="mr-1 shrink-0" />}
                {isExpanded ? <FolderOpen size={12} className="text-indigo-400 mr-1.5 shrink-0" /> : <Folder size={12} className="text-indigo-400 mr-1.5 shrink-0" />}
                <span className="truncate">{child.name}</span>
              </button>
              <div className="hidden group-hover/item:flex items-center space-x-1 shrink-0">
                <button
                  onClick={(e) => { e.stopPropagation(); handleRenameItem(child.path); }}
                  className="text-[9px] text-gray-500 hover:text-amber-400 font-bold font-mono px-0.5"
                  title="Renombrar Carpeta"
                >
                  ✎
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); handleDeleteItem(child.path); }}
                  className="text-[9px] text-gray-500 hover:text-rose-400 font-bold font-mono px-0.5"
                  title="Eliminar Carpeta"
                >
                  ✕
                </button>
              </div>
            </div>
            {isExpanded && <div className="w-full">{renderTree(child, level + 1)}</div>}
          </div>
        );
      } else {
        return (
          <div key={child.path} className="w-full group/item flex items-center justify-between hover:bg-white/5 pr-2 transition-colors">
            <button
              onClick={() => selectTab(child.path)}
              style={{ paddingLeft: `${level * 6 + 16}px` }}
              className={`flex-1 flex items-center py-1 text-[11px] font-mono text-left transition-colors truncate ${
                isActive ? 'bg-amber-500/10 border-l border-amber-500 text-amber-400' : 'text-gray-400 hover:text-white'
              }`}
            >
              {getFileIcon(child.name)}
              <span className="truncate">{child.name}</span>
            </button>
            <div className="hidden group-hover/item:flex items-center space-x-1 shrink-0">
              <button
                onClick={(e) => { e.stopPropagation(); handleRenameItem(child.path); }}
                className="text-[9px] text-gray-500 hover:text-amber-400 font-bold font-mono px-0.5"
                title="Renombrar Archivo"
              >
                ✎
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); handleDeleteItem(child.path); }}
                className="text-[9px] text-gray-500 hover:text-rose-400 font-bold font-mono px-0.5"
                title="Eliminar Archivo"
              >
                ✕
              </button>
            </div>
          </div>
        );
      }
    });
  };

  const fileTreeRoot = buildFileTree();

  return (
    <div className="flex-1 flex flex-col min-h-0">
      {/* Search Input Panels */}
      <div className="p-3.5 space-y-2 border-b border-white/5 bg-black/10">
        <div className="relative">
          <Search size={12} className="absolute left-2.5 top-2.5 text-white/30" />
          <input 
            type="text" 
            value={fileSearchQuery}
            onChange={(e) => setFileSearchQuery(e.target.value)}
            placeholder="Buscar por nombre..."
            className="w-full bg-[#0A0A0C]/50 border border-white/5 rounded pl-8 pr-2.5 py-1.5 text-[10px] text-white focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>
        <div className="relative">
          <Search size={12} className="absolute left-2.5 top-2.5 text-indigo-400/40" />
          <input 
            type="text" 
            value={globalSearchQuery}
            onChange={(e) => setGlobalSearchQuery(e.target.value)}
            placeholder="Buscar contenido (Grep)..."
            className="w-full bg-[#0A0A0C]/50 border border-white/5 rounded pl-8 pr-2.5 py-1.5 text-[10px] text-indigo-200 focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>
      </div>

      {/* Directory Tree Header Tools */}
      <div className="px-3.5 py-2 border-b border-white/5 flex items-center justify-between text-[9px] text-white/40 uppercase tracking-widest font-mono font-bold bg-black/20">
        <span>Workspace Local</span>
        <div className="flex space-x-2.5">
          <button 
            onClick={handleCreateFile}
            className="hover:text-amber-400 transition-colors cursor-pointer flex items-center"
            title="Nuevo Archivo"
          >
            <FilePlus size={12} />
          </button>
          <button 
            onClick={handleCreateFolder}
            className="hover:text-amber-400 transition-colors cursor-pointer flex items-center"
            title="Nueva Carpeta"
          >
            <FolderPlus size={12} />
          </button>
          <button 
            onClick={openWorkspaceInExplorer}
            className="hover:text-amber-400 transition-colors cursor-pointer flex items-center"
            title="Abrir Explorador Físico"
          >
            <ExternalLink size={11} />
          </button>
          <button 
            onClick={handleDestroyWorkspace}
            className="hover:text-rose-400 text-rose-500/70 transition-colors cursor-pointer flex items-center"
            title="Vaciar / Destruir Workspace"
          >
            <Trash2 size={11} />
          </button>
        </div>
      </div>

      {/* Scrolled File Tree View */}
      <div className="flex-1 overflow-y-auto py-2 pr-1 min-h-0 select-none">
        {Object.keys(fileTreeRoot.children).length > 0 ? (
          renderTree(fileTreeRoot)
        ) : (
          <div className="text-[10px] text-white/20 italic p-4 text-center">
            Ningún archivo coincide con los filtros.
          </div>
        )}
      </div>
    </div>
  );
}
