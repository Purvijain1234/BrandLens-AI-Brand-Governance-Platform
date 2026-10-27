import React, { useState, useEffect } from 'react'
import {
  Sparkles,
  ShieldAlert,
  ShieldCheck,
  Check,
  X,
  Edit2,
  Send,
  MessageSquare,
  History,
  FileCheck2,
  Lock,
  Eye,
  AlertTriangle,
  Upload,
  Info
} from 'lucide-react'
import { apiRequest } from '../api'
import ClauseModal from './ClauseModal'

interface ReviewTabProps {
  currentRole: string
  activeDocId: string | null
  onDocChange: (id: string) => void
}

export default function ReviewTab({ currentRole, activeDocId, onDocChange }: ReviewTabProps) {
  const [doc, setDoc] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [activeView, setActiveView] = useState<'editor' | 'highlight'>('highlight')
  const [rulesOnly, setRulesOnly] = useState(false)
  const [confidentialMode, setConfidentialMode] = useState(false)
  const [hasImage, setHasImage] = useState(true)
  const [altText, setAltText] = useState('')
  const [fgColor, setFgColor] = useState('#9aa6b2')
  const [bgColor, setBgColor] = useState('#ffffff')
  const [contentTitle, setContentTitle] = useState('')
  const [contentType, setContentType] = useState('Social post')
  const [contentText, setContentText] = useState('')
  const [commentInput, setCommentInput] = useState('')
  const [dismissModal, setDismissModal] = useState<{ open: boolean; findingId: string | null }>({ open: false, findingId: null })
  const [dismissReason, setDismissReason] = useState('')
  const [editModal, setEditModal] = useState<{ open: boolean; findingId: string | null; initialFix: string }>({ open: false, findingId: null, initialFix: '' })
  const [customFixInput, setCustomFixInput] = useState('')
  const [clauseModal, setClauseModal] = useState<{ open: boolean; id: string | null; info: any | null }>({ open: false, id: null, info: null })
  const [aiDisclosure, setAiDisclosure] = useState<any>(null)
  const [notification, setNotification] = useState<{ text: string; type: 'success' | 'error' } | null>(null)

  const showNotification = (text: string, type: 'success' | 'error' = 'success') => {
    setNotification({ text, type })
    setTimeout(() => setNotification(null), 4000)
  }

  // Load active document or default to first
  const loadDoc = async (id?: string) => {
    setLoading(true)
    try {
      if (!id) {
        const q = await apiRequest('/content', {}, currentRole)
        if (q.content_items && q.content_items.length > 0) {
          id = q.content_items[0].id
        }
      }
      if (id) {
        onDocChange(id)
        const d = await apiRequest(`/content/${id}`, {}, currentRole)
        setDoc(d)
        setContentTitle(d.item.title)
        setContentType(d.item.type)
        setContentText(d.latest_version?.text || '')
        
        // Fetch AI disclosure
        try {
          const disc = await apiRequest(`/ai-disclosure/${id}`, {}, currentRole)
          setAiDisclosure(disc)
        } catch (e) {
          // Disclosure not ready yet
        }
      }
    } catch (e: any) {
      showNotification(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDoc(activeDocId || undefined)
  }, [activeDocId, currentRole])

  // Run Brand Review
  const handleRunReview = async () => {
    if (!doc?.item?.id) return
    setLoading(true)
    try {
      const res = await apiRequest(`/content/${doc.item.id}/review`, {
        method: 'POST',
        body: JSON.stringify({
          rules_only: rulesOnly,
          confidential_mode: confidentialMode,
          has_image: hasImage,
          alt_text: altText,
          fg_color: fgColor,
          bg_color: bgColor,
        })
      }, currentRole)
      showNotification(`Review completed: ${res.result.findings.length} findings analyzed.`)
      await loadDoc(doc.item.id)
    } catch (e: any) {
      showNotification(e.message, 'error')
    } finally {
      setLoading(false)
    }
  }

  // Accept Fix
  const handleAcceptFix = async (findingId: string, customText?: string) => {
    try {
      await apiRequest(`/findings/${findingId}/accept`, {
        method: 'POST',
        body: JSON.stringify({ custom_fix: customText || null })
      }, currentRole)
      showNotification('Fix applied and new version recorded.')
      await loadDoc(doc.item.id)
    } catch (e: any) {
      showNotification(e.message, 'error')
    }
  }

  // Dismiss Finding
  const handleDismissFinding = async () => {
    if (!dismissModal.findingId || !dismissReason.trim()) {
      showNotification('A reason is required to dismiss a brand finding.', 'error')
      return
    }
    try {
      await apiRequest(`/findings/${dismissModal.findingId}/dismiss`, {
        method: 'POST',
        body: JSON.stringify({ reason: dismissReason.trim() })
      }, currentRole)
      showNotification('Finding dismissed with audit trail record.')
      setDismissModal({ open: false, findingId: null })
      setDismissReason('')
      await loadDoc(doc.item.id)
    } catch (e: any) {
      showNotification(e.message, 'error')
    }
  }

  // Submit for Review
  const handleSubmitForReview = async () => {
    if (!doc?.item?.id) return
    try {
      await apiRequest(`/content/${doc.item.id}/submit`, { method: 'POST' }, currentRole)
      showNotification('Document submitted for approval.')
      await loadDoc(doc.item.id)
    } catch (e: any) {
      showNotification(e.message, 'error')
    }
  }

  // Approve Document
  const handleApprove = async () => {
    if (!doc?.item?.id) return
    try {
      await apiRequest(`/content/${doc.item.id}/approve`, {
        method: 'POST',
        body: JSON.stringify({ reason: 'All high-severity and brand checks resolved.' })
      }, currentRole)
      showNotification('Document approved with signed compliance certificate!')
      await loadDoc(doc.item.id)
    } catch (e: any) {
      showNotification(e.message, 'error')
    }
  }

  // Request Changes
  const handleRequestChanges = async () => {
    if (!doc?.item?.id) return
    const reason = prompt('Specify requested changes for creator:')
    if (!reason) return
    try {
      await apiRequest(`/content/${doc.item.id}/request-changes`, {
        method: 'POST',
        body: JSON.stringify({ reason })
      }, currentRole)
      showNotification('Changes requested and sent to creator.')
      await loadDoc(doc.item.id)
    } catch (e: any) {
      showNotification(e.message, 'error')
    }
  }

  // Add Comment
  const handleAddComment = async () => {
    if (!doc?.item?.id || !commentInput.trim()) return
    try {
      await apiRequest(`/content/${doc.item.id}/comments`, {
        method: 'POST',
        body: JSON.stringify({ body: commentInput.trim() })
      }, currentRole)
      setCommentInput('')
      await loadDoc(doc.item.id)
    } catch (e: any) {
      showNotification(e.message, 'error')
    }
  }

  // Inspect Clause Modal
  const inspectClause = async (clauseId: string) => {
    try {
      const q = await apiRequest('/clauses', {}, currentRole)
      const found = q.clauses?.find((c: any) => c.id === clauseId)
      setClauseModal({ open: true, id: clauseId, info: found || null })
    } catch (e) {
      setClauseModal({ open: true, id: clauseId, info: null })
    }
  }

  // Highlight generator
  const renderHighlightedContent = () => {
    if (!doc?.latest_version?.text) return null
    const text = doc.latest_version.text
    const openFindings = (doc.findings || [])
      .filter((f: any) => f.state === 'open' && f.span_end > f.span_start)
      .sort((a: any, b: any) => a.span_start - b.span_start)

    if (openFindings.length === 0) {
      return <span>{text}</span>
    }

    const segments: React.ReactNode[] = []
    let cursor = 0

    openFindings.forEach((f: any, idx: number) => {
      if (f.span_start > cursor) {
        segments.push(<span key={`text-${cursor}`}>{text.slice(cursor, f.span_start)}</span>)
      }
      if (f.span_start >= cursor) {
        const markClass = f.severity === 'high' ? 'high' : f.severity === 'med' ? 'med' : 'low'
        segments.push(
          <mark
            key={`mark-${idx}`}
            className={`${markClass} cursor-pointer hover:opacity-80 transition`}
            title={`[${f.source_id}] ${f.category}: ${f.message}`}
            onClick={() => inspectClause(f.source_id)}
          >
            {text.slice(f.span_start, f.span_end)}
          </mark>
        )
        cursor = f.span_end
      }
    })

    if (cursor < text.length) {
      segments.push(<span key={`text-end`}>{text.slice(cursor)}</span>)
    }

    return segments
  }

  const openFindingsCount = (doc?.findings || []).filter((f: any) => f.state === 'open').length
  const highOpenCount = (doc?.findings || []).filter((f: any) => f.state === 'open' && f.severity === 'high').length
  const isCreator = currentRole.toLowerCase() === 'creator'
  const isReviewerOrManager = ['reviewer', 'manager', 'admin'].includes(currentRole.toLowerCase())
  const isApproved = doc?.item?.status === 'approved'
  const canEditDoc = isCreator && ['draft', 'changes_requested'].includes(doc?.item?.status)

  return (
    <div className="space-y-6">
      {/* Toast Notification */}
      {notification && (
        <div className={`fixed bottom-6 right-6 z-50 px-4 py-3 rounded-xl shadow-xl flex items-center gap-3 text-xs font-semibold animate-in slide-in-from-bottom duration-200 ${
          notification.type === 'error' ? 'bg-rose-600 text-white' : 'bg-emerald-600 text-white'
        }`}>
          {notification.type === 'error' ? <ShieldAlert className="w-4 h-4" /> : <ShieldCheck className="w-4 h-4" />}
          <span>{notification.text}</span>
        </div>
      )}

      {/* Top Document Status Banner */}
      <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-500/10 text-brand-600 dark:text-brand-400 flex items-center justify-center">
            <FileCheck2 className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-900 dark:text-white">
                {contentTitle || 'Untitled content'}
              </h2>
              <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider ${
                doc?.item?.status === 'approved'
                  ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/30'
                  : doc?.item?.status === 'in_review'
                  ? 'bg-amber-500/10 text-amber-500 border border-amber-500/30'
                  : doc?.item?.status === 'changes_requested'
                  ? 'bg-rose-500/10 text-rose-500 border border-rose-500/30'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
              }`}>
                {doc?.item?.status || 'Draft'}
              </span>
            </div>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              {contentType} · Version {doc?.latest_version?.n || 1} · Created by {doc?.item?.created_by || 'Creator'}
            </p>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 flex-wrap">
          {canEditDoc && (
            <button
              onClick={handleSubmitForReview}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-semibold transition"
            >
              <Send className="w-3.5 h-3.5" />
              Submit for Approval
            </button>
          )}

          {doc?.item?.status === 'in_review' && isReviewerOrManager && (
            <>
              <button
                onClick={handleRequestChanges}
                className="px-3 py-1.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 hover:bg-rose-500/20 text-xs font-semibold transition"
              >
                Request Changes
              </button>

              <button
                onClick={handleApprove}
                disabled={highOpenCount > 0}
                className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-bold text-white transition shadow-sm ${
                  highOpenCount > 0
                    ? 'bg-slate-400 cursor-not-allowed opacity-60'
                    : 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-600/20'
                }`}
                title={highOpenCount > 0 ? 'Blocked: unresolved high-severity findings' : 'Sign off on publication'}
              >
                <Check className="w-4 h-4" />
                Sign-off & Approve
              </button>
            </>
          )}

          {isApproved && (
            <span className="flex items-center gap-1.5 text-xs font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg">
              <Check className="w-4 h-4" /> Approved for Publication
            </span>
          )}
        </div>
      </div>

      {/* Main Grid: Left Reviewer / Editor & Right Findings */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Content Editor & Visual Tools (7 cols) */}
        <div className="lg:col-span-7 space-y-5">
          {/* Editor Header & Tabs */}
          <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setActiveView('highlight')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                    activeView === 'highlight'
                      ? 'bg-brand-600 text-white'
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                >
                  Grounded Highlight View
                </button>
                <button
                  onClick={() => setActiveView('editor')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${
                    activeView === 'editor'
                      ? 'bg-brand-600 text-white'
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800'
                  }`}
                >
                  Raw Content Editor
                </button>
              </div>

              <div className="text-xs text-slate-500 dark:text-slate-400">
                Word Count: <span className="font-semibold">{contentText.split(/\s+/).filter(Boolean).length}</span>
              </div>
            </div>

            {/* Display Area */}
            {activeView === 'highlight' ? (
              <div className="min-h-[160px] p-4 rounded-xl bg-slate-50 dark:bg-[#090d16] border border-slate-200 dark:border-slate-800/80 text-sm leading-relaxed whitespace-pre-wrap font-sans text-slate-800 dark:text-slate-200">
                {renderHighlightedContent()}
              </div>
            ) : (
              <textarea
                value={contentText}
                onChange={(e) => setContentText(e.target.value)}
                disabled={!canEditDoc}
                className="w-full min-h-[160px] p-4 rounded-xl bg-slate-50 dark:bg-[#090d16] border border-slate-200 dark:border-slate-800 text-sm text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 font-sans"
                placeholder="Paste or type content to review..."
              />
            )}

            {/* Creative & Image Metadata Card */}
            <div className="p-4 rounded-xl bg-slate-50/80 dark:bg-[#0c121c] border border-slate-200/80 dark:border-slate-800/80 space-y-3">
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={hasImage}
                    onChange={(e) => setHasImage(e.target.checked)}
                    className="rounded text-brand-600 focus:ring-brand-500"
                  />
                  <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">Post includes creative image asset</span>
                </label>
                <span className="text-[11px] font-mono text-slate-400">WCAG AA Standard</span>
              </div>

              {hasImage && (
                <div className="space-y-3 pt-2">
                  <input
                    type="text"
                    value={altText}
                    onChange={(e) => setAltText(e.target.value)}
                    placeholder="Descriptive Alt-Text for Screen Readers (Clause A-01)..."
                    className="w-full px-3 py-2 rounded-lg bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-700 text-xs text-slate-800 dark:text-slate-200 focus:ring-2 focus:ring-brand-500 focus:outline-none"
                  />

                  <div className="flex flex-wrap items-center gap-4 text-xs">
                    <label className="flex items-center gap-2">
                      <span className="text-slate-500 dark:text-slate-400">Text Colour:</span>
                      <input
                        type="color"
                        value={fgColor}
                        onChange={(e) => setFgColor(e.target.value)}
                        className="w-7 h-7 rounded border border-slate-300 dark:border-slate-700 cursor-pointer"
                      />
                      <span className="font-mono text-[11px] text-slate-600 dark:text-slate-300">{fgColor}</span>
                    </label>

                    <label className="flex items-center gap-2">
                      <span className="text-slate-500 dark:text-slate-400">Background:</span>
                      <input
                        type="color"
                        value={bgColor}
                        onChange={(e) => setBgColor(e.target.value)}
                        className="w-7 h-7 rounded border border-slate-300 dark:border-slate-700 cursor-pointer"
                      />
                      <span className="font-mono text-[11px] text-slate-600 dark:text-slate-300">{bgColor}</span>
                    </label>

                    <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-slate-200 dark:bg-slate-800 text-[11px] font-semibold">
                      <span>Palette Check (V-01):</span>
                      <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: fgColor }}></span>
                      <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: bgColor }}></span>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Pipeline Configuration Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
              <div className="flex items-center gap-4">
                <label className="flex items-center gap-2 cursor-pointer text-xs" title="Redacts confidential codenames and figures before external AI transmission">
                  <input
                    type="checkbox"
                    checked={confidentialMode}
                    onChange={(e) => setConfidentialMode(e.target.checked)}
                    className="rounded text-brand-600 focus:ring-brand-500"
                  />
                  <span className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1">
                    <Lock className="w-3.5 h-3.5 text-amber-500" />
                    Confidential Mode
                  </span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-xs" title="Uses local deterministic rule engine only (skips external LLM)">
                  <input
                    type="checkbox"
                    checked={rulesOnly}
                    onChange={(e) => setRulesOnly(e.target.checked)}
                    className="rounded text-brand-600 focus:ring-brand-500"
                  />
                  <span className="font-semibold text-slate-700 dark:text-slate-300">
                    Rules Only (No External AI)
                  </span>
                </label>
              </div>

              <button
                onClick={handleRunReview}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-brand-600 to-teal-500 hover:from-brand-500 hover:to-teal-400 text-white font-bold text-xs shadow-md shadow-brand-500/20 transition disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4" />
                {loading ? 'Evaluating Brand Policies...' : 'Run Brand Review'}
              </button>
            </div>
          </div>

          {/* AI Disclosure & Transparency Panel */}
          {aiDisclosure && (
            <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                  <ShieldCheck className="w-4 h-4 text-brand-500" />
                  AI Disclosure & Transparency Ledger
                </div>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-brand-500/10 text-brand-500 font-semibold">
                  {aiDisclosure.rules_only ? 'Deterministic (Zero External AI)' : `${aiDisclosure.total_ai_calls} Grounded Calls`}
                </span>
              </div>

              <p className="text-xs text-slate-600 dark:text-slate-400">
                {aiDisclosure.privacy_status}
              </p>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-1">
                <div className="bg-slate-50 dark:bg-[#090d16] p-3 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="font-bold text-slate-700 dark:text-slate-300 block mb-1">
                    Deterministic Rule Checks (L1)
                  </span>
                  <ul className="space-y-1 text-slate-500 dark:text-slate-400 list-disc list-inside text-[11px]">
                    <li>Claims regex patterns (C-01, C-02, C-03)</li>
                    <li>Approved terminology dictionary (T-01, T-02)</li>
                    <li>Fact price comparison (F-014)</li>
                    <li>Voice exclamation & shouting (R-02, R-03)</li>
                    <li>WCAG 4.5:1 Contrast & Alt Text (A-01, A-02)</li>
                  </ul>
                </div>

                <div className="bg-slate-50 dark:bg-[#090d16] p-3 rounded-xl border border-slate-200/60 dark:border-slate-800">
                  <span className="font-bold text-slate-700 dark:text-slate-300 block mb-1">
                    External AI Reliability Layer (L2-L4)
                  </span>
                  <ul className="space-y-1 text-slate-500 dark:text-slate-400 list-disc list-inside text-[11px]">
                    <li>Hybrid clause retrieval (BM25 + Cosine)</li>
                    <li>Pydantic structured output validation</li>
                    <li>Verbatim quote verification invariant</li>
                    <li>Source hallucination rejection filter</li>
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Findings Deck, Approval Gate, Comments, Versions (5 cols) */}
        <div className="lg:col-span-5 space-y-5">
          {/* Findings Deck */}
          <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Governance Findings
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  {openFindingsCount} open · {highOpenCount} high severity
                </p>
              </div>

              {highOpenCount > 0 && (
                <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-rose-500/10 text-rose-600 dark:text-rose-400 border border-rose-500/20 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" /> High Risk Blocking
                </span>
              )}
            </div>

            {/* Findings List */}
            <div className="space-y-3 max-h-[480px] overflow-y-auto pr-1">
              {(doc?.findings || []).length === 0 ? (
                <div className="py-8 text-center text-xs text-slate-400">
                  No policy issues raised yet. Click &quot;Run Brand Review&quot; above.
                </div>
              ) : (
                doc.findings.map((f: any) => {
                  const isOpen = f.state === 'open'
                  const isHigh = f.severity === 'high'

                  return (
                    <div
                      key={f.id}
                      className={`p-3.5 rounded-xl border text-xs transition space-y-2 ${
                        isOpen
                          ? isHigh
                            ? 'bg-rose-50/50 dark:bg-rose-950/20 border-rose-200 dark:border-rose-900/60'
                            : 'bg-amber-50/50 dark:bg-amber-950/20 border-amber-200 dark:border-amber-900/60'
                          : 'bg-slate-50 dark:bg-[#0c121c] border-slate-200 dark:border-slate-800 opacity-70'
                      }`}
                    >
                      {/* Badge row */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1.5">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-extrabold uppercase ${
                            isHigh
                              ? 'bg-rose-600 text-white'
                              : f.severity === 'med'
                              ? 'bg-amber-500 text-white'
                              : 'bg-slate-400 text-white'
                          }`}>
                            {f.severity}
                          </span>
                          <span className="font-bold text-slate-800 dark:text-slate-200">{f.category}</span>
                        </div>

                        <div className="flex items-center gap-1">
                          <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-400">
                            {f.origin.toUpperCase()}
                          </span>
                          <span className="text-[10px] text-slate-400">conf: {f.confidence}</span>
                        </div>
                      </div>

                      {/* Message & Quoted Text */}
                      <p className="text-slate-700 dark:text-slate-300 leading-normal">
                        {f.message}
                      </p>

                      {/* Source Citation */}
                      <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
                        <span>Source:</span>
                        <button
                          onClick={() => inspectClause(f.source_id)}
                          className="font-mono font-bold text-brand-600 dark:text-brand-400 hover:underline flex items-center gap-1"
                        >
                          {f.source_id} <Info className="w-3 h-3" />
                        </button>
                      </div>

                      {/* Suggested Diff Preview */}
                      {f.suggested_fix && (
                        <div className="p-2 rounded-lg bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 font-mono text-[11px] space-y-0.5">
                          {f.quoted_text && (
                            <div className="text-rose-600 dark:text-rose-400 line-through">
                              - {f.quoted_text}
                            </div>
                          )}
                          <div className="text-emerald-600 dark:text-emerald-400 font-bold">
                            + {f.suggested_fix}
                          </div>
                        </div>
                      )}

                      {/* Actions */}
                      {isOpen ? (
                        <div className="flex items-center gap-2 pt-1">
                          {f.suggested_fix && (
                            <button
                              onClick={() => handleAcceptFix(f.id)}
                              className="px-2.5 py-1 rounded bg-brand-600 hover:bg-brand-500 text-white text-[11px] font-bold transition"
                            >
                              Accept Fix
                            </button>
                          )}
                          <button
                            onClick={() => {
                              setCustomFixInput(f.suggested_fix || '')
                              setEditModal({ open: true, findingId: f.id, initialFix: f.suggested_fix || '' })
                            }}
                            className="px-2.5 py-1 rounded bg-slate-200 dark:bg-slate-800 hover:bg-slate-300 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-200 text-[11px] font-semibold transition"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => setDismissModal({ open: true, findingId: f.id })}
                            className="px-2.5 py-1 rounded bg-transparent border border-slate-300 dark:border-slate-700 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 text-[11px] font-semibold transition"
                          >
                            Dismiss
                          </button>
                        </div>
                      ) : (
                        <div className="text-[11px] text-slate-500 dark:text-slate-400 italic pt-1">
                          Status: <span className="font-bold uppercase not-italic">{f.state}</span>
                          {f.decision_reason && ` (${f.decision_reason})`}
                        </div>
                      )}
                    </div>
                  )
                })
              )}
            </div>
          </div>

          {/* Human Review & Approval Gating Card */}
          <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-3">
            <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-brand-500" />
              Human Governance Sign-off Gate
            </h3>

            {highOpenCount > 0 ? (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-600 dark:text-rose-400 text-xs space-y-1">
                <span className="font-bold block">Approval Strictly Blocked</span>
                <p>
                  {highOpenCount} high-severity policy finding(s) remain open. Every finding must be accepted or dismissed with a recorded reason before sign-off.
                </p>
              </div>
            ) : (
              <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs">
                <span className="font-bold block">Zero High-Severity Violations</span>
                <p>Eligible for Reviewer and Manager human sign-off.</p>
              </div>
            )}
          </div>

          {/* Collaboration Comments */}
          <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-3">
            <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-brand-500" />
              Reviewer & Creator Comments
            </h3>

            <div className="space-y-2 max-h-36 overflow-y-auto text-xs">
              {(doc?.comments || []).length === 0 ? (
                <p className="text-slate-400 italic">No comments yet.</p>
              ) : (
                doc.comments.map((c: any) => (
                  <div key={c.id} className="p-2.5 rounded-lg bg-slate-50 dark:bg-[#090d16] border border-slate-200/60 dark:border-slate-800 space-y-1">
                    <div className="flex items-center justify-between text-[11px] font-bold">
                      <span className="text-brand-600 dark:text-brand-400">{c.user_name || c.user_role}</span>
                      <span className="text-slate-400 text-[10px]">{c.created_at?.slice(0, 16)}</span>
                    </div>
                    <p className="text-slate-700 dark:text-slate-300">{c.body}</p>
                  </div>
                ))
              )}
            </div>

            <div className="flex gap-2 pt-1">
              <input
                type="text"
                value={commentInput}
                onChange={(e) => setCommentInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAddComment()}
                placeholder="Add a governance comment..."
                className="flex-1 px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-[#090d16] border border-slate-200 dark:border-slate-700 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
              <button
                onClick={handleAddComment}
                className="px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs transition"
              >
                Post
              </button>
            </div>
          </div>

          {/* Audit Trail Timeline */}
          <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-3">
            <h3 className="text-xs font-bold text-slate-900 dark:text-white uppercase tracking-wider flex items-center gap-2">
              <History className="w-4 h-4 text-brand-500" />
              Immutable Audit Log
            </h3>

            <div className="space-y-1.5 max-h-40 overflow-y-auto text-[11px] font-mono pr-1">
              {(doc?.audit_log || []).slice(0, 8).map((a: any) => (
                <div key={a.id} className="text-slate-500 dark:text-slate-400 truncate">
                  <span className="text-slate-400">{a.created_at?.slice(11, 19)}</span> ·{' '}
                  <span className="font-bold text-slate-700 dark:text-slate-300">{a.actor}:</span> {a.event}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Dismiss Finding Modal with Mandatory Reason */}
      {dismissModal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Dismiss Governance Finding
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400 leading-normal">
              A mandatory justification is required for dismissing a brand finding. This reason is immutably recorded in the compliance audit trail.
            </p>
            <textarea
              value={dismissReason}
              onChange={(e) => setDismissReason(e.target.value)}
              placeholder="e.g. Authorized promotional exception approved by legal..."
              className="w-full p-3 rounded-xl bg-slate-50 dark:bg-[#090d16] border border-slate-200 dark:border-slate-700 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 min-h-[90px]"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setDismissModal({ open: false, findingId: null })}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                onClick={handleDismissFinding}
                className="px-4 py-1.5 rounded-lg text-xs font-bold text-white bg-rose-600 hover:bg-rose-500 transition"
              >
                Confirm Dismissal
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Edit Fix Modal */}
      {editModal.open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Customize Suggested Fix
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Edit the replacement text to preserve the creator&apos;s intent while adhering to brand voice.
            </p>
            <input
              type="text"
              value={customFixInput}
              onChange={(e) => setCustomFixInput(e.target.value)}
              className="w-full px-3 py-2 rounded-xl bg-slate-50 dark:bg-[#090d16] border border-slate-200 dark:border-slate-700 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-2 focus:ring-brand-500 font-mono"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setEditModal({ open: false, findingId: null, initialFix: '' })}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold text-slate-600 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  if (editModal.findingId) {
                    handleAcceptFix(editModal.findingId, customFixInput)
                    setEditModal({ open: false, findingId: null, initialFix: '' })
                  }
                }}
                className="px-4 py-1.5 rounded-lg text-xs font-bold text-white bg-brand-600 hover:bg-brand-500 transition"
              >
                Apply Custom Fix
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Clause Inspector Modal */}
      <ClauseModal
        isOpen={clauseModal.open}
        clauseId={clauseModal.id}
        clauseInfo={clauseModal.info}
        onClose={() => setClauseModal({ open: false, id: null, info: null })}
      />
    </div>
  )
}
