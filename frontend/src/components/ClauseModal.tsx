import React from 'react'
import { X, BookOpen, ShieldCheck } from 'lucide-react'

interface ClauseModalProps {
  isOpen: boolean
  clauseId: string | null
  clauseInfo: {
    id?: string
    title?: string
    text?: string
    category?: string
  } | null
  onClose: () => void
}

export default function ClauseModal({ isOpen, clauseId, clauseInfo, onClose }: ClauseModalProps) {
  if (!isOpen || !clauseId) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 animate-in fade-in duration-150">
      <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 pb-3 border-b border-slate-100 dark:border-slate-800">
          <div className="w-10 h-10 rounded-xl bg-brand-500/10 text-brand-600 dark:text-brand-400 flex items-center justify-center">
            <BookOpen className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-slate-100 dark:bg-slate-800 text-slate-800 dark:text-slate-200">
                {clauseId}
              </span>
              <span className="text-xs font-medium text-brand-600 dark:text-brand-400">
                {clauseInfo?.category || 'Governance Rule'}
              </span>
            </div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white mt-1">
              {clauseInfo?.title || `Official Policy Rule ${clauseId}`}
            </h3>
          </div>
        </div>

        <div className="mt-4 space-y-3">
          <div>
            <h4 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Approved Policy Clause Text
            </h4>
            <p className="mt-1 text-sm text-slate-700 dark:text-slate-300 leading-relaxed bg-slate-50 dark:bg-[#090d16] p-3.5 rounded-xl border border-slate-200/60 dark:border-slate-800">
              {clauseInfo?.text || 'Clause details loaded from Lumina Skincare Governance Guidelines.'}
            </p>
          </div>

          <div className="flex items-center gap-2 text-xs text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-2 rounded-lg">
            <ShieldCheck className="w-4 h-4 flex-shrink-0" />
            <span>Non-negotiable Brand Standard: Every raised finding cites verified evidence.</span>
          </div>
        </div>

        <div className="mt-5 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-xs font-semibold rounded-lg transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}
