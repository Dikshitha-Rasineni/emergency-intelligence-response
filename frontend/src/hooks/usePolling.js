import { useCallback, useEffect, useRef, useState } from 'react'

/* Runs `fn` now and every `interval` ms. Keeps last good data on failure. */
export default function usePolling(fn, interval = 5000, key = null) {
  const [state, setState] = useState({ data: null, error: null, loading: true, updatedAt: null })
  const fnRef = useRef(fn)
  fnRef.current = fn

  const refresh = useCallback(async () => {
    try {
      const data = await fnRef.current()
      setState({ data, error: null, loading: false, updatedAt: new Date() })
    } catch (error) {
      setState((s) => ({ ...s, error, loading: false }))
    }
  }, [])

  useEffect(() => {
    setState({ data: null, error: null, loading: true, updatedAt: null })
    refresh()
    const t = setInterval(refresh, interval)
    return () => clearInterval(t)
  }, [refresh, interval, key])

  return { ...state, refresh }
}
