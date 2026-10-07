export interface ColumnInfo {
  name: string
  type: string
  nullable: boolean
  primary_key: boolean
  default: unknown
  extra: string
}

export interface ForeignKeyInfo {
  column: string
  referenced_table: string
  referenced_column: string
}

export interface TableInfo {
  name: string
  type: string
  columns: ColumnInfo[]
  foreign_keys: ForeignKeyInfo[]
}

export interface SchemaResponse {
  database: string
  tables: TableInfo[]
}

export interface HealthResponse {
  status: 'ok' | 'degraded'
  database: 'connected' | 'disconnected'
  database_error: 'authentication_failed' | 'database_not_found' | 'connection_failed' | 'configuration_error' | null
  database_name: string
  ai_provider: 'ollama' | 'openrouter'
  ai_model: string
  ai_configured: boolean
  ai_connected: boolean
  ai_error: 'model_missing' | 'service_unreachable' | 'service_error' | 'invalid_response' | 'api_key_missing' | null
  ai_accelerator: 'gpu' | 'mixed' | 'cpu' | null
}

export type Risk = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface PreparedPlan {
  status: 'prepared'
  plan_id: string
  operation: string
  sql: string
  parameters: unknown[]
  explanation: string
  risk: Risk
  requires_confirmation: boolean
  executed: false
}

export interface Clarification {
  status: 'needs_clarification'
  explanation: string
  question: string
}

export interface QueryResult {
  type: 'result_set' | 'affected_rows'
  columns?: string[]
  rows?: Record<string, unknown>[]
  row_count?: number
  truncated?: boolean
  affected_rows?: number
  last_insert_id?: number | null
}

export interface ExecutionResponse {
  status: 'executed'
  plan_id: string
  operation: string
  risk: Risk
  sql: string
  result: QueryResult
  schema_changed: boolean
}

export interface HistoryItem {
  id: string
  timestamp: string
  instruction: string
  sql: string
  operation: string
  risk: Risk
  success: boolean
  affected_rows: number | null
  error: string | null
}
