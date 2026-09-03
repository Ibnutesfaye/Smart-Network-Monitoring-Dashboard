import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

const WS_URL = import.meta.env.VITE_WS_URL || `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`
const HEARTBEAT_MS = 25_000
const MAX_RECONNECT_MS = 30_000

export type WebSocketState = 'connecting' | 'connected' | 'disconnected'

export function useWebSocket(path: string, onMessage?: (event: string, data: unknown) => void) {
  const queryClient = useQueryClient()
  const callbackRef = useRef(onMessage)
  const [state, setState] = useState<WebSocketState>('disconnected')

  useEffect(() => {
    callbackRef.current = onMessage
  }, [onMessage])

  useEffect(() => {
    let socket: WebSocket | null = null
    let reconnectTimer: number | undefined
    let heartbeatTimer: number | undefined
    let reconnectAttempt = 0
    let stopped = false

    const connect = () => {
      const token = localStorage.getItem('access_token')
      if (!token || stopped) return
      setState('connecting')
      socket = new WebSocket(`${WS_URL}${path}`, ['access_token', token])
      socket.onopen = () => {
        reconnectAttempt = 0
        setState('connected')
        heartbeatTimer = window.setInterval(() => {
          if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: 'ping' }))
        }, HEARTBEAT_MS)
      }
      socket.onmessage = (message) => {
        try {
          const payload = JSON.parse(message.data)
          if (payload.event === 'pong') return
          callbackRef.current?.(payload.type ?? payload.event, payload.data)
          if (payload.event === 'device.updated') queryClient.invalidateQueries({ queryKey: ['devices'] })
          if (payload.data?.event === 'device.telemetry.updated') {
            queryClient.invalidateQueries({ queryKey: ['device', String(payload.data.id)] })
            queryClient.invalidateQueries({ queryKey: ['device-telemetry', String(payload.data.id)] })
            queryClient.invalidateQueries({ queryKey: ['interfaces', String(payload.data.id)] })
          }
          if (payload.event === 'traffic.sample' || payload.event === 'dashboard.update')
            queryClient.invalidateQueries({ queryKey: ['dashboard'] })
          if (payload.event === 'alert.created') queryClient.invalidateQueries({ queryKey: ['alerts'] })
          if (payload.type?.startsWith('incident.')) {
            queryClient.invalidateQueries({ queryKey: ['incidents'] })
            queryClient.invalidateQueries({ queryKey: ['noc-summary'] })
          }
          if (payload.type?.startsWith('maintenance.')) {
            queryClient.invalidateQueries({ queryKey: ['maintenance'] })
            queryClient.invalidateQueries({ queryKey: ['noc-summary'] })
          }
        } catch {
          // Keep the connection alive if a malformed message is received.
        }
      }
      socket.onclose = (event) => {
        window.clearInterval(heartbeatTimer)
        setState('disconnected')
        if (stopped || event.code === 4401) return
        const delay = Math.min(1000 * 2 ** reconnectAttempt, MAX_RECONNECT_MS)
        reconnectAttempt += 1
        reconnectTimer = window.setTimeout(connect, delay)
      }
    }

    connect()
    return () => {
      stopped = true
      window.clearTimeout(reconnectTimer)
      window.clearInterval(heartbeatTimer)
      socket?.close(1000, 'component unmounted')
    }
  }, [path, queryClient])

  return state
}
