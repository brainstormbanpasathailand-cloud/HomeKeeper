import { useRef, useState } from 'react'
import { uploadFile } from '@/lib/upload'
import { useI18n } from '@/i18n'

interface Props {
  value: string[]
  onChange: (urls: string[]) => void
  max?: number
  folder?: string
}

export function MultiPhotoUpload({ value, onChange, max = 10, folder = 'jobs' }: Props) {
  const { t } = useI18n()
  const inputRef = useRef<HTMLInputElement>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const onSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    if (files.length === 0) return
    setError('')
    const room = max - value.length
    if (room <= 0) {
      setError(t('max_photos'))
      return
    }
    const toUpload = files.slice(0, room)
    setBusy(true)
    try {
      const urls: string[] = []
      for (const f of toUpload) {
        urls.push(await uploadFile(f, folder))
      }
      onChange([...value, ...urls])
      if (files.length > room) setError(t('max_photos'))
    } catch (err: any) {
      setError(err?.response?.data?.detail || t('upload_failed'))
    } finally {
      setBusy(false)
      if (inputRef.current) inputRef.current.value = ''
    }
  }

  const remove = (i: number) => onChange(value.filter((_, j) => j !== i))

  return (
    <div>
      <input ref={inputRef} type="file" accept="image/*" multiple className="hidden" onChange={onSelect} />
      <div className="grid grid-cols-4 gap-2">
        {value.map((url, i) => (
          <div key={i} className="relative">
            <img src={url} alt="" className="h-20 w-full rounded-lg object-cover" />
            <button
              type="button"
              onClick={() => remove(i)}
              className="absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-600 text-xs text-white"
              aria-label="remove"
            >
              ×
            </button>
          </div>
        ))}
        {value.length < max && (
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            disabled={busy}
            className="flex h-20 flex-col items-center justify-center gap-1 rounded-lg border border-dashed border-gray-300 text-gray-400"
          >
            <span className="text-xl">{busy ? '⏳' : '📷'}</span>
            <span className="text-[10px]">{busy ? t('uploading') : t('add_photo')}</span>
          </button>
        )}
      </div>
      <p className="mt-1 text-xs text-gray-400">
        {t('photos_hint')} · {value.length}/{max}
      </p>
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  )
}
