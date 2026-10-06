export default function Pending({ title, endpoint }) {
  return (
    <div className="screen">
      <div className="screen-header">
        <div>
          <div className="eyebrow">MODULE</div>
          <h1>{title}</h1>
          <p className="muted">
            This module is part of the Emergency Intelligence and Response
            platform and will be connected to its backend service.
          </p>
        </div>
      </div>

      <div className="panel">
        <div className="eyebrow">STATUS</div>
        <h2>MODULE NOT CONNECTED</h2>

        {endpoint && (
          <p className="muted">
            Backend endpoint: <code>{endpoint}</code>
          </p>
        )}
      </div>
    </div>
  )
}