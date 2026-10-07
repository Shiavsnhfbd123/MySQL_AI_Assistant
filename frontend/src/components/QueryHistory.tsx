import { CheckCircle2, Clock3, History, XCircle } from 'lucide-react'
import type { HistoryItem } from '../types'

export function QueryHistory({ items }: { items: HistoryItem[] }) {
  return (
    <aside className="history-panel">
      <div className="sidebar-heading">
        <div><span className="eyebrow">Audit trail</span><h2>Recent activity</h2></div>
        <History size={17} />
      </div>
      <div className="history-list">
        {items.length ? items.map((item) => (
          <details className="history-item" key={item.id}>
            <summary>
              <span className={item.success ? 'history-status success' : 'history-status failure'}>
                {item.success ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
              </span>
              <span className="history-summary">
                <strong>{item.instruction}</strong>
                <small><Clock3 size={11} /> {new Date(item.timestamp).toLocaleString()}</small>
              </span>
              <span className={`risk-dot risk-${item.risk.toLowerCase()}`} title={`${item.risk} risk`} />
            </summary>
            <div className="history-detail">
              <div><span>{item.operation}</span><span>{item.affected_rows ?? '—'} rows</span></div>
              <code>{item.sql}</code>
              {item.error && <p>{item.error}</p>}
            </div>
          </details>
        )) : (
          <div className="sidebar-empty"><History size={24} /><p>No query history yet</p><span>Successful and failed executions appear here.</span></div>
        )}
      </div>
    </aside>
  )
}
