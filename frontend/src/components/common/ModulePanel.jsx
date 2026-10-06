/* Reserved workspace area for a module whose API is not connected yet. */
export default function ModulePanel({ title, endpoint, children }) {
  return (
    <section className="panel module">
      <header className="panel__head">
        <h2>{title}</h2>
        <span className="module__tag">NOT CONNECTED</span>
      </header>
      <div className="module__body">
        <p>{children}</p>
        <p className="mono module__endpoint">{endpoint}</p>
      </div>
    </section>
  )
}
