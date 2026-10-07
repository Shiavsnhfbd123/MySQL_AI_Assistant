import { Check, Clipboard, LoaderCircle, Play, ShieldAlert } from 'lucide-react'
import { useState } from 'react'
import type { PreparedPlan } from '../types'

const keywords = new Set([
  'SELECT', 'FROM', 'WHERE', 'INSERT', 'INTO', 'VALUES', 'UPDATE', 'SET', 'DELETE',
  'CREATE', 'TABLE', 'ALTER', 'DROP', 'TRUNCATE', 'JOIN', 'LEFT', 'RIGHT', 'INNER',
  'ON', 'AND', 'OR', 'NOT', 'NULL', 'AS', 'ORDER', 'BY', 'GROUP', 'LIMIT', 'HAVING',
  'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES', 'INDEX', 'VIEW', 'COUNT', 'DESC', 'ASC',
])

function HighlightedSql({ sql }: { sql: string }) {
  const tokens = sql.split(/(\s+|[,();])/)
  return (
    <code>{tokens.map((token, index) => (
      <span className={keywords.has(token.toUpperCase()) ? 'sql-keyword' : /^%s$/i.test(token) ? 'sql-parameter' : ''} key={`${token}-${index}`}>
        {token}
      </span>
    ))}</code>
  )
}

interface Props {
  plan: PreparedPlan
  executing: boolean
  onExecute: () => void
}

export function SqlPreview({ plan, executing, onExecute }: Props) {
  const [copied, setCopied] = useState(false)
  const copy = async () => {
    await navigator.clipboard.writeText(plan.sql)
    setCopied(true)
    window.setTimeout(() => setCopied(false), 1500)
  }

  return (
    <section className="card sql-card">
      <div className="sql-heading">
        <div>
          <span className="eyebrow">AI interpretation</span>
          <h2>{plan.explanation}</h2>
        </div>
        <div className="badge-row">
          <span className="operation-badge">{plan.operation}</span>
          <span className={`risk-badge risk-${plan.risk.toLowerCase()}`}>{plan.risk}</span>
        </div>
      </div>

      <div className="code-window">
        <div className="code-toolbar">
          <div className="window-dots"><i /><i /><i /></div>
          <span>generated.sql</span>
          <button onClick={copy}>{copied ? <Check size={14} /> : <Clipboard size={14} />}{copied ? 'Copied' : 'Copy'}</button>
        </div>
        <pre><HighlightedSql sql={plan.sql} /></pre>
        {plan.parameters.length > 0 && (
          <div className="parameter-bar">
            <span>Bound parameters</span>
            {plan.parameters.map((parameter, index) => <code key={index}>${index + 1}: {String(parameter)}</code>)}
          </div>
        )}
      </div>

      <div className="sql-actions">
        <div className={plan.requires_confirmation ? 'warning-copy' : 'safe-copy'}>
          {plan.requires_confirmation ? <ShieldAlert size={17} /> : <Check size={17} />}
          <span>{plan.requires_confirmation ? 'This operation needs explicit confirmation.' : 'Validated and ready to execute.'}</span>
        </div>
        <button className={plan.requires_confirmation ? 'danger-button' : 'primary-button'} onClick={onExecute} disabled={executing}>
          {executing ? <LoaderCircle className="spin" size={17} /> : plan.requires_confirmation ? <ShieldAlert size={17} /> : <Play size={17} />}
          {executing ? 'Executing…' : plan.requires_confirmation ? 'Review & Confirm' : 'Execute Query'}
        </button>
      </div>
    </section>
  )
}
