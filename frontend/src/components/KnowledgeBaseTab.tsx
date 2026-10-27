import React, { useState, useEffect } from 'react'
import { Database, Plus, Trash2, Edit3, Shield, Palette, FileUp, Lock, Check } from 'lucide-react'
import { apiRequest } from '../api'

interface KnowledgeBaseTabProps {
  currentRole: string
}

export default function KnowledgeBaseTab({ currentRole }: KnowledgeBaseTabProps) {
  const [terms, setTerms] = useState<any[]>([])
  const [facts, setFacts] = useState<any[]>([])
  const [clauses, setClauses] = useState<any[]>([])
  const [assets, setAssets] = useState<any[]>([])
  const [redactionTerms, setRedactionTerms] = useState<any[]>([])
  const [loading, setLoading] = useState(false)

  // Forms state
  const [badTerm, setBadTerm] = useState('')
  const [goodTerm, setGoodTerm] = useState('')
  const [termNote, setTermNote] = useState('')

  const [priceInput, setPriceInput] = useState('1,199')
  const [factLabel, setFactLabel] = useState('')
  const [factValue, setFactValue] = useState('')
  const [factSource, setFactSource] = useState('')

  const [importText, setImportText] = useState('')
  const [importTitle, setImportTitle] = useState('')

  const [newRedactionTerm, setNewRedactionTerm] = useState('')

  const isAdmin = currentRole.toLowerCase() === 'admin'

  const loadAll = async () => {
    setLoading(true)
    try {
      const [tData, fData, cData, aData, rData] = await Promise.all([
        apiRequest('/terms', {}, currentRole),
        apiRequest('/facts', {}, currentRole),
        apiRequest('/clauses', {}, currentRole),
        apiRequest('/assets', {}, currentRole),
        apiRequest('/redaction-terms', {}, currentRole),
      ])
      setTerms(tData.terms || [])
      setFacts(fData.facts || [])
      setClauses(cData.clauses || [])
      setAssets(aData.assets || [])
      setRedactionTerms(rData.redaction_terms || [])

      // Set price fact
      const pFact = (fData.facts || []).find((f: any) => f.id === 'F-014')
      if (pFact) setPriceInput(pFact.value)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAll()
  }, [currentRole])

  // Add Term
  const handleAddTerm = async () => {
    if (!badTerm.trim() || !goodTerm.trim()) return
    try {
      await apiRequest('/terms', {
        method: 'POST',
        body: JSON.stringify({
          bad_term: badTerm.trim(),
          preferred_term: goodTerm.trim(),
          note: termNote.trim(),
        })
      }, currentRole)
      setBadTerm('')
      setGoodTerm('')
      setTermNote('')
      loadAll()
    } catch (e: any) {
      alert(e.message)
    }
  }

  // Delete Term
  const handleDeleteTerm = async (id: string) => {
    try {
      await apiRequest(`/terms/${id}`, { method: 'DELETE' }, currentRole)
      loadAll()
    } catch (e: any) {
      alert(e.message)
    }
  }

  // Update Price Fact
  const handleSavePrice = async () => {
    try {
      await apiRequest('/facts/F-014', {
        method: 'PUT',
        body: JSON.stringify({ value: priceInput.trim() })
      }, currentRole)
      alert('Approved price updated in Knowledge Base.')
      loadAll()
    } catch (e: any) {
      alert(e.message)
    }
  }

  // Import Guidelines
  const handleImportGuidelines = async () => {
    if (!importText.trim()) return
    try {
      const res = await apiRequest('/guidelines/import', {
        method: 'POST',
        body: JSON.stringify({
          title: importTitle || 'Policy Addendum',
          content: importText.trim(),
        })
      }, currentRole)
      alert(`Imported ${res.imported_clauses_count} clauses with stable IDs!`)
      setImportText('')
      setImportTitle('')
      loadAll()
    } catch (e: any) {
      alert(e.message)
    }
  }

  // Add Redaction Term
  const handleAddRedaction = async () => {
    if (!newRedactionTerm.trim()) return
    try {
      await apiRequest('/redaction-terms', {
        method: 'POST',
        body: JSON.stringify({ term: newRedactionTerm.trim() })
      }, currentRole)
      setNewRedactionTerm('')
      loadAll()
    } catch (e: any) {
      alert(e.message)
    }
  }

  const handleDeleteRedaction = async (id: string) => {
    try {
      await apiRequest(`/redaction-terms/${id}`, { method: 'DELETE' }, currentRole)
      loadAll()
    } catch (e: any) {
      alert(e.message)
    }
  }

  const palette = (assets.find((a: any) => a.type === 'palette')?.palette) || ['#1b2a49', '#0f8b8d', '#ffffff', '#e8a33d']

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 dark:text-white">
            Brand Knowledge Base (Lumina Skincare)
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            Source of truth for rules, terminology, pricing facts, brand palette, and confidentiality terms.
          </p>
        </div>

        {!isAdmin && (
          <div className="px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20 text-amber-600 dark:text-amber-400 text-xs font-semibold flex items-center gap-1.5">
            <Lock className="w-3.5 h-3.5" /> Read-Only Mode (Switch role to Admin above to modify)
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Approved Terminology Card */}
        <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Database className="w-4 h-4 text-brand-500" />
              Approved Terminology Dictionary
            </h3>
            <span className="text-xs font-mono text-slate-400">{terms.length} terms</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="text-slate-400 border-b border-slate-100 dark:border-slate-800 uppercase font-semibold text-[10px]">
                <tr>
                  <th className="py-2">ID</th>
                  <th className="py-2 text-rose-500">Avoid</th>
                  <th className="py-2 text-emerald-500">Use Instead</th>
                  {isAdmin && <th className="py-2 text-right">Action</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                {terms.map((t) => (
                  <tr key={t.id}>
                    <td className="py-2.5 font-mono font-bold text-slate-400">{t.id}</td>
                    <td className="py-2.5 text-rose-600 dark:text-rose-400 font-semibold">{t.bad_term}</td>
                    <td className="py-2.5 text-emerald-600 dark:text-emerald-400 font-bold">{t.preferred_term}</td>
                    {isAdmin && (
                      <td className="py-2.5 text-right">
                        <button
                          onClick={() => handleDeleteTerm(t.id)}
                          className="text-slate-400 hover:text-rose-500 transition"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {isAdmin && (
            <div className="pt-3 border-t border-slate-100 dark:border-slate-800 space-y-2">
              <span className="text-xs font-bold text-slate-700 dark:text-slate-300 block">Add Term</span>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <input
                  type="text"
                  value={badTerm}
                  onChange={(e) => setBadTerm(e.target.value)}
                  placeholder="Avoid wording"
                  className="px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-[#090d16] border border-slate-200 dark:border-slate-700 text-xs text-slate-800 dark:text-slate-200"
                />
                <input
                  type="text"
                  value={goodTerm}
                  onChange={(e) => setGoodTerm(e.target.value)}
                  placeholder="Preferred wording"
                  className="px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-[#090d16] border border-slate-200 dark:border-slate-700 text-xs text-slate-800 dark:text-slate-200"
                />
                <button
                  onClick={handleAddTerm}
                  className="px-3 py-1.5 rounded-lg bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs transition"
                >
                  Add Term
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Approved Facts & Pricing Card */}
        <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Shield className="w-4 h-4 text-brand-500" />
              Approved Facts & Verification Values
            </h3>
            <span className="text-xs font-mono text-slate-400">{facts.length} facts</span>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 dark:bg-[#090d16] border border-slate-200/80 dark:border-slate-800 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-800 dark:text-slate-200">
                F-014: Glow Serum Current Retail Price
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-500 font-bold">
                Active
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-slate-500 dark:text-slate-400">Approved Price: Rs</span>
              <input
                type="text"
                value={priceInput}
                onChange={(e) => setPriceInput(e.target.value)}
                disabled={!isAdmin}
                className="w-24 px-2 py-1 rounded bg-white dark:bg-[#131b26] border border-slate-300 dark:border-slate-700 font-bold font-mono text-slate-900 dark:text-white"
              />
              {isAdmin && (
                <button
                  onClick={handleSavePrice}
                  className="px-3 py-1 rounded bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs"
                >
                  Save
                </button>
              )}
            </div>
          </div>

          {/* List of other facts */}
          <div className="space-y-2 text-xs">
            {facts.filter((f) => f.id !== 'F-014').map((f) => (
              <div key={f.id} className="p-2.5 rounded-lg border border-slate-100 dark:border-slate-800/80 flex items-center justify-between">
                <div>
                  <span className="font-mono font-bold text-brand-600 dark:text-brand-400 mr-2">{f.id}</span>
                  <span className="font-semibold text-slate-800 dark:text-slate-200">{f.label}:</span>{' '}
                  <span className="text-slate-600 dark:text-slate-400">{f.value}</span>
                </div>
                <span className="text-[10px] text-slate-400 font-mono">exp: {f.expires_on || 'Permanent'}</span>
              </div>
            ))}
          </div>

          {/* Brand Palette Swatches */}
          <div className="pt-2 border-t border-slate-100 dark:border-slate-800 space-y-2">
            <span className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
              <Palette className="w-3.5 h-3.5 text-brand-500" />
              Approved Brand Palette (V-01)
            </span>
            <div className="flex items-center gap-3">
              {palette.map((c: string) => (
                <div key={c} className="flex items-center gap-1.5">
                  <span
                    className="w-6 h-6 rounded-md shadow-sm border border-slate-200 dark:border-slate-700"
                    style={{ backgroundColor: c }}
                  ></span>
                  <span className="font-mono text-[11px] text-slate-500 dark:text-slate-400">{c}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Guidelines Import Card */}
        <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <FileUp className="w-4 h-4 text-brand-500" />
              Import Guidelines & Clauses
            </h3>
            <span className="text-xs text-slate-400 font-mono">{clauses.length} active clauses</span>
          </div>

          <p className="text-xs text-slate-500 dark:text-slate-400 leading-normal">
            Paste guidelines text with numbered or prefix-labelled rules (e.g. C-01, Voice 2.1). The parser splits clauses and provisions them with stable IDs.
          </p>

          <div className="space-y-2">
            <input
              type="text"
              value={importTitle}
              onChange={(e) => setImportTitle(e.target.value)}
              placeholder="Guideline Title (e.g. Influencer Guidelines 2026)"
              disabled={!isAdmin}
              className="w-full px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-[#090d16] border border-slate-200 dark:border-slate-700 text-xs text-slate-800 dark:text-slate-200"
            />
            <textarea
              value={importText}
              onChange={(e) => setImportText(e.target.value)}
              placeholder="C-05: Claims must link to certified lab reports.&#10;Tone 1.3: Do not use aggressive urgency tactics."
              disabled={!isAdmin}
              className="w-full min-h-[90px] p-3 rounded-lg bg-slate-50 dark:bg-[#090d16] border border-slate-200 dark:border-slate-700 text-xs text-slate-800 dark:text-slate-200 font-mono"
            />
            {isAdmin && (
              <button
                onClick={handleImportGuidelines}
                className="px-4 py-2 rounded-lg bg-brand-600 hover:bg-brand-500 text-white font-bold text-xs transition"
              >
                Import Clauses
              </button>
            )}
          </div>
        </div>

        {/* Confidential Mode Redaction Terms */}
        <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Lock className="w-4 h-4 text-amber-500" />
              Confidential Mode Redaction Terms
            </h3>
            <span className="text-xs font-mono text-slate-400">{redactionTerms.length} terms</span>
          </div>

          <p className="text-xs text-slate-500 dark:text-slate-400 leading-normal">
            When Confidential Mode is activated during a review, these sensitive strings (project names, NDA formulas, internal financials) are tokenized with placeholder hashes before external AI transmission.
          </p>

          <div className="space-y-2 text-xs">
            {redactionTerms.map((rt) => (
              <div key={rt.id} className="p-2.5 rounded-lg bg-slate-50 dark:bg-[#090d16] border border-slate-200/80 dark:border-slate-800 flex items-center justify-between">
                <div className="flex items-center gap-2 font-mono">
                  <span className="font-bold text-slate-900 dark:text-white">&quot;{rt.term}&quot;</span>
                  <span className="text-slate-400">&rarr;</span>
                  <span className="text-amber-500 font-bold">{rt.replacement}</span>
                </div>
                {isAdmin && (
                  <button
                    onClick={() => handleDeleteRedaction(rt.id)}
                    className="text-slate-400 hover:text-rose-500 transition"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            ))}
          </div>

          {isAdmin && (
            <div className="flex gap-2 pt-2">
              <input
                type="text"
                value={newRedactionTerm}
                onChange={(e) => setNewRedactionTerm(e.target.value)}
                placeholder="e.g. Project Radiance or $4.2M"
                className="flex-1 px-3 py-1.5 rounded-lg bg-slate-50 dark:bg-[#090d16] border border-slate-200 dark:border-slate-700 text-xs text-slate-800 dark:text-slate-200"
              />
              <button
                onClick={handleAddRedaction}
                className="px-3 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-bold text-xs transition"
              >
                Add Term
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
