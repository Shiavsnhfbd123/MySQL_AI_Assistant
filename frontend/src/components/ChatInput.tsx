import { ArrowUp, Command, LoaderCircle, Sparkles } from 'lucide-react'
import { useState, type KeyboardEvent } from 'react'

const examples = [
  'Show all students',
  'Create a students table with id, name, email and age',
  'Show top 5 students by age',
  'Count students course-wise',
  'Add Rahul age 20',
]

interface Props {
  loading: boolean
  disabled?: boolean
  onSubmit: (instruction: string) => void
}

export function ChatInput({ loading, disabled, onSubmit }: Props) {
  const [value, setValue] = useState('')

  const submit = () => {
    const instruction = value.trim()
    if (!instruction || loading || disabled) return
    onSubmit(instruction)
  }

  const onKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
      event.preventDefault()
      submit()
    }
  }

  return (
    <section className="card command-card">
      <div className="section-title">
        <span className="icon-box"><Sparkles size={16} /></span>
        <div>
          <h2>Ask your database</h2>
          <p>Plain English in. Reviewed MySQL out.</p>
        </div>
      </div>

      <div className="prompt-shell">
        <textarea
          autoFocus
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Try: give students age more than 20"
          rows={4}
          disabled={disabled}
          aria-label="Natural language database instruction"
        />
        <div className="prompt-footer">
          <span className="shortcut"><Command size={13} /> Ctrl + Enter</span>
          <button className="primary-button" onClick={submit} disabled={!value.trim() || loading || disabled}>
            {loading ? <LoaderCircle className="spin" size={17} /> : <ArrowUp size={17} />}
            {loading ? 'Planning…' : 'Generate SQL'}
          </button>
        </div>
      </div>

      <div className="suggestions" aria-label="Example prompts">
        {examples.map((example) => (
          <button key={example} onClick={() => setValue(example)} disabled={loading || disabled}>
            {example}
          </button>
        ))}
      </div>
    </section>
  )
}
