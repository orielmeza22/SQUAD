import React, { useState, useEffect, useRef } from 'react';
import { useApp } from '../context/AppContext';
import { Database, RefreshCw, AlertTriangle, ArrowRight } from 'lucide-react';

export default function DatabaseVisualizer() {
  const {
    dbSchemaData,
    isDbSchemaLoading,
    dbSchemaError,
    fetchDbSchemaDiagram,
    sqliteDbs,
    selectedSqliteDb,
    setSelectedSqliteDb,
    sqliteTables,
    selectedSqliteTable,
    setSelectedSqliteTable,
    sqliteData,
    fetchSqliteDbs,
    fetchSqliteTables,
    fetchSqliteTableData,
    postgresTables,
    selectedPostgresTable,
    setSelectedPostgresTable,
    postgresData,
    postgresError,
    fetchPostgresTables,
    fetchPostgresTableData,
    activeTab,
    tc,
    seedDb
  } = useApp();

  const [activeSubTab, setActiveSubTab] = useState<'tables' | 'diagram' | 'sql'>('tables');
  const [sqlQuery, setSqlQuery] = useState('SELECT * FROM sqlite_master WHERE type="table";');
  const [sqlResult, setSqlResult] = useState<{ success: boolean; columns?: string[]; rows?: any[]; message?: string; error?: string } | null>(null);
  const [isExecutingSql, setIsExecutingSql] = useState(false);

  const executeSql = () => {
    if (!sqlQuery.trim()) return;
    setIsExecutingSql(true);
    setSqlResult(null);
    const API_BASE = window.location.port === '3000' ? 'http://localhost:8000' : '';
    fetch(API_BASE + '/api/infra/sql-query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: sqlQuery })
    })
      .then(r => r.json())
      .then(d => {
        setIsExecutingSql(false);
        setSqlResult(d);
      })
      .catch(e => {
        setIsExecutingSql(false);
        setSqlResult({ success: false, error: e.message || String(e) });
      });
  };

  // Draggable tables state for ER Diagram
  const [positions, setPositions] = useState<Record<string, { x: number, y: number }>>({});
  const [draggingTable, setDraggingTable] = useState<string | null>(null);
  const dragStart = useRef({ x: 0, y: 0 });
  const tablePosStart = useRef({ x: 0, y: 0 });

  const handleMouseDown = (e: React.MouseEvent, tableName: string) => {
    // Only drag with left click on the card header
    if (e.button !== 0) return;
    setDraggingTable(tableName);
    dragStart.current = { x: e.clientX, y: e.clientY };
    const currentPos = positions[tableName] || { x: 0, y: 0 };
    tablePosStart.current = { ...currentPos };
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!draggingTable) return;
      const dx = e.clientX - dragStart.current.x;
      const dy = e.clientY - dragStart.current.y;
      setPositions(prev => ({
        ...prev,
        [draggingTable]: {
          x: tablePosStart.current.x + dx,
          y: tablePosStart.current.y + dy
        }
      }));
    };

    const handleMouseUp = () => {
      if (draggingTable) setDraggingTable(null);
    };

    if (draggingTable) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
    }
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [draggingTable]);

  // Sync schema diagram data when database changes
  useEffect(() => {
    if (selectedSqliteDb) {
      fetchDbSchemaDiagram('sqlite', selectedSqliteDb);
    }
  }, [selectedSqliteDb]);

  const renderDBSchemaDiagram = () => {
    if (isDbSchemaLoading) {
      return (
        <div className="flex flex-col items-center justify-center h-64 text-white/40 space-y-4 font-mono">
          <Database size={32} className="text-amber-500/50 animate-pulse" />
          <p className="text-[11px] italic">Diseñando plano de base de datos...</p>
        </div>
      );
    }
    
    if (dbSchemaError) {
      return (
        <div className="flex flex-col items-center justify-center h-64 text-rose-400 p-6 space-y-3 text-center font-mono">
          <AlertTriangle size={28} />
          <p className="text-xs font-bold">{dbSchemaError}</p>
        </div>
      );
    }
    
    if (!dbSchemaData) {
      return (
        <div className="flex flex-col items-center justify-center h-64 text-white/30 space-y-2 font-mono">
          <Database size={28} />
          <p className="text-xs italic">Presiona Actualizar para cargar el plano.</p>
        </div>
      );
    }
    
    const tables = Object.entries(dbSchemaData);
    if (tables.length === 0) {
      return (
        <div className="flex flex-col items-center justify-center h-64 text-white/30 space-y-2 font-mono">
          <Database size={28} />
          <p className="text-xs">No se encontraron tablas en el esquema.</p>
        </div>
      );
    }
    
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center text-[10px] text-gray-500 font-mono border-b border-white/5 pb-2">
          <span>💡 Consejo: Mantén presionado y arrastra las cabeceras de las tarjetas para organizar tu esquema.</span>
          <button 
            onClick={() => setPositions({})}
            className="text-[9px] hover:text-amber-400 font-bold border border-white/10 px-2 py-0.5 rounded cursor-pointer"
            title="Restablecer posiciones"
          >
            Restablecer Posición
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 relative min-h-[400px] p-2">
          {tables.map(([tableName, tableInfo]: [string, any]) => {
            const pos = positions[tableName] || { x: 0, y: 0 };
            return (
              <div 
                key={tableName} 
                className="bg-[#111116]/80 border border-white/10 rounded-lg overflow-hidden shadow-2xl flex flex-col transition-shadow hover:shadow-indigo-500/5 select-none"
                style={{ 
                  transform: `translate(${pos.x}px, ${pos.y}px)`,
                  zIndex: draggingTable === tableName ? 50 : 10,
                  cursor: draggingTable === tableName ? 'grabbing' : 'default'
                }}
              >
                {/* Header (Draggable Handle) */}
                <div 
                  onMouseDown={(e) => handleMouseDown(e, tableName)}
                  className="bg-indigo-950/40 hover:bg-indigo-950/60 border-b border-white/10 p-3 flex justify-between items-center cursor-grab select-none active:cursor-grabbing"
                >
                  <span className="text-xs font-bold text-indigo-400 flex items-center space-x-1.5 font-mono">
                    <span>🗄️</span> 
                    <span>{tableName}</span>
                  </span>
                  <span className="text-[8px] bg-indigo-500/10 text-indigo-300 px-2 py-0.5 rounded font-bold uppercase font-mono">
                    {tableInfo.columns ? tableInfo.columns.length : 0} Cols
                  </span>
                </div>
                
                {/* Columns List */}
                <div className="p-3 space-y-1.5 flex-1 font-mono">
                  {tableInfo.columns && tableInfo.columns.map((col: any) => (
                    <div key={col.name} className="flex justify-between items-center text-[10px] py-1 border-b border-white/5">
                      <span className="flex items-center space-x-1">
                        {col.pk && <span className="text-amber-400" title="Clave Primaria">🔑</span>}
                        <span className={col.pk ? 'text-amber-400 font-bold' : 'text-gray-300'}>
                          {col.name}
                        </span>
                      </span>
                      <span className="text-gray-500 text-[9px] uppercase">{col.type}</span>
                    </div>
                  ))}
                </div>
                
                {/* Foreign Keys / Relations */}
                {tableInfo.foreign_keys && tableInfo.foreign_keys.length > 0 && (
                  <div className="bg-black/30 p-2.5 border-t border-white/5 text-[9px] space-y-1 font-mono">
                    <div className="text-gray-500 font-bold uppercase tracking-wider text-[8px] mb-1">Claves Foráneas</div>
                    {tableInfo.foreign_keys.map((fk: any, idx: number) => (
                      <div key={idx} className="flex items-center space-x-1 text-emerald-400">
                        <span>🔗</span>
                        <span className="font-bold">{fk.from}</span>
                        <span className="text-gray-500">→</span>
                        <span className="text-indigo-400 font-bold truncate" title={`${fk.table}(${fk.to})`}>
                          {fk.table}({fk.to})
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4">
      {/* Sub Tabs Toggle */}
      <div className="flex border-b border-white/5 font-mono select-none">
        <button
          onClick={() => setActiveSubTab('tables')}
          className={`py-2 px-4 text-xs font-bold transition-all border-b-2 ${
            activeSubTab === 'tables' 
              ? 'border-amber-500 text-amber-400' 
              : 'border-transparent text-gray-500 hover:text-white'
          }`}
        >
          🗂️ Explorador de Datos
        </button>
        <button
          onClick={() => {
            setActiveSubTab('diagram');
            if (selectedSqliteDb) fetchDbSchemaDiagram('sqlite', selectedSqliteDb);
            else fetchDbSchemaDiagram('postgres');
          }}
          className={`py-2 px-4 text-xs font-bold transition-all border-b-2 ${
            activeSubTab === 'diagram' 
              ? 'border-amber-500 text-amber-400' 
              : 'border-transparent text-gray-500 hover:text-white'
          }`}
        >
          📊 Diagrama ER Interactivo
        </button>
        <button
          onClick={() => setActiveSubTab('sql')}
          className={`py-2 px-4 text-xs font-bold transition-all border-b-2 ${
            activeSubTab === 'sql' 
              ? 'border-amber-500 text-amber-400' 
              : 'border-transparent text-gray-500 hover:text-white'
          }`}
        >
          💻 Consola SQL
        </button>
      </div>

      {/* RENDER TABLE PREVIEW OR DIAGRAM */}
      {activeSubTab === 'tables' ? (
        <div className="space-y-4 font-mono">
          {/* SQLite Selector Block */}
          {sqliteDbs.length > 0 && (
            <div className="bg-black/30 border border-white/5 rounded p-3 space-y-3 shadow-lg">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-amber-400 uppercase tracking-widest block font-mono">Bases de datos SQLite</span>
                <div className="flex items-center space-x-2 font-mono">
                  <button 
                    onClick={seedDb} 
                    className="text-[9px] bg-emerald-500/20 hover:bg-emerald-500/35 border border-emerald-500/30 text-emerald-300 px-2 py-0.5 rounded transition-all cursor-pointer font-bold"
                    title="Poblar la base de datos con 20-50 registros simulados realistas"
                  >
                    🌱 Generar Semilla
                  </button>
                  <button onClick={fetchSqliteDbs} className="text-[9px] text-white/30 hover:text-white cursor-pointer">↻ REFRESCAR</button>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[8px] text-gray-500 block mb-1 uppercase">Base de Datos</label>
                  <select 
                    value={selectedSqliteDb}
                    onChange={(e) => {
                      setSelectedSqliteDb(e.target.value);
                      fetchSqliteTables(e.target.value);
                    }}
                    className="w-full bg-[#0A0A0C] border border-white/15 text-[10px] p-1.5 rounded outline-none text-emerald-400"
                  >
                    {sqliteDbs.map(db => <option key={db} value={db}>{db}</option>)}
                  </select>
                </div>

                <div>
                  <label className="text-[8px] text-gray-500 block mb-1 uppercase">Tabla SQLite</label>
                  <select 
                    value={selectedSqliteTable}
                    onChange={(e) => {
                      setSelectedSqliteTable(e.target.value);
                      fetchSqliteTableData(selectedSqliteDb, e.target.value);
                    }}
                    className="w-full bg-[#0A0A0C] border border-white/15 text-[10px] p-1.5 rounded outline-none text-emerald-400"
                  >
                    {sqliteTables.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>
              </div>

              {/* Data Grid Render */}
              {sqliteData && (
                <div className="overflow-x-auto border border-white/10 rounded mt-3 select-text bg-[#0A0A0C]/50">
                  <table className="w-full border-collapse text-[10px] text-left">
                    <thead>
                      <tr className="bg-black/50 border-b border-white/10 text-white font-bold">
                        {sqliteData.columns.map((c: string) => (
                          <th key={c} className="p-2 border-r border-white/5 truncate max-w-[120px]">{c}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sqliteData.rows.map((row: any, idx: number) => (
                        <tr key={idx} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                          {sqliteData.columns.map((col: string) => (
                            <td key={col} className="p-2 border-r border-white/5 truncate max-w-[120px] text-gray-400" title={String(row[col])}>
                              {row[col] === null ? <i className="text-white/20">null</i> : String(row[col])}
                            </td>
                          ))}
                        </tr>
                      ))}
                      {sqliteData.rows.length === 0 && (
                        <tr>
                          <td colSpan={sqliteData.columns.length} className="p-4 text-center text-white/30 italic">
                            Tabla vacía sin registros.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Postgres Selector Block */}
          <div className="bg-black/30 border border-white/5 rounded p-3 space-y-3 shadow-lg">
            <div className="flex justify-between items-center">
              <span className="text-[10px] font-bold text-cyan-400 uppercase tracking-widest block">Base de Datos PostgreSQL Cloud (.env)</span>
              <button onClick={fetchPostgresTables} className="text-[9px] text-white/30 hover:text-white cursor-pointer">↻ CONECTAR</button>
            </div>

            {postgresError ? (
              <p className="text-[10px] text-rose-400 italic leading-relaxed">{postgresError}</p>
            ) : postgresTables.length > 0 ? (
              <div className="space-y-3">
                <div>
                  <label className="text-[8px] text-gray-500 block mb-1 uppercase">Tabla Postgres</label>
                  <select 
                    value={selectedPostgresTable}
                    onChange={(e) => {
                      setSelectedPostgresTable(e.target.value);
                      fetchPostgresTableData(e.target.value);
                    }}
                    className="w-full bg-[#0A0A0C] border border-white/15 text-[10px] p-1.5 rounded outline-none text-cyan-400"
                  >
                    {postgresTables.map(t => <option key={t} value={t}>{t}</option>)}
                  </select>
                </div>

                {/* Data Grid Render */}
                {postgresData && (
                  <div className="overflow-x-auto border border-white/10 rounded mt-3 select-text bg-[#0A0A0C]/50">
                    <table className="w-full border-collapse text-[10px] text-left">
                      <thead>
                        <tr className="bg-black/50 border-b border-white/10 text-white font-bold">
                          {postgresData.columns.map((c: string) => (
                            <th key={c} className="p-2 border-r border-white/5 truncate max-w-[120px]">{c}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {postgresData.rows.map((row: any, idx: number) => (
                          <tr key={idx} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                            {postgresData.columns.map((col: string) => (
                              <td key={col} className="p-2 border-r border-white/5 truncate max-w-[120px] text-gray-400" title={String(row[col])}>
                                {row[col] === null ? <i className="text-white/20">null</i> : String(row[col])}
                              </td>
                            ))}
                          </tr>
                        ))}
                        {postgresData.rows.length === 0 && (
                          <tr>
                            <td colSpan={postgresData.columns.length} className="p-4 text-center text-white/30 italic">
                              Tabla vacía sin registros.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-[10px] text-gray-500 italic">No se ha establecido conexión con Postgres. Presiona Conectar si configuraste DATABASE_URL en .env</p>
            )}
          </div>
        </div>
      ) : activeSubTab === 'diagram' ? (
        <div className="bg-black/30 border border-white/5 rounded p-4 shadow-lg min-h-[300px]">
          {renderDBSchemaDiagram()}
        </div>
      ) : (
        <div className="space-y-4 font-mono">
          <div className="bg-black/30 border border-white/5 rounded p-4 shadow-lg space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-[11px] font-bold text-amber-400 uppercase tracking-widest">
                Consola SQL (local_project.db)
              </span>
              <button
                onClick={executeSql}
                disabled={isExecutingSql}
                className="bg-amber-500 hover:bg-amber-600 disabled:bg-amber-800 text-black font-bold text-[10px] px-3 py-1 rounded cursor-pointer transition-colors"
              >
                {isExecutingSql ? 'EJECUTANDO...' : 'EJECUTAR QUERY'}
              </button>
            </div>
            
            <textarea
              value={sqlQuery}
              onChange={(e) => setSqlQuery(e.target.value)}
              placeholder="Escribe tu consulta SQL aquí (ej: SELECT * FROM sqlite_master WHERE type='table';)"
              className="w-full h-24 bg-[#0A0A0C] border border-white/10 p-2 text-xs text-green-400 font-mono rounded focus:outline-none focus:border-amber-500/50"
            />
            
            {sqlResult && (
              <div className="mt-4 border-t border-white/5 pt-4 space-y-2">
                <span className="text-[9px] font-bold text-gray-500 block uppercase">
                  Resultado de la Ejecución
                </span>
                
                {sqlResult.success ? (
                  sqlResult.rows && sqlResult.columns ? (
                    <div className="space-y-2">
                      <div className="text-[10px] text-emerald-400 font-semibold">
                        ✅ Query ejecutada con éxito. Filas devueltas: {sqlResult.rows.length}
                      </div>
                      
                      <div className="overflow-x-auto border border-white/10 rounded max-h-60 bg-[#0A0A0C]/50 select-text">
                        <table className="w-full border-collapse text-[10px] text-left">
                          <thead>
                            <tr className="bg-black/50 border-b border-white/10 text-white font-bold sticky top-0">
                              {sqlResult.columns.map((c: string) => (
                                <th key={c} className="p-2 border-r border-white/5 truncate max-w-[125px]">{c}</th>
                              ))}
                            </tr>
                          </thead>
                          <tbody>
                            {sqlResult.rows.map((row: any, idx: number) => (
                              <tr key={idx} className="border-b border-white/5 hover:bg-white/5 transition-colors">
                                {sqlResult.columns!.map((col: string) => (
                                  <td key={col} className="p-2 border-r border-white/5 truncate max-w-[125px] text-gray-400" title={String(row[col])}>
                                    {row[col] === null ? <i className="text-white/20">null</i> : String(row[col])}
                                  </td>
                                ))}
                              </tr>
                            ))}
                            {sqlResult.rows.length === 0 && (
                              <tr>
                                <td colSpan={sqlResult.columns.length} className="p-4 text-center text-white/30 italic">
                                  Query ejecutada con éxito pero no devolvió filas.
                                </td>
                              </tr>
                            )}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  ) : (
                    <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs rounded">
                      {sqlResult.message || '✅ Query ejecutada correctamente.'}
                    </div>
                  )
                ) : (
                  <div className="p-3 bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs rounded">
                    ❌ Error: {sqlResult.error}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
