const colors: Record<string, string> = {
  requested: 'bg-blue-100 text-blue-700',
  searching: 'bg-indigo-100 text-indigo-700',
  assigned: 'bg-amber-100 text-amber-700',
  accepted: 'bg-teal-100 text-teal-700',
  traveling: 'bg-cyan-100 text-cyan-700',
  arrived: 'bg-cyan-100 text-cyan-700',
  inspecting: 'bg-purple-100 text-purple-700',
  quoted: 'bg-orange-100 text-orange-700',
  approved: 'bg-green-100 text-green-700',
  in_progress: 'bg-brand-100 text-brand-700',
  completed: 'bg-green-100 text-green-700',
  customer_confirmed: 'bg-green-100 text-green-800',
  closed: 'bg-gray-100 text-gray-600',
  cancelled: 'bg-red-100 text-red-700',
  disputed: 'bg-red-100 text-red-700',
}

export function StatusBadge({ status }: { status: string }) {
  return <span className={`chip ${colors[status] || 'bg-gray-100 text-gray-600'}`}>{status}</span>
}
