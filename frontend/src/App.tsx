import React, { useState, useEffect } from 'react'
import { Shield, FileText, BarChart3, Database, Sparkles, Moon, Sun } from 'lucide-react'
import ReviewTab from './components/ReviewTab'
import QueueTab from './components/QueueTab'
import KnowledgeBaseTab from './components/KnowledgeBaseTab'
import InsightsTab from './components/InsightsTab'

export type Role = 'Creator' | 'Reviewer' | 'Manager' | 'Admin'
export type Tab = 'Review' | 'Queue' | 'Knowledge Base' | 'Insights'

export default function App() {
  const [role, setRole] = useState<Role>('Creator')
  const [tab, setTab] = useState<Tab>('Review')
  const [darkMode, setDarkMode] = useState<boolean>(true)
  const [backendStatus, setBackendStatus] = useState<string>('Checking...')
  const [activeDocId, setActiveDocId] = useState<string | null>(null)

  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [darkMode])

  useEffect(() => {
    fetch('http://localhost:8000/')
      .then(res => res.json())
      .then(data => setBackendStatus(`Online (${data.app})`))
      .catch(() => setBackendStatus('Backend starting...'))
  }, [])

  const handleOpenDocFromQueue = (id: string) => {
    setActiveDocId(id)
    setTab('Review')
  }

  return (
    <div className="min-h-screen flex flex-col font-sans transition-colors duration-200 bg-slate-50 dark:bg-[#090d16] text-slate-900 dark:text-slate-100">
      {/* Top Header */}
      <header className="bg-navy-900 border-b border-slate-800 text-white px-6 py-3.5 flex flex-wrap items-center justify-between gap-4 shadow-lg sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-brand-600 to-teal-400 flex items-center justify-center shadow-md shadow-brand-500/20">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-100 to-teal-200 bg-clip-text text-transparent">
                BrandLens
              </span>
              <span className="text-[11px] font-semibold uppercase tracking-wider bg-brand-500/10 text-brand-300 border border-brand-500/30 px-2 py-0.5 rounded-full">
                Team Double Trouble
              </span>
            </div>
            <p className="text-xs text-slate-400">Pre-publication brand governance & reliability</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 bg-slate-800/80 border border-slate-700/60 rounded-lg px-3 py-1.5 text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-slate-300 font-medium">{backendStatus}</span>
          </div>

          <div className="flex items-center gap-2">
            <label htmlFor="role-select" className="text-xs text-slate-300 font-medium">Signed in as:</label>
            <select
              id="role-select"
              value={role}
              onChange={(e) => setRole(e.target.value as Role)}
              className="bg-slate-800 border border-slate-700 text-teal-300 text-xs font-semibold rounded-lg px-2.5 py-1.5 focus:ring-2 focus:ring-brand-500 focus:outline-none"
            >
              <option value="Creator">Creator (Draft & Edit)</option>
              <option value="Reviewer">Reviewer (Request Changes)</option>
              <option value="Manager">Manager (Final Sign-off)</option>
              <option value="Admin">Admin (Knowledge Base)</option>
            </select>
          </div>

          <button
            onClick={() => setDarkMode(!darkMode)}
            className="p-1.5 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 hover:text-white transition"
            title="Toggle theme"
          >
            {darkMode ? <Sun className="w-4 h-4 text-amber-300" /> : <Moon className="w-4 h-4 text-slate-300" />}
          </button>
        </div>
      </header>

      {/* Navigation Bar */}
      <nav className="bg-white dark:bg-navy-950 border-b border-slate-200 dark:border-slate-800/80 px-6 py-2.5 flex items-center justify-between shadow-sm sticky top-[65px] z-40">
        <div className="flex items-center gap-1">
          {[
            { id: 'Review', icon: Sparkles, label: 'Review & Edit' },
            { id: 'Queue', icon: FileText, label: 'Content Queue' },
            { id: 'Knowledge Base', icon: Database, label: 'Knowledge Base' },
            { id: 'Insights', icon: BarChart3, label: 'Governance Insights' },
          ].map((item) => {
            const Icon = item.icon
            const active = tab === item.id
            return (
              <button
                key={item.id}
                onClick={() => setTab(item.id as Tab)}
                className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                  active
                    ? 'bg-brand-600 text-white shadow-sm shadow-brand-600/30'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-slate-800/60'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {item.label}
              </button>
            )
          })}
        </div>

        <div className="text-xs text-slate-500 dark:text-slate-400 flex items-center gap-2">
          <span>Active Org:</span>
          <span className="font-semibold text-brand-600 dark:text-brand-400">Lumina Skincare</span>
        </div>
      </nav>

      {/* Main Content Area */}
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
        {tab === 'Review' && (
          <ReviewTab
            currentRole={role}
            activeDocId={activeDocId}
            onDocChange={(id) => setActiveDocId(id)}
          />
        )}
        {tab === 'Queue' && (
          <QueueTab
            currentRole={role}
            onOpenDoc={handleOpenDocFromQueue}
          />
        )}
        {tab === 'Knowledge Base' && (
          <KnowledgeBaseTab
            currentRole={role}
          />
        )}
        {tab === 'Insights' && (
          <InsightsTab
            currentRole={role}
          />
        )}
      </main>
    </div>
  )
}
