import type {
  Clarification,
  ExecutionResponse,
  HealthResponse,
  HistoryItem,
  PreparedPlan,
  SchemaResponse,
} from '../types'

// Empty means same-origin in production. Vite proxies /api to FastAPI during local development.
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message: string, public status: number) {
    super(message)
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...options?.headers },
    })
  } catch {
    throw new ApiError('The backend is unreachable. Make sure FastAPI is running.', 0)
  }

  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = typeof payload.detail === 'string' ? payload.detail : 'The request failed.'
    throw new ApiError(detail, response.status)
  }
  return payload as T
}

export const api = {
  health: () => request<HealthResponse>('/api/health'),
  schema: () => request<SchemaResponse>('/api/schema'),
  history: () => request<{ items: HistoryItem[] }>('/api/history'),
  plan: (instruction: string, readOnly: boolean) =>
    request<PreparedPlan | Clarification>('/api/query/plan', {
      method: 'POST',
      body: JSON.stringify({ instruction, read_only: readOnly }),
    }),
  execute: (planId: string, confirm = false) =>
    request<ExecutionResponse>('/api/query/execute', {
      method: 'POST',
      body: JSON.stringify({ plan_id: planId, confirm }),
    }),
  cancel: (planId: string) =>
    request<{ status: 'cancelled' }>('/api/query/cancel', {
      method: 'POST',
      body: JSON.stringify({ plan_id: planId }),
    }),
}
