import { useRef, useState } from 'react'
import { uploadFile } from '@/lib/upload'

interface Props {
  label: string
  value: string | null
  onChange: (url: string) => void
  folder?: string
  required?: boolean
}

export function FileUploadField({ label, value, onChange, folder = 'homekeeper', required }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const pick = () => inputRef.current?.click()

  const onSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setBusy(true)
    setError('')
    try {
      const url = await uploadFile(file, folder)
      onChange(url)
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'อัปโหลดไม่สำเร็จ')
    } finally {
      setBusy(false)
    }
  }

  const isImage = value && !value.toLowerCase().endsWith('.pdf')

  return (
    <div>
      <label className="label">
        {label} {required && <span className="text-red-500">*</span>}
      </label>
      <input ref={inputRef} type="file" accept="image/*,application/pdf" className="hidden" onChange={onSelect} />
      <button type="button" onClick={pick} className="flex w-full items-center gap-3 rounded-xl border border-dashed border-gray-300 p-3 text-left">
        {value ? (
          isImage ? (
            <img src={value} alt="" className="h-14 w-14 rounded-lg object-cover" />
          ) : (
            <span className="flex h-14 w-14 items-center justify-center rounded-lg bg-gray-100 text-xl">📄</span>
          )
        ) : (
          <span className="flex h-14 w-14 items-center justify-center rounded-lg bg-gray-100 text-xl">📷</span>
        )}
        <span className="text-sm text-gray-500">
          {busy ? 'กำลังอัปโหลด…' : value ? 'อัปโหลดแล้ว · แตะเพื่อเปลี่ยน' : 'แตะเพื่อเลือกไฟล์'}
        </span>
      </button>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  )
}
