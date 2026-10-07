import { AlertCircle, Bot, BrainCircuit, Database, LockKeyhole, ShieldCheck, Wifi, WifiOff } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'
import { api, ApiError } from './api/client'
import { ChatInput } from './components/ChatInput'
import { ConfirmationModal } from './components/ConfirmationModal'
import { QueryHistory } from './components/QueryHistory'
import { ResultsTable } from './components/ResultsTable'
import { SchemaExplorer } from './components/SchemaExplorer'
import { SqlPreview } from './components/SqlPreview'
import type { ExecutionResponse, HealthResponse, HistoryItem, PreparedPlan, SchemaResponse } from './types'

function errorMessage(error: unknown) {
  return error instanceof ApiError || error instanceof Error ? error.message : 'Something went wrong.'
}

function databaseSetupMessage(health: HealthResponse) {
  if (health.database_error === 'authentication_failed') {
    return 'MySQL rejected the application credentials. Check MYSQL_URL or the MYSQL_* secrets, then run the database setup utility when using local MySQL.'
  }
  if (health.database_error === 'database_not_found') {
    return `Database “${health.database_name}” does not exist. Create it with your managed provider or run the local database setup utility.`
  }
  if (health.database_error === 'configuration_error') {
    return 'The MySQL configuration is invalid. MYSQL_URL must use mysql:// and include a user, host, and database.'
  }
  return 'MySQL is unreachable. Confirm the managed-database network, MYSQL_URL, or individual MYSQL_* settings.'
}

function aiSetupMessage(health: HealthResponse) {
  if (health.ai_provider === 'ollama') {
    if (health.ai_error === 'model_missing') return `Model ${health.ai_model} is missing. Run: ollama pull ${health.ai_model}`
    if (health.ai_error === 'service_unreachable') return 'Ollama is not running. Start Ollama from the Start menu or run ollama serve.'
    return 'The local Ollama service returned an error. Check the Ollama server log.'
  }
  return 'Add OPENROUTER_API_KEY to backend/.env, then restart FastAPI.'
}

export default function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [schema, setSchema] = useState<SchemaResponse | null>(null)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const [plan, setPlan] = useState<PreparedPlan | null>(null)
  const [execution, setExecution] = useState<ExecutionResponse | null>(null)
  const [clarification, setClarification] = useState<string | null>(null)
  const [readOnly, setReadOnly] = useState(true)
  const [planning, setPlanning] = useState(false)
  const [executing, setExecuting] = useState(false)
  const [schemaLoading, setSchemaLoading] = useState(true)
  const [showConfirmation, setShowConfirmation] = useState(false)

  const loadHealth = useCallback(async () => {
    try { setHealth(await api.health()) }
    catch { setHealth({ status: 'degraded', database: 'disconnected', database_error: 'connection_failed', database_name: 'unknown', ai_provider: 'ollama', ai_model: 'qwen2.5:3b', ai_configured: false, ai_connected: false, ai_error: 'service_unreachable', ai_accelerator: null }) }
  }, [])

  const loadSchema = useCallback(async (notify = false) => {
    setSchemaLoading(true)
    try {
      setSchema(await api.schema())
      if (notify) toast.success('Schema refreshed')
    } catch (error) {
      if (notify) toast.error(errorMessage(error))
    } finally { setSchemaLoading(false) }
  }, [])

  const loadHistory = useCallback(async () => {
    try { setHistory((await api.history()).items) }
    catch { /* history is non-critical */ }
  }, [])

  useEffect(() => {
    void loadHealth()
    void loadSchema()
    void loadHistory()
  }, [loadHealth, loadHistory, loadSchema])

  const generate = async (instruction: string) => {
    setPlanning(true)
    setPlan(null)
    setExecution(null)
    setClarification(null)
    try {
      const response = await api.plan(instruction, readOnly)
      if (response.status === 'needs_clarification') {
        setClarification(response.question || response.explanation)
        toast.info('The assistant needs more detail')
      } else {
        setPlan(response)
        toast.success('SQL plan generated and validated')
        await loadHealth()
      }
    } catch (error) { toast.error(errorMessage(error)) }
    finally { setPlanning(false) }
  }

  const runPlan = async (confirm = false) => {
    if (!plan) return
    setExecuting(true)
    try {
      const response = await api.execute(plan.plan_id, confirm)
      setExecution(response)
      setShowConfirmation(false)
      toast.success('Query executed successfully')
      await loadHistory()
      if (response.schema_changed) await loadSchema()
    } catch (error) { toast.error(errorMessage(error)) }
    finally { setExecuting(false) }
  }

  const executeOrReview = () => {
    if (!plan) return
    if (plan.requires_confirmation) setShowConfirmation(true)
    else void runPlan(false)
  }

  const cancelPlan = async () => {
    if (!plan) return
    try { await api.cancel(plan.plan_id) }
    catch { /* an expired plan is already effectively cancelled */ }
    setShowConfirmation(false)
    setPlan(null)
    toast.info('Pending plan cancelled')
  }

  const databaseConnected = health?.database === 'connected'
  const aiReady = Boolean(health?.ai_configured && health?.ai_connected)
  const available = databaseConnected && aiReady

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark"><Database size={21} /></span>
          <div><strong>QueryPilot</strong><span>MySQL AI Assistant</span></div>
        </div>
        <div className="topbar-actions">
          <label className={`readonly-toggle ${readOnly ? 'active' : ''}`}>
            <LockKeyhole size={15} />
            <span>Read Only</span>
            <input type="checkbox" checked={readOnly} onChange={(event) => setReadOnly(event.target.checked)} />
            <i />
          </label>
          <span className={`connection-pill ${aiReady ? 'online' : 'offline'}`}>
            <BrainCircuit size={14} />
            {health ? `${health.ai_model}${health.ai_accelerator ? ` · ${health.ai_accelerator.toUpperCase()}` : ''}` : 'Checking AI'}
          </span>
          <span className={`connection-pill ${databaseConnected ? 'online' : 'offline'}`}>
            {databaseConnected ? <Wifi size={14} /> : <WifiOff size={14} />}
            {health ? (databaseConnected ? 'Database connected' : 'Database offline') : 'Checking connection'}
          </span>
        </div>
      </header>

      <div className="workspace-grid">
        <SchemaExplorer schema={schema} loading={schemaLoading} onRefresh={() => void loadSchema(true)} />

        <main className="main-content">
          <div className="hero-copy">
            <div><span className="eyebrow"><Bot size={13} /> Schema-aware copilot</span><h1>Talk to MySQL.<br /><em>Stay in control.</em></h1></div>
            <p>Turn rough ideas into reviewed, parameterized SQL. Every query passes backend validation before it can reach your database.</p>
          </div>

          {health && !available && (
            <div className="setup-alert">
              <AlertCircle size={18} />
              <div><strong>Setup required</strong><span>{!databaseConnected ? databaseSetupMessage(health) : aiSetupMessage(health)}</span></div>
            </div>
          )}

          <ChatInput loading={planning} disabled={health !== null && !available} onSubmit={(instruction) => void generate(instruction)} />

          {clarification && (
            <div className="clarification-card"><Bot size={20} /><div><span className="eyebrow">Clarification needed</span><p>{clarification}</p></div></div>
          )}

          {plan && <SqlPreview plan={plan} executing={executing} onExecute={executeOrReview} />}
          <ResultsTable execution={execution} />

          <div className="security-strip">
            <ShieldCheck size={17} /><span>Credentials stay server-side</span><i />
            <span>SQLGlot validation</span><i /><span>Immutable execution plans</span>
          </div>
        </main>

        <QueryHistory items={history} />
      </div>

      {showConfirmation && plan && (
        <ConfirmationModal plan={plan} loading={executing} onCancel={() => void cancelPlan()} onConfirm={() => void runPlan(true)} />
      )}
    </div>
  )
}
