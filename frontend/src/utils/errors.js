/* Turns an Axios/FastAPI error into one readable sentence. */
export function apiErrorMessage(err) {
  if (err?.response) {
    const d = err.response.data?.detail
    if (Array.isArray(d)) return d.map((x) => `${(x.loc || []).slice(1).join('.')}: ${x.msg}`).join('; ')
    if (typeof d === 'string') return d
    return `The server responded with status ${err.response.status}.`
  }
  if (err?.request) return 'Cannot reach the backend. Check that the API is running and VITE_API_URL is correct.'
  return err?.message || 'Unexpected error.'
}
