export interface User {
  id: number
  username: string
  email: string
  role: 'administrator' | 'network_analyst'
  first_name?: string
  last_name?: string
  created_at?: string
}

export interface Device {
  id: number
  device_name: string
  hostname: string
  ip_address: string
  mac_address: string
  vendor: string
  status: 'online' | 'offline' | 'unknown' | 'degraded' | 'maintenance'
  site: number | null
  network_segment: number | null
  device_type: string
  criticality: 'low' | 'medium' | 'high' | 'critical'
  monitoring_enabled: boolean
  snmp_enabled: boolean
  snmp_version: '2c' | '3'
  snmp_status: string
  snmp_last_error_code: string
  last_seen: string | null
  last_latency_ms: number | null
  current_packet_loss: number | null
  uptime_seconds: number | null
  last_checked_at: string | null
  is_known: boolean
}

export interface Alert {
  id: number
  device: number | null
  device_name?: string
  interface: number | null
  interface_name?: string
  alert_level: 'low' | 'medium' | 'high' | 'critical'
  alert_type: string
  message: string
  acknowledged: boolean
  state: 'pending' | 'firing' | 'acknowledged' | 'resolved'
  occurrence_count: number
  recovery_count: number
  acknowledgement_note: string
  resolved_at: string | null
  maintenance_suppressed: boolean
  maintenance_window: number | null
  created_at: string
}

export interface DeviceInterface {
  id: number
  device: number
  if_index: number
  name: string
  alias: string
  admin_status: string
  oper_status: string
  speed_bps: number | null
  utilization_in_pct: number | null
  utilization_out_pct: number | null
  last_polled_at: string | null
}

export interface Site {
  id: number
  organization: number
  name: string
  code: string
  active: boolean
}

export interface DashboardMetrics {
  total_devices: number
  online_devices: number
  offline_devices: number
  active_alerts: number
  traffic_summary: { upload: number; download: number; bandwidth: number }
  network_health_score: number
  risk_score: number
  recent_activities: Array<{ action: string; description: string; created_at: string; user__username: string }>
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
