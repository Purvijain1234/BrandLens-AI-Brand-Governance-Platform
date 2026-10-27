import React, { useState, useEffect } from 'react'
import { FileText, Plus, ArrowUpRight, Upload, AlertCircle } from 'lucide-react'
import { apiRequest } from '../api'

interface QueueTabProps {
  currentRole: string
  onOpenDoc: (docId: string) => void
}

export default function QueueTab({ currentRole, onOpenDoc }: QueueTabProps) {
  const [items, setItems] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [newModalOpen, setNewModalOpen] = useState(false)
  const [newTitle, setNewTitle] = useState('')
  const [newType, setNewType] = useState('Social post')
  const [newChannel, setNewChannel] = useState('Instagram')
  const [newText, setNewText] = useState('')
  const [uploadFile, setUploadFile] = useState<File | null>(null)

  const loadQueue = async () => {
    setLoading(true)
    try {
      const data = await apiRequest('/content', {}, currentRole)
      setItems(data.content_items || [])
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadQueue()
  }, [currentRole])

  const handleCreate = async () => {
    try {
      if (uploadFile) {
        const formData = new FormData()
        formData.append('file', uploadFile)
        formData.append('title', newTitle || uploadFile.name)
        formData.append('content_type', newType)
        formData.append('channel', newChannel)

        const res = await apiRequest('/content/upload', {
          method: 'POST',
          body: formData,
        }, currentRole)
        setNewModalOpen(false)
        setUploadFile(null)
        setNewTitle('')
        setNewText('')
        onOpenDoc(res.content_item_id)
      } else {
        if (!newText.trim()) return
        const res = await apiRequest('/content', {
          method: 'POST',
          body: JSON.stringify({
            title: newTitle || 'Untitled post',
            type: newType,
            channel: newChannel,
            text: newText.trim(),
          })
        }, currentRole)
        setNewModalOpen(false)
        setNewTitle('')
        setNewText('')
        onOpenDoc(res.content_item_id)
      }
    } catch (e: any) {
      alert(e.message)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header and New Content Action */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">
            Pre-Publication Content Queue
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Track content governance status, review gating, and open high-severity violations.
          </p>
        </div>

        <button
          onClick={() => setNewModalOpen(true)}
          className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-brand-600 hover:bg-brand-500 text-white text-xs font-bold shadow-md shadow-brand-500/20 transition"
        >
          <Plus className="w-4 h-4" />
          New Content / Upload
        </button>
      </div>

      {/* Content Table Card */}
      <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-[#0c121c] border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 font-semibold uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3.5">Title</th>
                <th className="px-6 py-3.5">Type & Channel</th>
                <th className="px-6 py-3.5">Governance Status</th>
                <th className="px-6 py-3.5">Open Findings</th>
                <th className="px-6 py-3.5 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-6 py-8 text-center text-slate-400">
                    Loading content items...
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-slate-400">
                    No content created yet. Click &quot;+ New Content&quot; to begin.
                  </td>
                </tr>
              ) : (
                items.map((it) => (
                  <tr key={it.id} className="hover:bg-slate-50/60 dark:hover:bg-[#172230]/60 transition">
                    <td className="px-6 py-4 font-bold text-slate-900 dark:text-white">
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-brand-500 flex-shrink-0" />
                        <span className="truncate max-w-xs">{it.title}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-600 dark:text-slate-400">
                      {it.type} · <span className="font-mono text-[11px]">{it.channel || 'All'}</span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider ${
                        it.status === 'approved'
                          ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/30'
                          : it.status === 'in_review'
                          ? 'bg-amber-500/10 text-amber-500 border border-amber-500/30'
                          : it.status === 'changes_requested'
                          ? 'bg-rose-500/10 text-rose-500 border border-rose-500/30'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                      }`}>
                        {it.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-700 dark:text-slate-300">
                          {it.open_findings} open
                        </span>
                        {it.high_findings > 0 && (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20">
                            {it.high_findings} HIGH
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => onOpenDoc(it.id)}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-brand-600 hover:text-white text-slate-700 dark:text-slate-200 text-xs font-bold transition"
                      >
                        Open <ArrowUpRight className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* New Content / Upload Modal */}
      {newModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-base font-bold text-slate-900 dark:text-white">
              Create New Content for Review
            </h3>

            <div className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Title</label>
                <input
                  type="text"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Lumina Serum Product Launch"
                  className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-[#090d16] border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Content Type</label>
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-[#090d16] border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  >
                    <option>Social post</option>
                    <option>Press release</option>
                    <option>Ad copy</option>
                    <option>Blog</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">Target Channel</label>
                  <input
                    type="text"
                    value={newChannel}
                    onChange={(e) => setNewChannel(e.target.value)}
                    placeholder="Instagram / LinkedIn"
                    className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-[#090d16] border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              </div>

              {/* Upload Document or Image Option */}
              <div>
                <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Upload Document or Creative (Optional)
                </label>
                <div className="flex items-center gap-2 p-3 rounded-xl border border-dashed border-slate-300 dark:border-slate-700 bg-slate-50/50 dark:bg-[#090d16]">
                  <Upload className="w-5 h-5 text-brand-500 flex-shrink-0" />
                  <input
                    type="file"
                    accept=".docx,.pdf,.png,.jpg,.jpeg,.webp"
                    onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    className="text-xs text-slate-500 dark:text-slate-400 file:mr-2 file:py-1 file:px-2.5 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-brand-500/10 file:text-brand-600 dark:file:text-brand-400 hover:file:bg-brand-500/20"
                  />
                </div>
              </div>

              {/* Textarea if not uploading */}
              {!uploadFile && (
                <div>
                  <label className="block font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Or Paste Text Copy
                  </label>
                  <textarea
                    value={newText}
                    onChange={(e) => setNewText(e.target.value)}
                    placeholder="Draft copy to review against approved brand guidelines..."
                    className="w-full min-h-[120px] p-3 rounded-xl bg-slate-50 dark:bg-[#090d16] border border-slate-200 dark:border-slate-700 text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
                  />
                </div>
              )}
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setNewModalOpen(false)}
                className="px-4 py-2 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                onClick={handleCreate}
                className="px-4 py-2 rounded-lg text-xs font-bold text-white bg-brand-600 hover:bg-brand-500 shadow-md shadow-brand-500/20 transition"
              >
                Create & Open
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
