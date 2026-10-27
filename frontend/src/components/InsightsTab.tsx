import React, { useState, useEffect } from 'react'
import {
  BarChart3,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Calendar,
  Sparkles,
  Info,
  TrendingUp,
  FileCheck2
} from 'lucide-react'
import { apiRequest } from '../api'

interface InsightsTabProps {
  currentRole: string
}

export default function InsightsTab({ currentRole }: InsightsTabProps) {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  const loadInsights = async () => {
    setLoading(true)
    try {
      const res = await apiRequest('/insights', {}, currentRole)
      setData(res)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadInsights()
  }, [currentRole])

  if (loading || !data) {
    return (
      <div className="py-20 text-center text-xs text-slate-400">
        Loading governance insights and guideline clarity analytics...
      </div>
    )
  }

  const { summary, clause_analytics, max_flags, frequent_categories, issues_by_type, expiring_facts } = data
  const unclearCount = summary?.unclear_guidelines_count || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-bold text-slate-900 dark:text-white">
          Brand Governance & Clarity Insights
        </h2>
        <p className="text-xs text-slate-500 dark:text-slate-400">
          Real-time analytics computed directly from the audit trail to detect ambiguous guidelines, monitor turnaround, and track expiring facts.
        </p>
      </div>

      {/* Metric Cards Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold">Total Documents</span>
            <FileCheck2 className="w-4 h-4 text-brand-500" />
          </div>
          <div className="text-2xl font-extrabold text-slate-900 dark:text-white">
            {summary.total_documents}
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400">
            {summary.approved_documents} approved for publication
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold">Approval Turnaround</span>
            <Clock className="w-4 h-4 text-brand-500" />
          </div>
          <div className="text-2xl font-extrabold text-slate-900 dark:text-white">
            {summary.avg_turnaround_minutes}m
          </div>
          <div className="text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1">
            <TrendingUp className="w-3 h-3" /> Real-time median turnaround
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold">Possibly Unclear Rules</span>
            <AlertTriangle className={`w-4 h-4 ${unclearCount > 0 ? 'text-amber-500' : 'text-slate-400'}`} />
          </div>
          <div className="text-2xl font-extrabold text-slate-900 dark:text-white">
            {unclearCount}
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400">
            Dismiss rate &ge; 50% (min 3 flags)
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 shadow-sm space-y-1">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-semibold">Active Fact Expirations</span>
            <Calendar className="w-4 h-4 text-brand-500" />
          </div>
          <div className="text-2xl font-extrabold text-slate-900 dark:text-white">
            {expiring_facts.length}
          </div>
          <div className="text-[11px] text-slate-500 dark:text-slate-400">
            {expiring_facts.filter((f: any) => f.is_urgent).length} expiring in &lt; 60 days
          </div>
        </div>
      </div>

      {/* Major Improvement 1: Guideline Clarity Table */}
      <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-slate-100 dark:border-slate-800">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-brand-500" />
              Guideline Clarity Analytics &amp; Unclear Rule Detection
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              When content creators dismiss a clause in 50% or more of its flags (min 3 flags), BrandLens highlights it as possibly unclear so the Brand Admin can refine its phrasing.
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">Calculated from Audit Trail</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 dark:bg-[#0c121c] border-b border-slate-200 dark:border-slate-800 text-slate-500 dark:text-slate-400 uppercase font-semibold text-[10px]">
              <tr>
                <th className="px-4 py-3">Clause / Rule</th>
                <th className="px-4 py-3">Times Flagged</th>
                <th className="px-4 py-3 w-32">Relative Frequency</th>
                <th className="px-4 py-3">Accepted</th>
                <th className="px-4 py-3">Dismissed</th>
                <th className="px-4 py-3">Dismiss Rate</th>
                <th className="px-4 py-3">Clarity Signal</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-sans">
              {clause_analytics.map((c: any) => {
                const pct = max_flags > 0 ? (c.flags / max_flags) * 100 : 0
                return (
                  <tr key={c.source_id} className="hover:bg-slate-50/60 dark:hover:bg-[#172230]/60 transition">
                    <td className="px-4 py-3">
                      <div className="font-bold text-slate-900 dark:text-white">
                        <span className="font-mono text-brand-600 dark:text-brand-400 mr-1.5">{c.source_id}</span>
                        {c.title}
                      </div>
                      <div className="text-[11px] text-slate-500 dark:text-slate-400 truncate max-w-sm mt-0.5">
                        {c.text}
                      </div>
                    </td>
                    <td className="px-4 py-3 font-bold text-slate-800 dark:text-slate-200">{c.flags}</td>
                    <td className="px-4 py-3">
                      <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-brand-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${Math.max(8, pct)}%` }}
                        ></div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-emerald-600 dark:text-emerald-400 font-bold">{c.accepts}</td>
                    <td className="px-4 py-3 text-rose-600 dark:text-rose-400 font-bold">{c.dismisses}</td>
                    <td className="px-4 py-3 font-mono font-bold text-slate-700 dark:text-slate-300">
                      {c.dismiss_rate}%
                    </td>
                    <td className="px-4 py-3">
                      {c.is_unclear ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/30 animate-pulse">
                          <AlertTriangle className="w-3 h-3" /> Possibly unclear guideline
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-500 dark:text-slate-400">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" /> Clear / Compliant
                        </span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Two Column Section: Category Distribution & Expiring Facts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Most Frequent Categories */}
        <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-3">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-brand-500" />
            Most Frequent Violations by Category
          </h3>

          <div className="space-y-2.5 pt-1 text-xs">
            {frequent_categories.map((fc: any) => (
              <div key={fc.category} className="space-y-1">
                <div className="flex items-center justify-between text-slate-700 dark:text-slate-300">
                  <span className="font-semibold">{fc.category}</span>
                  <span className="font-mono font-bold">{fc.count} violations</span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-slate-800 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-brand-500 h-2 rounded-full"
                    style={{ width: `${Math.min(100, fc.count * 15)}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Expiring Facts Watchlist */}
        <div className="bg-white dark:bg-[#131b26] border border-slate-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm space-y-3">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Calendar className="w-4 h-4 text-brand-500" />
            Expiring Facts Watchlist
          </h3>

          <div className="space-y-2 pt-1 text-xs">
            {expiring_facts.map((ef: any) => (
              <div
                key={ef.id}
                className="p-3 rounded-xl bg-slate-50 dark:bg-[#090d16] border border-slate-200/80 dark:border-slate-800 flex items-center justify-between"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-brand-600 dark:text-brand-400">{ef.id}</span>
                    <span className="font-bold text-slate-800 dark:text-slate-200">{ef.label}</span>
                  </div>
                  <div className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                    Owner: {ef.owner} · Source: {ef.source}
                  </div>
                </div>

                <div className="text-right">
                  <div className="font-mono font-bold text-slate-900 dark:text-white">{ef.expires_on}</div>
                  <span className={`text-[10px] font-bold uppercase ${
                    ef.is_expired
                      ? 'text-rose-500'
                      : ef.is_urgent
                      ? 'text-amber-500'
                      : 'text-emerald-500'
                  }`}>
                    {ef.is_expired ? 'Expired' : `${ef.days_remaining} days left`}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
