import { AlertTriangle, LoaderCircle, X } from 'lucide-react'
import { useEffect } from 'react'
import type { PreparedPlan } from '../types'

interface Props {
  plan: PreparedPlan
  loading: boolean
  onCancel: () => void
  onConfirm: () => void
}

export function ConfirmationModal({ plan, loading, onCancel, onConfirm }: Props) {
  useEffect(() => {
    const close = (event: KeyboardEvent) => event.key === 'Escape' && !loading && onCancel()
    window.addEventListener('keydown', close)
    return () => window.removeEventListener('keydown', close)
  }, [loading, onCancel])

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={(event) => event.target === event.currentTarget && !loading && onCancel()}>
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby="confirmation-title">
        <button className="modal-close" onClick={onCancel} disabled={loading} aria-label="Close"><X size={18} /></button>
        <div className="danger-orb"><AlertTriangle size={27} /></div>
        <span className={`risk-badge risk-${plan.risk.toLowerCase()}`}>{plan.risk} RISK</span>
        <h2 id="confirmation-title">Confirm database change</h2>
        <p>This operation may permanently modify data or schema. The validated plan below is immutable.</p>
        <pre><code>{plan.sql}</code></pre>
        <div className="modal-note"><AlertTriangle size={15} /><span>Review the target and WHERE clause carefully. This action cannot be undone by the assistant.</span></div>
        <div className="modal-actions">
          <button className="secondary-button" onClick={onCancel} disabled={loading}>Cancel plan</button>
          <button className="danger-button" onClick={onConfirm} disabled={loading}>
            {loading ? <LoaderCircle className="spin" size={17} /> : <AlertTriangle size={17} />}
            {loading ? 'Executing…' : 'Confirm Execution'}
          </button>
        </div>
      </div>
    </div>
  )
}
