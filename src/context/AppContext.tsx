import React, { createContext, useContext, useState, useEffect, useRef } from 'react';

const API_BASE = window.location.port === '3000' ? 'http://localhost:8000' : '';

interface DockerContainer {
  Names: string;
  Image: string;
  Status: string;
}

interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info';
  text: string;
}

interface PromptDialog {
  isOpen: boolean;
  title: string;
  placeholder: string;
  defaultValue: string;
  onSubmit: (value: string) => void;
}

interface ConfirmDialog {
  isOpen: boolean;
  title: string;
  message: string;
  onConfirm: () => void;
}

interface AppContextType {
  // Theme & Navigation
  theme: 'dark' | 'cyberpunk' | 'light' | 'matrix' | 'glass';
  setTheme: (t: 'dark' | 'cyberpunk' | 'light' | 'matrix' | 'glass') => void;
  activeSidebarTab: 'build' | 'chat' | 'infra' | 'llm' | 'deploy' | 'modules';
  setActiveSidebarTab: (tab: 'build' | 'chat' | 'infra' | 'llm' | 'deploy' | 'modules') => void;
  
  // Toasts
  toasts: ToastMessage[];
  showToast: (text: string, type?: 'success' | 'error' | 'info') => void;
  
  // Custom Dialogs
  promptDialog: PromptDialog;
  setPromptDialog: React.Dispatch<React.SetStateAction<PromptDialog>>;
  promptInputText: string;
  setPromptInputText: (t: string) => void;
  openCustomPrompt: (title: string, placeholder: string, defaultValue: string, onSubmit: (val: string) => void) => void;
  confirmDialog: ConfirmDialog;
  setConfirmDialog: React.Dispatch<React.SetStateAction<ConfirmDialog>>;
  openCustomConfirm: (title: string, message: string, onConfirm: () => void) => void;
  
  // Settings & STDIN
  settings: any;
  saveSettingsConfig: (newSettings: any) => void;
  stdinInput: string;
  setStdinInput: (t: string) => void;
  stdinHistory: string[];
  setStdinHistory: React.Dispatch<React.SetStateAction<string[]>>;
  stdinHistoryIdx: number;
  setStdinHistoryIdx: (idx: number) => void;
  
  // Git History
  gitCommits: any[];
  fetchGitHistory: () => void;
  revertGitCommit: (hash: string) => void;
  
  // Templates
  isApplyingTemplate: boolean;
  applyProjectTemplate: (name: string) => void;
  
  // Postgres Explorer
  postgresTables: string[];
  selectedPostgresTable: string;
  setSelectedPostgresTable: (t: string) => void;
  postgresData: any;
  postgresError: string | null;
  fetchPostgresTables: () => void;
  fetchPostgresTableData: (table: string) => void;
  
  // SQLite Explorer
  sqliteDbs: string[];
  selectedSqliteDb: string;
  setSelectedSqliteDb: (db: string) => void;
  sqliteTables: string[];
  selectedSqliteTable: string;
  setSelectedSqliteTable: (t: string) => void;
  sqliteData: any;
  fetchSqliteDbs: () => void;
  fetchSqliteTables: (dbName: string) => void;
  fetchSqliteTableData: (dbName: string, tableName: string) => void;
  
  // Workspace Files
  currentFiles: Record<string, string>;
  setCurrentFiles: React.Dispatch<React.SetStateAction<Record<string, string>>>;
  openTabs: string[];
  setOpenTabs: React.Dispatch<React.SetStateAction<string[]>>;
  activeTab: string | null;
  setActiveTab: (t: string | null) => void;
  expandedFolders: Record<string, boolean>;
  setExpandedFolders: React.Dispatch<React.SetStateAction<Record<string, boolean>>>;
  fileSearchQuery: string;
  setFileSearchQuery: (q: string) => void;
  globalSearchQuery: string;
  setGlobalSearchQuery: (q: string) => void;
  fetchFiles: () => void;
  saveActiveFile: () => void;
  
  // LLM Configurations
  models: string[];
  selectedModel: string;
  setSelectedModel: (m: string) => void;
  promptInput: string;
  setPromptInput: (p: string) => void;
  temperature: number;
  setTemperature: (t: number) => void;
  contextWindow: string;
  setContextWindow: (w: string) => void;
  forceJson: boolean;
  setForceJson: (f: boolean) => void;
  systemPrompt: string;
  setSystemPrompt: (p: string) => void;
  
  // Pipeline & Agent Runs
  pipelineLogs: string[];
  isPipelineRunning: boolean;
  startBuildPipeline: () => void;
  
  // Terminal Launcher
  launcherLogs: string[];
  setLauncherLogs: React.Dispatch<React.SetStateAction<string[]>>;
  isAppLaunching: boolean;
  setIsAppLaunching: (l: boolean) => void;
  launchAppSystem: () => void;
  
  // Chatbot Agent
  chatMessage: string;
  setChatMessage: (m: string) => void;
  chatHistory: ChatMessage[];
  setChatHistory: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  isChatThinking: boolean;
  chatTarget: 'general' | 'architect' | 'qa' | 'devops' | 'debate';
  setChatTarget: (t: 'general' | 'architect' | 'qa' | 'devops' | 'debate') => void;
  sendChatMessage: () => void;
  
  // Physical Telemetry & Vercel
  hwTime: string;
  hwCpuTemp: string;
  hwCpuUsage: number;
  hwRamUsage: string;
  hwRamPercentage: number;
  hwDiskUsage: string;
  hwDiskPercentage: number;
  dockerContainers: DockerContainer[];
  dockerError: string | null;
  vercelUrl: string | null;
  isDeployingVercel: boolean;
  deployToVercel: () => void;
  tokenIn: number;
  tokenOut: number;
  costUsd: number;
  cacheHits: number;
  vaultPrompts: string[];
  fetchTelemetry: () => void;
  saveToVault: () => void;
  
  // Env Config & Pre-flight
  envContent: string;
  setEnvContent: (c: string) => void;
  envEditMode: 'visual' | 'raw';
  setEnvEditMode: (m: 'visual' | 'raw') => void;
  preflightStatus: Record<string, boolean>;
  installingTools: Record<string, boolean>;
  fetchPreflightStatus: () => void;
  installSystemTool: (toolName: string) => void;
  saveEnvContent: () => void;
  
  // Editor view preferences
  showPreview: boolean;
  setShowPreview: (p: boolean) => void;
  editorFontSize: number;
  setEditorFontSize: (s: number) => void;
  
  // Monaco Diff Editor
  isDiffMode: boolean;
  setIsDiffMode: (d: boolean) => void;
  diffOriginalContent: string;
  fetchFileOriginalContent: (filename: string) => void;
  
  // ER Schema Diagram
  dbSchemaData: Record<string, any> | null;
  isDbSchemaLoading: boolean;
  dbSchemaError: string | null;
  fetchDbSchemaDiagram: (dbType: 'sqlite' | 'postgres', dbName?: string) => void;
  
  // GitHub Graduation
  githubToken: string;
  setGithubToken: (t: string) => void;
  githubRepoName: string;
  setGithubRepoName: (r: string) => void;
  githubPrivate: boolean;
  setGithubPrivate: (p: boolean) => void;
  isPublishingGithub: boolean;
  publishToGithub: () => void;
  
  // DB Auto-provision
  isDbProvisioning: boolean;
  handleDbProvision: () => void;
  
  // Refs
  logsContainerRef: React.RefObject<HTMLDivElement | null>;
  terminalContainerRef: React.RefObject<HTMLDivElement | null>;
  chatHistoryRef: React.RefObject<HTMLDivElement | null>;
  
  // Theme Color Tokens Helper
  tc: any;

  // V7 Features
  pendingWrites: any[];
  fetchPendingWrites: () => void;
  resolvePendingWrites: (action: 'confirm' | 'reject', files: string[]) => void;
  listeningPorts: any[];
  fetchListeningPorts: () => void;
  killListeningPort: (pid: number) => void;
  deployToRealProvider: (provider: 'vercel' | 'netlify', token: string) => void;
  refactorCodeAction: (file: string, action: 'docstrings' | 'optimize' | 'typescript' | 'tests') => void;
  runDockerCompose: (action: 'up' | 'down' | 'build') => void;
  deleteVaultPrompt: (prompt: string) => void;
  providersList: any[];
  fetchProvidersList: () => void;
  pullOllamaModel: (model: string) => void;

  // 10 Advanced Optimization Features
  pipelineStatus: 'idle' | 'running' | 'waiting_spec_approval';
  activePort: number;
  activeDiagnostic: any;
  designIdentity: any;
  setDesignIdentity: React.Dispatch<React.SetStateAction<any>>;
  smartRouting: boolean;
  setSmartRouting: React.Dispatch<React.SetStateAction<boolean>>;
  optimizePrompt: (promptText: string) => Promise<void>;
  adjustSpec: (feedbackText: string) => Promise<void>;
  approveSpec: () => Promise<void>;
  seedDb: () => Promise<void>;
  runUxAudit: () => Promise<void>;
  runUxFix: () => Promise<void>;
  extractUxStyle: () => Promise<void>;
  gitCheckout: (hash: string) => Promise<void>;
  gitRestoreHead: () => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used within AppContextProvider');
  return context;
};

export const AppContextProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Theme & Navigation
  const [theme, setTheme] = useState<'dark' | 'cyberpunk' | 'light' | 'matrix' | 'glass'>('dark');
  const [activeSidebarTab, setActiveSidebarTab] = useState<'build' | 'chat' | 'infra' | 'llm' | 'deploy' | 'modules'>('build');
  
  // 10 Advanced Optimization Features States
  const [pipelineStatus, setPipelineStatus] = useState<'idle' | 'running' | 'waiting_spec_approval'>('idle');
  const [activePort, setActivePort] = useState<number>(5000);
  const [activeDiagnostic, setActiveDiagnostic] = useState<any>(null);
  const [designIdentity, setDesignIdentity] = useState<any>(null);
  const [smartRouting, setSmartRouting] = useState<boolean>(false);

  // Toasts
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const showToast = (text: string, type: 'success' | 'error' | 'info' = 'success') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts(prev => [...prev, { id, type, text }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 4000);
  };

  // Custom Inline Prompt & Confirm Dialogs
  const [promptDialog, setPromptDialog] = useState<PromptDialog>({
    isOpen: false, title: '', placeholder: '', defaultValue: '', onSubmit: () => {}
  });
  const [promptInputText, setPromptInputText] = useState('');
  const openCustomPrompt = (title: string, placeholder: string, defaultValue: string, onSubmit: (val: string) => void) => {
    setPromptInputText(defaultValue);
    setPromptDialog({ isOpen: true, title, placeholder, defaultValue, onSubmit });
  };

  const [confirmDialog, setConfirmDialog] = useState<ConfirmDialog>({
    isOpen: false, title: '', message: '', onConfirm: () => {}
  });
  const openCustomConfirm = (title: string, message: string, onConfirm: () => void) => {
    setConfirmDialog({ isOpen: true, title, message, onConfirm });
  };

  // Settings & STDIN
  const [settings, setSettings] = useState({
    workspace: '', ollama_host: '', default_model: '', temperature: 0.3, enable_rag: true, default_port: 5000
  });
  const [stdinInput, setStdinInput] = useState('');
  const [stdinHistory, setStdinHistory] = useState<string[]>([]);
  const [stdinHistoryIdx, setStdinHistoryIdx] = useState(-1);

  // Git History
  const [gitCommits, setGitCommits] = useState<any[]>([]);

  // Templates
  const [isApplyingTemplate, setIsApplyingTemplate] = useState(false);

  // Postgres Explorer
  const [postgresTables, setPostgresTables] = useState<string[]>([]);
  const [selectedPostgresTable, setSelectedPostgresTable] = useState('');
  const [postgresData, setPostgresData] = useState<any>(null);
  const [postgresError, setPostgresError] = useState<string | null>(null);

  // SQLite Explorer
  const [sqliteDbs, setSqliteDbs] = useState<string[]>([]);
  const [selectedSqliteDb, setSelectedSqliteDb] = useState('');
  const [sqliteTables, setSqliteTables] = useState<string[]>([]);
  const [selectedSqliteTable, setSelectedSqliteTable] = useState('');
  const [sqliteData, setSqliteData] = useState<any>(null);

  // Workspace Files
  const [currentFiles, setCurrentFiles] = useState<Record<string, string>>({});
  const [openTabs, setOpenTabs] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState<string | null>(null);
  const [expandedFolders, setExpandedFolders] = useState<Record<string, boolean>>({});
  const [fileSearchQuery, setFileSearchQuery] = useState('');
  const [globalSearchQuery, setGlobalSearchQuery] = useState('');

  // LLM Configurations
  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [promptInput, setPromptInput] = useState('');
  const [temperature, setTemperature] = useState(0.3);
  const [contextWindow, setContextWindow] = useState('8.192 Tokens');
  const [forceJson, setForceJson] = useState(true);
  const [systemPrompt, setSystemPrompt] = useState('Eres el Orquestador V5. Responde siempre en JSON.');

  // Pipeline & Agent Runs
  const [pipelineLogs, setPipelineLogs] = useState<string[]>([]);
  const [isPipelineRunning, setIsPipelineRunning] = useState(false);

  // Terminal Launcher
  const [launcherLogs, setLauncherLogs] = useState<string[]>([]);
  const [isAppLaunching, setIsAppLaunching] = useState(false);

  // Chatbot Agent
  const [chatMessage, setChatMessage] = useState('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [isChatThinking, setIsChatThinking] = useState(false);
  const [chatTarget, setChatTarget] = useState<'general' | 'architect' | 'qa' | 'devops' | 'debate'>('general');

  // Physical Telemetry & Vercel
  const [hwTime, setHwTime] = useState('00:00:00');
  const [hwCpuTemp, setHwCpuTemp] = useState('45.0°C');
  const [hwCpuUsage, setHwCpuUsage] = useState(25);
  const [hwRamUsage, setHwRamUsage] = useState('4.2 / 16.0 GB');
  const [hwRamPercentage, setHwRamPercentage] = useState(26);
  const [hwDiskUsage, setHwDiskUsage] = useState('45%');
  const [hwDiskPercentage, setHwDiskPercentage] = useState(45);
  const [dockerContainers, setDockerContainers] = useState<DockerContainer[]>([]);
  const [dockerError, setDockerError] = useState<string | null>(null);
  const [vercelUrl, setVercelUrl] = useState<string | null>(null);
  const [isDeployingVercel, setIsDeployingVercel] = useState(false);
  const [tokenIn, setTokenIn] = useState(0);
  const [tokenOut, setTokenOut] = useState(0);
  const [costUsd, setCostUsd] = useState(0.0);
  const [cacheHits, setCacheHits] = useState(0);
  const [vaultPrompts, setVaultPrompts] = useState<string[]>([]);

  // Env Config & Pre-flight
  const [envContent, setEnvContent] = useState('');
  const [envEditMode, setEnvEditMode] = useState<'visual' | 'raw'>('visual');
  const [preflightStatus, setPreflightStatus] = useState<Record<string, boolean>>({
    node: false, docker: false, python: false, git: false
  });
  const [installingTools, setInstallingTools] = useState<Record<string, boolean>>({});

  // Editor View Preferences
  const [showPreview, setShowPreview] = useState(false);
  const [editorFontSize, setEditorFontSize] = useState(12);

  // Monaco Diff Editor
  const [isDiffMode, setIsDiffMode] = useState(false);
  const [diffOriginalContent, setDiffOriginalContent] = useState('');

  // ER Schema Diagram
  const [dbSchemaData, setDbSchemaData] = useState<Record<string, any> | null>(null);
  const [isDbSchemaLoading, setIsDbSchemaLoading] = useState(false);
  const [dbSchemaError, setDbSchemaError] = useState<string | null>(null);

  // GitHub Graduation
  const [githubToken, setGithubToken] = useState(() => localStorage.getItem('squad_github_token') || '');
  const [githubRepoName, setGithubRepoName] = useState(() => localStorage.getItem('squad_github_repo_name') || '');
  const [githubPrivate, setGithubPrivate] = useState(false);
  const [isPublishingGithub, setIsPublishingGithub] = useState(false);

  // DB Auto-provision
  const [isDbProvisioning, setIsDbProvisioning] = useState(false);

  // V7 Features states
  const [pendingWrites, setPendingWrites] = useState<any[]>([]);
  const [listeningPorts, setListeningPorts] = useState<any[]>([]);
  const [providersList, setProvidersList] = useState<any[]>([]);

  // Refs
  const logsContainerRef = useRef<HTMLDivElement>(null);
  const terminalContainerRef = useRef<HTMLDivElement>(null);
  const chatHistoryRef = useRef<HTMLDivElement>(null);

  const getThemeClasses = () => {
    switch (theme) {
      case 'cyberpunk':
        return {
          bg: "bg-[#09080d]/95 text-[#00ffcc]",
          card: "bg-black/80 border border-[#ff0055]/30 shadow-[0_0_15px_rgba(255,0,85,0.15)]",
          accentText: "text-[#ff0055] font-mono",
          accentBg: "bg-[#ff0055] hover:bg-[#d60048]",
          accentGlow: "shadow-[0_0_20px_#ff0055]",
          border: "border-[#ff0055]/20",
          inputBg: "bg-black/90 border border-[#00ffcc]/30",
          accentHoverBg: "hover:bg-[#ff3377]"
        };
      case 'matrix':
        return {
          bg: "bg-[#020804] text-[#00ff00]",
          card: "bg-[#031406]/90 border border-[#00ff00]/40 shadow-[0_0_12px_rgba(0,255,0,0.15)]",
          accentText: "text-[#00ff00] font-mono",
          accentBg: "bg-[#00cc00] hover:bg-[#009900]",
          accentGlow: "shadow-[0_0_20px_#00ff00]",
          border: "border-[#00ff00]/20",
          inputBg: "bg-[#010903]/90 border border-[#00ff00]/30",
          accentHoverBg: "hover:bg-[#33ff33]"
        };
      case 'light':
        return {
          bg: "bg-slate-50 text-slate-900",
          card: "bg-white/80 border border-slate-200 shadow-md backdrop-blur-md",
          accentText: "text-indigo-600 font-semibold",
          accentBg: "bg-indigo-600 hover:bg-indigo-700 text-white",
          accentGlow: "shadow-indigo-200 shadow-md",
          border: "border-slate-200",
          inputBg: "bg-white border border-slate-300 text-slate-900",
          accentHoverBg: "hover:bg-indigo-700"
        };
      case 'glass':
        return {
          bg: "bg-slate-950/80 text-white backdrop-blur-2xl",
          card: "bg-white/5 border border-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.37)] backdrop-blur-md",
          accentText: "text-purple-300 font-bold",
          accentBg: "bg-purple-600/30 hover:bg-purple-600/50 text-purple-200 border border-purple-500/40",
          accentGlow: "shadow-[0_0_30px_rgba(168,85,247,0.15)]",
          border: "border-white/5",
          inputBg: "bg-black/50 border border-white/10",
          accentHoverBg: "hover:bg-purple-500/40"
        };
      case 'dark':
      default:
        return {
          bg: "bg-[#0A0A0C] text-gray-200",
          card: "bg-[#111115]/80 border border-white/5 shadow-2xl backdrop-blur-md",
          accentText: "text-amber-400 font-bold",
          accentBg: "bg-amber-500 hover:bg-amber-600 text-black",
          accentGlow: "shadow-[0_0_20px_rgba(245,158,11,0.15)]",
          border: "border-white/5",
          inputBg: "bg-black/40 border border-white/10",
          accentHoverBg: "hover:bg-amber-600"
        };
    }
  };
  const tc = getThemeClasses();

  // API Call Fetchers
  const fetchModels = () => {
    fetch(API_BASE + '/api/models')
      .then(r => r.json())
      .then(d => {
        setModels(d.models || []);
        if (d.models && d.models.length > 0) {
          const defaultModel = d.models.find((m: string) => m.includes('qwen')) || d.models[0];
          setSelectedModel(defaultModel);
        }
      })
      .catch(e => console.error("Error fetching models", e));
  };

  const fetchFiles = () => {
    fetch(API_BASE + '/api/files')
      .then(r => r.json())
      .then(d => {
        const files = d.files || {};
        setCurrentFiles(prev => {
          const merged = { ...prev };
          Object.keys(files).forEach(k => {
            if (merged[k] === undefined || prev[k] === files[k]) {
              merged[k] = files[k];
            }
          });
          return merged;
        });

        const fileList = Object.keys(files);
        if (fileList.length > 0 && !activeTab) {
          const defaultTab = fileList.includes('ARCHITECTURE.md') ? 'ARCHITECTURE.md' : fileList[0];
          setActiveTab(defaultTab);
          if (!openTabs.includes(defaultTab)) {
            setOpenTabs([defaultTab]);
          }
        }
      })
      .catch(e => console.error("Error fetching files", e));
  };

  const fetchChatHistory = () => {
    fetch(API_BASE + '/api/chat-history')
      .then(r => r.json())
      .then(d => setChatHistory(d.history || []))
      .catch(e => console.error("Error fetching chat history", e));
  };

  const fetchGitHistory = () => {
    fetch(API_BASE + '/api/git/history')
      .then(r => r.json())
      .then(d => {
        if (d.success) setGitCommits(d.commits || []);
      })
      .catch(e => console.error("Error fetching git history", e));
  };

  const fetchDockerContainers = () => {
    fetch(API_BASE + '/api/infra/docker')
      .then(r => r.json())
      .then(d => {
        if (d.error) {
          setDockerError(d.error);
          setDockerContainers([]);
        } else {
          setDockerError(null);
          setDockerContainers(d.containers || []);
        }
      })
      .catch(e => {
        setDockerError("No se pudo conectar a los contenedores.");
        console.error(e);
      });
  };

  const fetchSqliteDbs = () => {
    fetch(API_BASE + '/api/infra/sqlite')
      .then(r => r.json())
      .then(d => {
        const dbs = d.dbs || [];
        setSqliteDbs(dbs);
        if (dbs.length > 0) {
          setSelectedSqliteDb(dbs[0]);
          fetchSqliteTables(dbs[0]);
        }
      })
      .catch(e => console.error("Error loading SQLite DBs", e));
  };

  const fetchSqliteTables = (dbName: string) => {
    if (!dbName) return;
    fetch(API_BASE + `/api/infra/sqlite/tables?db=${encodeURIComponent(dbName)}`)
      .then(r => r.json())
      .then(d => {
        const tables = d.tables || [];
        setSqliteTables(tables);
        if (tables.length > 0) {
          setSelectedSqliteTable(tables[0]);
          fetchSqliteTableData(dbName, tables[0]);
        } else {
          setSelectedSqliteTable('');
          setSqliteData(null);
        }
      })
      .catch(e => console.error("Error loading SQLite tables", e));
  };

  const fetchSqliteTableData = (dbName: string, tableName: string) => {
    if (!dbName || !tableName) return;
    fetch(API_BASE + `/api/infra/sqlite/data?db=${encodeURIComponent(dbName)}&table=${encodeURIComponent(tableName)}`)
      .then(r => r.json())
      .then(d => {
        if (d.error) {
          console.error(d.error);
          setSqliteData(null);
        } else {
          setSqliteData({ columns: d.columns || [], rows: d.rows || [] });
        }
      })
      .catch(e => console.error("Error loading SQLite rows", e));
  };

  const fetchEnvContent = () => {
    fetch(API_BASE + '/api/infra/env')
      .then(r => r.json())
      .then(d => setEnvContent(d.env || ''))
      .catch(e => console.error("Error loading env content", e));
  };

  const fetchPreflightStatus = () => {
    fetch(API_BASE + '/api/infra/preflight')
      .then(r => r.json())
      .then(d => {
        if (d.preflight) {
          setPreflightStatus(d.preflight);
          setInstallingTools(prev => {
            const next = { ...prev };
            Object.keys(d.preflight).forEach(k => {
              if (d.preflight[k]) next[k] = false;
            });
            return next;
          });
        }
      })
      .catch(e => console.error("Error fetching preflight status", e));
  };

  const fetchTelemetry = () => {
    fetch(API_BASE + '/api/llm/telemetry')
      .then(r => r.json())
      .then(d => {
        if (d.token_in !== undefined) setTokenIn(d.token_in);
        if (d.token_out !== undefined) setTokenOut(d.token_out);
        if (d.cost_usd !== undefined) setCostUsd(d.cost_usd);
        if (d.cache_hits !== undefined) setCacheHits(d.cache_hits);
      })
      .catch(e => console.error("Error fetching telemetry", e));
  };

  const fetchSettings = () => {
    fetch(API_BASE + '/api/settings')
      .then(r => r.json())
      .then(d => {
        if (d.success && d.settings) {
          setSettings(d.settings);
          setTemperature(d.settings.temperature);
          if (d.settings.default_model) setSelectedModel(d.settings.default_model);
          if (d.settings.design_identity) setDesignIdentity(d.settings.design_identity);
          if (d.settings.smart_routing !== undefined) setSmartRouting(d.settings.smart_routing);
        }
      })
      .catch(e => console.error("Error fetching settings:", e));
  };

  const fetchPostgresTables = () => {
    setPostgresError(null);
    fetch(API_BASE + '/api/infra/postgres/tables')
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          setPostgresTables(d.tables || []);
          if (d.tables && d.tables.length > 0) {
            setSelectedPostgresTable(d.tables[0]);
            fetchPostgresTableData(d.tables[0]);
          } else {
            setPostgresTables([]);
            setPostgresData(null);
          }
        } else {
          setPostgresError(d.error || "No se pudo conectar a la base de datos.");
          setPostgresTables([]);
          setPostgresData(null);
        }
      })
      .catch(e => {
        setPostgresError("Error de conexión con el backend.");
        console.error(e);
      });
  };

  const fetchPostgresTableData = (table: string) => {
    if (!table) return;
    fetch(API_BASE + `/api/infra/postgres/data?table=${table}`)
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          setPostgresData({ columns: d.columns || [], rows: d.rows || [] });
        } else {
          alert("Error cargando datos de Postgres: " + d.error);
        }
      })
      .catch(e => console.error(e));
  };

  // Actions
  const saveSettingsConfig = (newSettings: any) => {
    const updated = { ...settings, ...newSettings };
    setSettings(updated);
    fetch(API_BASE + '/api/settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(updated)
    })
      .then(r => r.json())
      .then(d => {
        if (d.success) fetchFiles();
        else alert("Error guardando ajustes: " + d.message);
      })
      .catch(e => console.error("Error saving settings:", e));
  };

  const startBuildPipeline = () => {
    if (!promptInput.trim()) return;
    setIsPipelineRunning(true);
    setPipelineLogs([">> Iniciando enjambre de agentes..."]);
    setTokenIn(prev => prev + Math.floor(Math.random() * 5000 + 2000));
    setTokenOut(prev => prev + Math.floor(Math.random() * 2000 + 500));

    fetch(API_BASE + '/api/run-agent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ goal: promptInput, model: selectedModel })
    }).catch(e => {
      console.error("Error executing pipeline", e);
      setIsPipelineRunning(false);
    });
  };

  const saveActiveFile = () => {
    if (!activeTab) return;
    const content = currentFiles[activeTab] || '';
    showToast(`Formateando y guardando ${activeTab}...`, "info");
    
    fetch(API_BASE + '/api/format', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: activeTab, content })
    })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          showToast(`✅ Guardado y Formateado: ${activeTab}`, "success");
          if (d.content !== undefined) {
            setCurrentFiles(prev => ({ ...prev, [activeTab]: d.content }));
          }
          fetchFiles();
          fetchGitHistory();
          if (isDiffMode) fetchFileOriginalContent(activeTab);
        } else {
          showToast(`❌ Error al guardar: ${d.message}`, "error");
        }
      })
      .catch(e => showToast(`❌ Error de conexión: ${e}`, "error"));
  };

  const fetchFileOriginalContent = (filename: string) => {
    if (!filename) return;
    fetch(API_BASE + `/api/git/file-history?file=${encodeURIComponent(filename)}`)
      .then(r => r.json())
      .then(d => {
        setDiffOriginalContent(d.success ? d.content || '' : '');
      })
      .catch(e => {
        console.error("Error loading file history", e);
        setDiffOriginalContent('');
      });
  };

  const revertGitCommit = (hash: string) => {
    if (!confirm(`¿Estás seguro de que deseas revertir el workspace al commit ${hash}? Todos los cambios no guardados se perderán.`)) return;
    fetch(API_BASE + '/api/git/revert', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ hash })
    })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          alert(`✅ Workspace revertido exitosamente al commit ${hash}.`);
          fetchFiles();
          fetchGitHistory();
        } else {
          alert(`❌ Error al revertir: ${d.message}`);
        }
      })
      .catch(e => alert("Error: " + e));
  };

  const applyProjectTemplate = (templateName: string) => {
    if (!confirm(`¿Estás seguro de que deseas aplicar la plantilla '${templateName}'? Esto borrará el código actual de tu Workspace.`)) return;
    setIsApplyingTemplate(true);
    fetch(API_BASE + '/api/templates/apply', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ template: templateName })
    })
      .then(r => r.json())
      .then(d => {
        setIsApplyingTemplate(false);
        if (d.success) {
          alert(`✅ Plantilla '${templateName}' aplicada correctamente.`);
          setActiveTab(null);
          setOpenTabs([]);
          fetchFiles();
          fetchGitHistory();
        } else {
          alert(`❌ Error aplicando plantilla: ${d.message}`);
        }
      })
      .catch(e => {
        setIsApplyingTemplate(false);
        alert("Error: " + e);
      });
  };

  const sendChatMessage = () => {
    if (!chatMessage.trim() || isChatThinking) return;
    const msg = chatMessage;
    setChatMessage('');
    setChatHistory(prev => [...prev, { role: 'user', content: msg }]);
    setIsChatThinking(true);

    fetch(API_BASE + '/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg, model: selectedModel, target: chatTarget })
    })
      .then(r => r.json())
      .then(d => {
        setIsChatThinking(false);
        setChatHistory(d.history || []);
        fetchFiles();
      })
      .catch(e => {
        setIsChatThinking(false);
        console.error(e);
      });
  };

  const launchAppSystem = () => {
    setIsAppLaunching(true);
    setLauncherLogs(["[SISTEMA] Iniciando despliegue de lanzamiento..."]);
    
    fetch(API_BASE + '/api/launch', { 
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: selectedModel })
    })
      .then(r => r.json())
      .then(d => {
        if (!d.success) {
          showToast(`❌ Error al lanzar: ${d.message}`, "error");
          setIsAppLaunching(false);
        } else {
          showToast(`🚀 Lanzamiento iniciado: ${d.message}`, "success");
          setIsAppLaunching(false);
        }
      })
      .catch(e => {
        showToast(`❌ Error de red: ${e.message}`, "error");
        setIsAppLaunching(false);
      });
  };

  const optimizePrompt = async (promptText: string) => {
    if (!promptText.trim()) return;
    showToast("✨ Optimizando prompt con IA...", "info");
    try {
      const response = await fetch(API_BASE + '/api/prompt/optimize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: promptText, model: selectedModel })
      });
      const d = await response.json();
      if (d.success && d.optimized) {
        setPromptInput(d.optimized);
        showToast("✨ Prompt optimizado!", "success");
      } else {
        showToast("❌ Error al optimizar prompt: " + (d.detail || d.message || "Error desconocido"), "error");
      }
    } catch (e: any) {
      showToast("❌ Error de red: " + e.message, "error");
    }
  };

  const adjustSpec = async (feedbackText: string) => {
    if (!feedbackText.trim()) return;
    showToast("🧠 Refinando especificación...", "info");
    try {
      const response = await fetch(API_BASE + '/api/spec/adjust', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feedback: feedbackText, model: selectedModel })
      });
      const d = await response.json();
      if (d.success) {
        fetchFiles();
        showToast("✅ Especificación SPEC.md actualizada", "success");
      } else {
        showToast("❌ Error al refinar: " + (d.detail || d.message), "error");
      }
    } catch (e: any) {
      showToast("❌ Error de red: " + e.message, "error");
    }
  };

  const approveSpec = async () => {
    showToast("🚀 Construyendo aplicación...", "info");
    try {
      const response = await fetch(API_BASE + '/api/spec/approve', {
        method: 'POST'
      });
      const d = await response.json();
      if (d.success) {
        showToast("🚀 Fase 2 del enjambre iniciada", "success");
        setActiveDiagnostic(null);
      } else {
        showToast("❌ Error al aprobar: " + (d.detail || d.message), "error");
      }
    } catch (e: any) {
      showToast("❌ Error de red: " + e.message, "error");
    }
  };

  const seedDb = async () => {
    showToast("🌱 Generando datos semilla...", "info");
    try {
      const response = await fetch(API_BASE + '/api/infra/db-seed', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: selectedModel })
      });
      const d = await response.json();
      if (d.success) {
        showToast("🌱 Datos semilla generados e insertados", "success");
        if (selectedSqliteDb) {
          fetchSqliteTables(selectedSqliteDb);
        }
      } else {
        showToast("❌ Error al generar semillas: " + (d.detail || d.message), "error");
      }
    } catch (e: any) {
      showToast("❌ Error de red: " + e.message, "error");
    }
  };

  const runUxAudit = async () => {
    showToast("🎨 Iniciando auditoría visual...", "info");
    try {
      const response = await fetch(API_BASE + '/api/ux/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: selectedModel })
      });
      const d = await response.json();
      if (d.success) {
        showToast("🎨 Auditoría visual registrada en VISUAL_REPORT.md", "success");
        fetchFiles();
      } else {
        showToast("❌ Error al auditar: " + (d.detail || d.message), "error");
      }
    } catch (e: any) {
      showToast("❌ Error de red: " + e.message, "error");
    }
  };

  const runUxFix = async () => {
    showToast("🎨 Aplicando mejoras de UI/UX...", "info");
    try {
      const response = await fetch(API_BASE + '/api/ux/fix', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: selectedModel })
      });
      const d = await response.json();
      if (d.success) {
        showToast("🎨 Mejoras aplicadas con éxito!", "success");
        fetchFiles();
      } else {
        showToast("❌ Error al aplicar mejoras: " + (d.detail || d.message), "error");
      }
    } catch (e: any) {
      showToast("❌ Error de red: " + e.message, "error");
    }
  };

  const extractUxStyle = async () => {
    showToast("💾 Extrayendo identidad del proyecto...", "info");
    try {
      const response = await fetch(API_BASE + '/api/ux/extract-style', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ model: selectedModel })
      });
      const d = await response.json();
      if (d.success && d.profile) {
        setDesignIdentity(d.profile);
        showToast("💾 Memoria de estilo actualizada", "success");
      } else {
        showToast("❌ Error al extraer: " + (d.detail || d.message), "error");
      }
    } catch (e: any) {
      showToast("❌ Error de red: " + e.message, "error");
    }
  };

  const gitCheckout = async (hash: string) => {
    showToast(`⏱️ Viajando en el tiempo al commit ${hash}...`, "info");
    try {
      const response = await fetch(API_BASE + '/api/git/checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hash })
      });
      const d = await response.json();
      if (d.success) {
        showToast(`⏱️ Workspace cambiado al commit ${hash}`, "success");
        fetchFiles();
      } else {
        showToast("❌ Error al cambiar: " + (d.detail || d.message), "error");
      }
    } catch (e: any) {
      showToast("❌ Error de red: " + e.message, "error");
    }
  };

  const gitRestoreHead = async () => {
    showToast("⏱️ Regresando al presente (HEAD)...", "info");
    try {
      const response = await fetch(API_BASE + '/api/git/restore-head', {
        method: 'POST'
      });
      const d = await response.json();
      if (d.success) {
        showToast("⏱️ Regresaste al estado actual", "success");
        fetchFiles();
      } else {
        showToast("❌ Error al regresar: " + (d.detail || d.message), "error");
      }
    } catch (e: any) {
      showToast("❌ Error de red: " + e.message, "error");
    }
  };

  const installSystemTool = (toolName: string) => {
    setInstallingTools(prev => ({ ...prev, [toolName]: true }));
    setLauncherLogs(prev => [...prev, `[AUTO-INSTALADOR] Iniciando instalación remota de ${toolName} via winget...`]);
    
    fetch(API_BASE + '/api/infra/install', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tool: toolName })
    })
      .then(r => r.json())
      .then(d => {
        if (d.success) alert(`📥 ${d.message}\nSigue el progreso en la consola inferior.`);
        else {
          alert(`❌ Error al instalar: ${d.message}`);
          setInstallingTools(prev => ({ ...prev, [toolName]: false }));
        }
      })
      .catch(e => {
        alert(`❌ Conexión fallida: ${e}`);
        setInstallingTools(prev => ({ ...prev, [toolName]: false }));
      });
  };

  const saveEnvContent = () => {
    fetch(API_BASE + '/api/save_file', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: '.env', content: envContent })
    })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          alert("✅ Variables de entorno (.env) guardadas exitosamente.");
          fetchModels();
        }
        else alert("❌ Error al guardar .env: " + d.message);
      })
      .catch(e => alert("Error: " + e));
  };

  const saveToVault = () => {
    if (!promptInput.trim()) return;
    fetch(API_BASE + '/api/llm/vault', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: promptInput })
    })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          setVaultPrompts(d.prompts || []);
          showToast("💾 Prompt guardado en el baúl.", "success");
        }
      })
      .catch(e => console.error("Error saving prompt to vault", e));
  };

  const fetchPendingWrites = () => {
    fetch(API_BASE + '/api/infra/pending-writes')
      .then(r => r.json())
      .then(d => {
        setPendingWrites(d.pending || []);
      })
      .catch(e => console.error("Error fetching pending writes", e));
  };

  const resolvePendingWrites = (action: 'confirm' | 'reject', files: string[]) => {
    fetch(API_BASE + '/api/infra/pending-writes/resolve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, files })
    })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          showToast(d.message, "success");
          fetchPendingWrites();
          fetchFiles();
        } else {
          showToast("Error resolviendo cambios: " + d.message, "error");
        }
      })
      .catch(e => showToast("Error: " + e, "error"));
  };

  const fetchListeningPorts = () => {
    fetch(API_BASE + '/api/infra/ports')
      .then(r => r.json())
      .then(d => {
        if (d.success) setListeningPorts(d.ports || []);
      })
      .catch(e => console.error("Error fetching listening ports", e));
  };

  const killListeningPort = (pid: number) => {
    fetch(API_BASE + '/api/infra/ports/kill', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pid })
    })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          showToast(d.message, "success");
          fetchListeningPorts();
        } else {
          showToast("Error cerrando puerto: " + d.message, "error");
        }
      })
      .catch(e => showToast("Error: " + e, "error"));
  };

  const deployToRealProvider = (provider: 'vercel' | 'netlify', token: string) => {
    fetch(API_BASE + '/api/deploy/real', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, token })
    })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          showToast(d.message, "success");
        } else {
          showToast("Error de despliegue: " + d.message, "error");
        }
      })
      .catch(e => showToast("Error: " + e, "error"));
  };

  const refactorCodeAction = (file: string, action: 'docstrings' | 'optimize' | 'typescript' | 'tests') => {
    fetch(API_BASE + '/api/refactor/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ file, action, model: selectedModel })
    })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          showToast(d.message, "success");
          fetchFiles();
        } else {
          showToast("Error de refactorización: " + d.error, "error");
        }
      })
      .catch(e => showToast("Error: " + e, "error"));
  };

  const runDockerCompose = (action: 'up' | 'down' | 'build') => {
    fetch(API_BASE + '/api/infra/docker-compose', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action })
    })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          showToast(d.message, "success");
        } else {
          showToast("Error Docker Compose: " + d.message, "error");
        }
      })
      .catch(e => showToast("Error: " + e, "error"));
  };

  const deleteVaultPrompt = (prompt: string) => {
    fetch(API_BASE + '/api/llm/vault/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt })
    })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          setVaultPrompts(d.prompts || []);
          showToast("🗑️ Prompt eliminado del baúl.", "info");
        }
      })
      .catch(e => console.error("Error deleting prompt from vault", e));
  };

  const fetchProvidersList = () => {
    fetch(API_BASE + '/api/llm/providers')
      .then(r => r.json())
      .then(d => {
        setProvidersList(d.providers || []);
      })
      .catch(e => console.error("Error fetching providers list", e));
  };

  const pullOllamaModel = (model: string) => {
    fetch(API_BASE + '/api/llm/ollama/pull', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model })
    })
      .then(r => r.json())
      .then(d => {
        if (d.success) {
          showToast(d.message, "success");
        } else {
          showToast("Error descargando modelo: " + d.message, "error");
        }
      })
      .catch(e => showToast("Error: " + e, "error"));
  };

  const fetchDbSchemaDiagram = (dbType: 'sqlite' | 'postgres', dbName = '') => {
    setIsDbSchemaLoading(true);
    setDbSchemaError(null);
    const url = API_BASE + `/api/infra/db-schema-diagram?type=${dbType}&db=${encodeURIComponent(dbName)}`;
    fetch(url)
      .then(r => r.json())
      .then(d => {
        setIsDbSchemaLoading(false);
        if (d.success) setDbSchemaData(d.schema || {});
        else {
          setDbSchemaError(d.error || "No se pudo obtener el esquema.");
          setDbSchemaData(null);
        }
      })
      .catch(e => {
        setIsDbSchemaLoading(false);
        setDbSchemaError("Error de red: " + e.message);
        setDbSchemaData(null);
      });
  };

  const publishToGithub = () => {
    if (!githubToken.trim() || !githubRepoName.trim()) {
      alert("Introduce tu Token de GitHub y el nombre del repositorio.");
      return;
    }
    
    localStorage.setItem('squad_github_token', githubToken);
    localStorage.setItem('squad_github_repo_name', githubRepoName);
    setIsPublishingGithub(true);
    showToast("Inicializando y empujando a GitHub...", "info");
    
    fetch(API_BASE + '/api/git/github-publish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: githubToken, repo_name: githubRepoName, private: githubPrivate })
    })
      .then(r => r.json())
      .then(d => {
        setIsPublishingGithub(false);
        if (d.success) {
          showToast("🚀 " + d.message, "success");
          alert("✅ " + d.message);
        } else {
          showToast("❌ " + d.message, "error");
          alert("❌ " + d.message);
        }
      })
      .catch(e => {
        setIsPublishingGithub(false);
        showToast("❌ Error de red: " + e.message, "error");
      });
  };

  const handleDbProvision = () => {
    setIsDbProvisioning(true);
    showToast("Invocando DBA Agent para provisionar base de datos...", "info");
    fetch(API_BASE + '/api/infra/db-provision', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: selectedModel })
    })
      .then(r => r.json())
      .then(d => {
        setIsDbProvisioning(false);
        if (d.success) {
          showToast("✅ Base de datos provisionada correctamente.", "success");
          fetchFiles();
          fetchSqliteDbs();
          if (d.schema) alert(`✅ Base de datos provisionada!\n\nEsquema SQL:\n${d.schema}`);
        } else {
          showToast("❌ Error al provisionar: " + d.message, "error");
        }
      })
      .catch(e => {
        setIsDbProvisioning(false);
        showToast("❌ Error de red: " + e.message, "error");
      });
  };

  const deployToVercel = () => {
    setIsDeployingVercel(true);
    showToast("Desplegando en Vercel...", "info");
    fetch(API_BASE + '/api/deploy/vercel', { method: 'POST' })
      .then(r => r.json())
      .then(d => {
        setIsDeployingVercel(false);
        if (d.success) {
          setVercelUrl(d.url);
          showToast("✅ Despliegue en Vercel completado.", "success");
        }
      })
      .catch(() => {
        setIsDeployingVercel(false);
        showToast("❌ Falló el despliegue en Vercel.", "error");
      });
  };

  // Init Data Fetches
  useEffect(() => {
    fetchSettings();
    fetchModels();
    fetchFiles();
    fetchChatHistory();
    fetchDockerContainers();
    fetchSqliteDbs();
    fetchEnvContent();
    fetchPreflightStatus();
    fetchTelemetry();
    fetchGitHistory();
    fetchPostgresTables();
    fetchPendingWrites();
    fetchListeningPorts();
    fetchProvidersList();
  }, []);

  // Update tabs or fetch context data when switching panels
  useEffect(() => {
    if (activeSidebarTab === 'infra') {
      fetchDockerContainers();
      fetchSqliteDbs();
      fetchEnvContent();
      fetchPreflightStatus();
      fetchPostgresTables();
      fetchListeningPorts();
    } else if (activeSidebarTab === 'llm') {
      fetchTelemetry();
      fetchProvidersList();
    } else if (activeSidebarTab === 'deploy') {
      fetchGitHistory();
    }
  }, [activeSidebarTab]);

  // Connect to the native SSE stream
  useEffect(() => {
    const sseUrl = `${API_BASE}/api/stream-logs`;
    console.log("Conectando EventSource a", sseUrl);
    const eventSource = new EventSource(sseUrl);

    eventSource.addEventListener('pipeline_logs', (e: any) => {
      try {
        const data = JSON.parse(e.data);
        setPipelineLogs((prev) => {
          const nextLogs = data.logs || [];
          if (prev.length === nextLogs.length && (prev.length === 0 || prev[prev.length - 1] === nextLogs[nextLogs.length - 1])) {
            return prev;
          }
          return nextLogs;
        });
        setIsPipelineRunning((prev) => prev === data.is_running ? prev : data.is_running);
        if (data.pipeline_status) {
          setPipelineStatus((prev) => prev === data.pipeline_status ? prev : data.pipeline_status);
        }
      } catch (err) {
        console.error("Error parsing pipeline logs SSE:", err);
      }
    });

    eventSource.addEventListener('launcher_logs', (e: any) => {
      try {
        const data = JSON.parse(e.data);
        setLauncherLogs((prev) => {
          const nextLogs = data.logs || [];
          if (prev.length === nextLogs.length && (prev.length === 0 || prev[prev.length - 1] === nextLogs[nextLogs.length - 1])) {
            return prev;
          }
          return nextLogs;
        });
        if (data.active_port) {
          setActivePort((prev) => prev === data.active_port ? prev : data.active_port);
        }
        if (data.active_diagnostic !== undefined) {
          setActiveDiagnostic((prev) => JSON.stringify(prev) === JSON.stringify(data.active_diagnostic) ? prev : data.active_diagnostic);
        }
        const hasInterceptor = (data.logs || []).some((l: string) => l.includes("[INTERCEPTOR]"));
        if (hasInterceptor) {
          fetchPendingWrites();
        }
      } catch (err) {
        console.error("Error parsing launcher logs SSE:", err);
      }
    });

    eventSource.addEventListener('file_change', (e: any) => {
      try {
        console.log("🔥 [HOT RELOAD] Cambio de archivo detectado en SSE, recargando iframe preview...");
        const iframe = document.getElementById('sandbox-iframe') as HTMLIFrameElement;
        if (iframe) {
          const src = iframe.src;
          iframe.src = '';
          iframe.src = src;
        }
        fetchFiles();
        fetchGitHistory();
      } catch (err) {
        console.error("Error handling file_change SSE:", err);
      }
    });

    eventSource.onerror = (err) => {
      console.error("EventSource error:", err);
    };

    return () => eventSource.close();
  }, []);

  // Jitter and Hardware statistics monitoring interval
  useEffect(() => {
    const interval = setInterval(() => {
      const d = new Date();
      setHwTime(d.toTimeString().split(' ')[0]);

      fetchPendingWrites();

      fetch(API_BASE + '/api/infra/telemetry')
        .then(r => r.json())
        .then(data => {
          if (data.success) {
            setHwCpuTemp(`${data.cpu_temp.toFixed(1)}°C`);
            setHwCpuUsage(data.cpu_usage);
            setHwRamUsage(`${(data.ram_used / (1024**3)).toFixed(1)} / ${(data.ram_total / (1024**3)).toFixed(1)} GB`);
            setHwRamPercentage(data.ram_percentage);
            setHwDiskUsage(`${data.disk_percentage}%`);
            setHwDiskPercentage(data.disk_percentage);
          }
        })
        .catch(() => {
          setHwCpuTemp(`${(45 + Math.random() * 5).toFixed(1)}°C`);
          setHwCpuUsage(Math.floor(20 + Math.random() * 15));
        });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <AppContext.Provider value={{
      theme, setTheme, activeSidebarTab, setActiveSidebarTab,
      toasts, showToast,
      promptDialog, setPromptDialog, promptInputText, setPromptInputText, openCustomPrompt,
      confirmDialog, setConfirmDialog, openCustomConfirm,
      settings, saveSettingsConfig, stdinInput, setStdinInput, stdinHistory, setStdinHistory, stdinHistoryIdx, setStdinHistoryIdx,
      gitCommits, fetchGitHistory, revertGitCommit,
      isApplyingTemplate, applyProjectTemplate,
      postgresTables, selectedPostgresTable, setSelectedPostgresTable, postgresData, postgresError, fetchPostgresTables, fetchPostgresTableData,
      sqliteDbs, selectedSqliteDb, setSelectedSqliteDb, sqliteTables, selectedSqliteTable, setSelectedSqliteTable, sqliteData, fetchSqliteDbs, fetchSqliteTables, fetchSqliteTableData,
      currentFiles, setCurrentFiles, openTabs, setOpenTabs, activeTab, setActiveTab, expandedFolders, setExpandedFolders, fileSearchQuery, setFileSearchQuery, globalSearchQuery, setGlobalSearchQuery, fetchFiles, saveActiveFile,
      models, selectedModel, setSelectedModel, promptInput, setPromptInput, temperature, setTemperature, contextWindow, setContextWindow, forceJson, setForceJson, systemPrompt, setSystemPrompt,
      pipelineLogs, isPipelineRunning, startBuildPipeline,
      launcherLogs, setLauncherLogs, isAppLaunching, setIsAppLaunching, launchAppSystem,
      chatMessage, setChatMessage, chatHistory, setChatHistory, isChatThinking, chatTarget, setChatTarget, sendChatMessage,
      hwTime, hwCpuTemp, hwCpuUsage, hwRamUsage, hwRamPercentage, hwDiskUsage, hwDiskPercentage, dockerContainers, dockerError, vercelUrl, isDeployingVercel, deployToVercel, tokenIn, tokenOut, costUsd, cacheHits, vaultPrompts, fetchTelemetry, saveToVault,
      envContent, setEnvContent, envEditMode, setEnvEditMode, preflightStatus, installingTools, fetchPreflightStatus, installSystemTool, saveEnvContent,
      showPreview, setShowPreview, editorFontSize, setEditorFontSize,
      isDiffMode, setIsDiffMode, diffOriginalContent, fetchFileOriginalContent,
      dbSchemaData, isDbSchemaLoading, dbSchemaError, fetchDbSchemaDiagram,
      githubToken, setGithubToken, githubRepoName, setGithubRepoName, githubPrivate, setGithubPrivate, isPublishingGithub, publishToGithub,
      isDbProvisioning, handleDbProvision,
      logsContainerRef, terminalContainerRef, chatHistoryRef,
      tc,
      pendingWrites, fetchPendingWrites, resolvePendingWrites,
      listeningPorts, fetchListeningPorts, killListeningPort,
      deployToRealProvider, refactorCodeAction, runDockerCompose,
      deleteVaultPrompt, providersList, fetchProvidersList, pullOllamaModel,
      pipelineStatus, activePort, activeDiagnostic, designIdentity, setDesignIdentity, smartRouting, setSmartRouting,
      optimizePrompt, adjustSpec, approveSpec, seedDb, runUxAudit, runUxFix, extractUxStyle, gitCheckout, gitRestoreHead
    }}>
      {children}
    </AppContext.Provider>
  );
};
