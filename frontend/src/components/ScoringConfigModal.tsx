import React, { useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';
import { ScoringConfig } from '../types';
import { X, Sliders, CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';

interface ScoringConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const ScoringConfigModal: React.FC<ScoringConfigModalProps> = ({ isOpen, onClose }) => {
  const api = useApi();
  const [config, setConfig] = useState<ScoringConfig>({
    qualified_threshold: 75,
    needs_info_threshold: 50,
    fit_weight: 0.25,
    readiness_weight: 0.25,
    opportunity_weight: 0.30,
    risk_weight: 0.20,
  });
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSaving(false);
    setSavedSuccess(false);
    setError(null);
    if (isOpen) {
      api.getScoringConfig().then((data) => {
        if (data) {
          setConfig({
            qualified_threshold: data.qualified_threshold ?? 75,
            needs_info_threshold: data.needs_info_threshold ?? 50,
            fit_weight: data.fit_weight ?? 0.25,
            readiness_weight: data.readiness_weight ?? 0.25,
            opportunity_weight: data.opportunity_weight ?? 0.30,
            risk_weight: data.risk_weight ?? 0.20,
          });
        }
      }).catch((err) => {
        console.error('Failed to load scoring config:', err);
      });
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const totalWeight = Math.round((config.fit_weight + config.readiness_weight + config.opportunity_weight + config.risk_weight) * 100) / 100;
  const isWeightValid = Math.abs(totalWeight - 1.0) < 0.001;

  const handleWeightChange = (key: keyof ScoringConfig, value: number) => {
    setConfig(prev => ({
      ...prev,
      [key]: Math.round(value * 100) / 100,
    }));
  };

  const handleResetDefaults = () => {
    setConfig({
      qualified_threshold: 75,
      needs_info_threshold: 50,
      fit_weight: 0.25,
      readiness_weight: 0.25,
      opportunity_weight: 0.30,
      risk_weight: 0.20,
    });
    setError(null);
  };

  const handleSave = async (e?: React.FormEvent | React.MouseEvent) => {
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    if (!isWeightValid) {
      setError(`Weights must sum to exactly 1.00 (currently ${totalWeight.toFixed(2)})`);
      return;
    }
    if (config.needs_info_threshold >= config.qualified_threshold) {
      setError("Needs More Information threshold must be strictly less than Qualified threshold.");
      return;
    }

    setSaving(true);
    setError(null);
    setSavedSuccess(false);
    try {
      await api.updateScoringConfig(config);
      setSavedSuccess(true);
      setSaving(false);
      window.dispatchEvent(new CustomEvent('scoring-config-updated', { detail: config }));
      setTimeout(() => {
        setSavedSuccess(false);
        onClose();
      }, 600);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to save configuration');
      setSaving(false);
      setSavedSuccess(false);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4 animate-in fade-in duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="glass-panel border border-white/[0.12] rounded-2xl max-w-lg w-full p-6 sm:p-7 shadow-2xl shadow-indigo-950/50 overflow-y-auto max-h-[90vh] relative">
        {/* Glow ambient highlight */}
        <div className="absolute top-0 right-0 w-48 h-48 bg-indigo-500/10 rounded-full blur-2xl pointer-events-none" />

        <div className="flex items-center justify-between pb-4 border-b border-white/[0.08] mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 text-indigo-400 border border-indigo-500/30">
              <Sliders size={20} />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white tracking-tight">Qualification Engine Tuning</h2>
              <p className="text-xs text-slate-400">Customize criteria weights and status thresholds</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1.5 rounded-xl hover:bg-white/[0.05] transition cursor-pointer"
          >
            <X size={20} />
          </button>
        </div>

        {error && (
          <div className="mb-4 bg-rose-500/10 border border-rose-500/30 rounded-xl p-3 text-rose-200 text-xs flex items-center gap-2">
            <AlertTriangle size={15} className="text-rose-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {savedSuccess && (
          <div className="mb-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl p-3 text-emerald-200 text-xs flex items-center gap-2">
            <CheckCircle2 size={15} className="text-emerald-400 flex-shrink-0" />
            <span>Configuration saved! Updating active pipeline criteria...</span>
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-5">
          {/* Thresholds */}
          <div className="glass-card p-4 rounded-xl border border-white/[0.06] space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">Lead Status Thresholds</h3>
            <div>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-slate-300">Qualified Threshold:</span>
                <span className="font-bold text-emerald-400 font-mono">&ge; {config.qualified_threshold} / 100</span>
              </div>
              <input
                type="range"
                min={60}
                max={95}
                step={1}
                value={config.qualified_threshold}
                onChange={(e) => setConfig({ ...config, qualified_threshold: Number(e.target.value) })}
                className="w-full accent-emerald-500 cursor-pointer"
              />
            </div>
            <div>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-slate-300">Needs More Information Threshold:</span>
                <span className="font-bold text-amber-400 font-mono">&ge; {config.needs_info_threshold} / 100</span>
              </div>
              <input
                type="range"
                min={30}
                max={65}
                step={1}
                value={config.needs_info_threshold}
                onChange={(e) => setConfig({ ...config, needs_info_threshold: Number(e.target.value) })}
                className="w-full accent-amber-500 cursor-pointer"
              />
              <p className="text-[11px] text-slate-400 mt-1">Scores below {config.needs_info_threshold} are marked as Low Priority.</p>
            </div>

            {/* Explanatory Rule Callout */}
            <div className="p-3 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-[11px] text-indigo-300 leading-relaxed">
              <div className="font-semibold text-indigo-200 mb-1 flex items-center gap-1.5">
                <span>💡</span>
                <span>Qualification Status Rules</span>
              </div>
              <ul className="space-y-1 text-slate-300">
                <li><strong className="text-emerald-400">Qualified (&ge; {config.qualified_threshold})</strong>: Requirements are complete and lead score meets or exceeds threshold.</li>
                <li><strong className="text-amber-400">Needs More Information</strong>: Critical customer data is missing (e.g. budget, timeline, scale) or score is between {config.needs_info_threshold}&ndash;{config.qualified_threshold - 1}.</li>
                <li><strong className="text-rose-400">Low Priority (&lt; {config.needs_info_threshold})</strong>: Score falls below minimum threshold or inquiry is out-of-scope.</li>
              </ul>
            </div>
          </div>

          {/* Criteria Weights */}
          <div className="glass-card p-4 rounded-xl border border-white/[0.06] space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300">Criteria Weights</h3>
              <span className={`text-[11px] px-2.5 py-0.5 rounded-full font-mono font-bold border ${isWeightValid ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30' : 'bg-rose-500/10 text-rose-300 border-rose-500/30'}`}>
                Sum: {totalWeight.toFixed(2)} / 1.00
              </span>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-slate-300">Product/Technical Fit:</span>
                <span className="font-mono text-cyan-400 font-bold">{Math.round(config.fit_weight * 100)}%</span>
              </div>
              <input
                type="range"
                min={0.05}
                max={0.50}
                step={0.05}
                value={config.fit_weight}
                onChange={(e) => handleWeightChange('fit_weight', Number(e.target.value))}
                className="w-full accent-cyan-500 cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-slate-300">Readiness (Timeline & Budget):</span>
                <span className="font-mono text-blue-400 font-bold">{Math.round(config.readiness_weight * 100)}%</span>
              </div>
              <input
                type="range"
                min={0.05}
                max={0.50}
                step={0.05}
                value={config.readiness_weight}
                onChange={(e) => handleWeightChange('readiness_weight', Number(e.target.value))}
                className="w-full accent-blue-500 cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-slate-300">Opportunity Scale:</span>
                <span className="font-mono text-purple-400 font-bold">{Math.round(config.opportunity_weight * 100)}%</span>
              </div>
              <input
                type="range"
                min={0.05}
                max={0.50}
                step={0.05}
                value={config.opportunity_weight}
                onChange={(e) => handleWeightChange('opportunity_weight', Number(e.target.value))}
                className="w-full accent-purple-500 cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1.5">
                <span className="text-slate-300">Risk Mitigation Weight:</span>
                <span className="font-mono text-rose-400 font-bold">{Math.round(config.risk_weight * 100)}%</span>
              </div>
              <input
                type="range"
                min={0.05}
                max={0.50}
                step={0.05}
                value={config.risk_weight}
                onChange={(e) => handleWeightChange('risk_weight', Number(e.target.value))}
                className="w-full accent-rose-500 cursor-pointer"
              />
            </div>
          </div>

          <div className="p-3 bg-slate-900/80 rounded-xl text-[11px] text-slate-400 font-mono border border-white/[0.06] leading-relaxed">
            <strong className="text-indigo-300">Formula:</strong> Score = (Fit × {config.fit_weight.toFixed(2)}) + (Readiness × {config.readiness_weight.toFixed(2)}) + (Opp × {config.opportunity_weight.toFixed(2)}) + ((100 − Risk) × {config.risk_weight.toFixed(2)})
          </div>

          <div className="flex gap-3 justify-end pt-2">
            <button
              type="button"
              onClick={handleResetDefaults}
              className="px-4 py-2 text-xs text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700/80 border border-white/[0.08] rounded-xl flex items-center gap-1.5 transition cursor-pointer active:scale-95"
            >
              <RefreshCw size={13} /> Reset Defaults
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving || !isWeightValid}
              className={`px-5 py-2 text-xs font-semibold rounded-xl text-white transition cursor-pointer active:scale-95 flex items-center gap-1.5 shadow-lg ${
                saving
                  ? 'bg-blue-600/70 text-blue-100 cursor-wait'
                  : savedSuccess
                  ? 'bg-emerald-600 hover:bg-emerald-500 shadow-emerald-500/20'
                  : !isWeightValid
                  ? 'bg-blue-600/40 text-slate-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 shadow-indigo-500/25'
              }`}
            >
              {saving ? (
                <>
                  <RefreshCw size={13} className="animate-spin" />
                  <span>Applying...</span>
                </>
              ) : savedSuccess ? (
                <>
                  <CheckCircle2 size={14} className="text-white" />
                  <span>Applied!</span>
                </>
              ) : (
                <span>Apply Configuration</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ScoringConfigModal;
