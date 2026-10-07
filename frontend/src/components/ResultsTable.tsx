import { CheckCircle2, DatabaseZap, Inbox, Rows3 } from 'lucide-react'
import type { ExecutionResponse } from '../types'

function displayValue(value: unknown): string {
  if (value === null) return 'NULL'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

export function ResultsTable({ execution }: { execution: ExecutionResponse | null }) {
  if (!execution) {
    return (
      <section className="card results-card empty-results">
        <Inbox size={26} />
        <h3>Results will appear here</h3>
        <p>Generate a plan, review its SQL, then execute when you’re ready.</p>
      </section>
    )
  }

  const { result } = execution
  if (result.type === 'affected_rows') {
    return (
      <section className="card results-card success-result">
        <div className="success-orb"><CheckCircle2 size={23} /></div>
        <div>
          <span className="eyebrow">Execution complete</span>
          <h3>{result.affected_rows ?? 0} row{result.affected_rows === 1 ? '' : 's'} affected</h3>
          <p>{execution.operation} completed successfully{result.last_insert_id ? ` · New ID ${result.last_insert_id}` : ''}.</p>
        </div>
      </section>
    )
  }

  const rows = result.rows ?? []
  const columns = result.columns ?? (rows[0] ? Object.keys(rows[0]) : [])
  return (
    <section className="card results-card">
      <div className="results-heading">
        <div className="section-title compact">
          <span className="icon-box"><DatabaseZap size={16} /></span>
          <div><h2>Query results</h2><p>{result.row_count ?? 0} rows returned</p></div>
        </div>
        {result.truncated && <span className="limit-badge">Limited preview</span>}
      </div>
      {rows.length === 0 ? (
        <div className="table-empty"><Rows3 size={23} /><p>The query returned no rows.</p></div>
      ) : (
        <div className="table-scroll">
          <table>
            <thead><tr><th>#</th>{columns.map((column) => <th key={column}>{column}</th>)}</tr></thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={rowIndex}>
                  <td className="row-number">{rowIndex + 1}</td>
                  {columns.map((column) => (
                    <td className={row[column] === null ? 'null-value' : ''} key={column} title={displayValue(row[column])}>
                      {displayValue(row[column])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
