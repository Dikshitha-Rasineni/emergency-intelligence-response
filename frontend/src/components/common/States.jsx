export function LoadingState({ steps = ['Loading data'] }) {
  return (
    <div className="state state--loading" role="status">
      <span className="state__bar" aria-hidden="true" />
      <ul className="state__steps mono">
        {steps.map((s) => <li key={s}>{s}</li>)}
      </ul>
    </div>
  )
}

export function EmptyState({ title, children }) {
  return (
    <div className="state">
      <p className="state__title">{title}</p>
      {children && <p className="state__body">{children}</p>}
    </div>
  )
}

export function ErrorState({ title = 'Data unavailable', children, onRetry }) {
  return (
    <div className="state state--error" role="alert">
      <p className="state__title">{title}</p>
      {children && <p className="state__body">{children}</p>}
      {onRetry && <button className="btn" onClick={onRetry}>Retry</button>}
    </div>
  )
}
