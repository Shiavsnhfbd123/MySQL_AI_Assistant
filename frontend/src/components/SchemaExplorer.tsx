import { ChevronDown, ChevronRight, Database, KeyRound, Link2, RefreshCw, Table2 } from 'lucide-react'
import { useState } from 'react'
import type { SchemaResponse } from '../types'

interface Props {
  schema: SchemaResponse | null
  loading: boolean
  onRefresh: () => void
}

export function SchemaExplorer({ schema, loading, onRefresh }: Props) {
  const [openTables, setOpenTables] = useState<Set<string>>(new Set())

  const toggle = (name: string) => {
    setOpenTables((current) => {
      const next = new Set(current)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }

  return (
    <aside className="schema-panel">
      <div className="sidebar-heading">
        <div>
          <span className="eyebrow">Workspace</span>
          <h2>Schema Explorer</h2>
        </div>
        <button className="icon-button" onClick={onRefresh} title="Refresh schema" aria-label="Refresh schema">
          <RefreshCw className={loading ? 'spin' : ''} size={16} />
        </button>
      </div>

      <div className="database-name">
        <Database size={16} />
        <span>{schema?.database ?? 'No database'}</span>
        <span className="count-badge">{schema?.tables.length ?? 0}</span>
      </div>

      <div className="schema-tree">
        {loading && !schema ? (
          <div className="skeleton-stack">{[1, 2, 3].map((item) => <div className="skeleton" key={item} />)}</div>
        ) : schema?.tables.length ? (
          schema.tables.map((table) => {
            const open = openTables.has(table.name)
            return (
              <div className="tree-table" key={table.name}>
                <button className="tree-table-button" onClick={() => toggle(table.name)}>
                  {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  <Table2 size={14} className="table-icon" />
                  <span>{table.name}</span>
                  <small>{table.columns.length}</small>
                </button>
                {open && (
                  <div className="column-list">
                    {table.columns.map((column) => {
                      const foreign = table.foreign_keys.some((key) => key.column === column.name)
                      return (
                        <div className="column-row" key={column.name}>
                          {column.primary_key ? <KeyRound size={12} className="key-icon" /> : foreign ? <Link2 size={12} /> : <span className="column-dot" />}
                          <span title={column.name}>{column.name}</span>
                          <small title={column.type}>{column.type}</small>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })
        ) : (
          <div className="sidebar-empty">
            <Table2 size={24} />
            <p>No tables found</p>
            <span>Create one with the assistant.</span>
          </div>
        )}
      </div>
      <div className="schema-legend">
        <span><KeyRound size={11} /> Primary key</span>
        <span><Link2 size={11} /> Foreign key</span>
      </div>
    </aside>
  )
}
