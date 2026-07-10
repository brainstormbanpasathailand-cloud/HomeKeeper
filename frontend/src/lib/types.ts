export interface User {
  id: number
  email: string | null
  phone: string | null
  full_name: string | null
  display_name: string | null
  avatar_url: string | null
  role: 'customer' | 'technician' | 'admin' | 'super_admin' | 'support' | 'dispatcher'
  language: string
  onboarding_completed: boolean
  email_verified: boolean
  phone_verified: boolean
}

export interface ServiceCategory {
  id: number
  slug: string
  name_th: string
  name_en: string | null
  icon: string | null
  sort_order: number
  is_active: boolean
  requires_certification: boolean
}

export interface Property {
  id: number
  owner_id: number
  name: string
  property_type: string
  address: string | null
  province: string | null
  district: string | null
  latitude: number | null
  longitude: number | null
}

export interface Asset {
  id: number
  property_id: number
  asset_category: string | null
  name: string
  brand: string | null
  model: string | null
  serial_number: string | null
  warranty_end: string | null
  next_maintenance_date: string | null
  status: string
}

export interface Job {
  id: number
  job_number: string
  customer_id: number
  service_category_id: number
  property_id: number | null
  asset_id: number | null
  urgency: string
  title: string
  problem_description: string | null
  status: string
  assigned_technician_id: number | null
  address: string | null
  created_at: string
}

export interface Quotation {
  id: number
  job_id: number
  technician_id: number
  version: number
  labor_cost: number
  total: number
  notes: string | null
  status: string
}

export interface HealthRecord {
  id: number
  job_id: number
  property_id: number | null
  asset_id: number | null
  service_date: string | null
  issue: string | null
  work_performed: string | null
  total_cost: number | null
  before_photos: string[] | null
  after_photos: string[] | null
  warranty_end: string | null
  next_maintenance_date: string | null
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface NotificationItem {
  id: number
  type: string
  title: string
  body: string | null
  is_read: boolean
}
