import { api } from './api'

/** Upload a file to the backend and return its stored URL. */
export async function uploadFile(file: File, folder = 'homekeeper'): Promise<string> {
  const fd = new FormData()
  fd.append('file', file)
  const resp = await api.post(`/uploads?folder=${encodeURIComponent(folder)}`, fd)
  return resp.data.url as string
}
