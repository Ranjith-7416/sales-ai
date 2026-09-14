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
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="bg-slate-800 border border-slate-700 rounded-xl max-w-lg w-full p-6 shadow-2xl overflow-y-auto max-h-[90vh]">
        <div className="flex items-center justify-between pb-4 border-b border-slate-700 mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-900/50 text-blue-400 rounded-lg">
              <Sliders size={20} />
            </div>
            <div>
              <h2 className="text-xl font-bold text-white">Configurable Qualification Engine</h2>
              <p className="text-xs text-slate-400">Customize criteria weights and status thresholds</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-md transition"
          >
            <X size={20} />
          </button>
        </div>

        {error && (
          <div className="mb-4 bg-red-900/20 border border-red-700 rounded-lg p-3 text-red-200 text-sm flex items-center gap-2">
            <AlertTriangle size={16} className="text-red-400 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {savedSuccess && (
          <div className="mb-4 bg-green-900/20 border border-green-700 rounded-lg p-3 text-green-200 text-sm flex items-center gap-2">
            <CheckCircle2 size={16} className="text-green-400 flex-shrink-0" />
            <span>Configuration saved successfully! Updating active pipeline criteria...</span>
          </div>
        )}

        <form onSubmit={handleSave} className="space-y-5">
          {/* Thresholds */}
          <div className="bg-slate-700/50 p-4 rounded-lg border border-slate-600/50 space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">Lead Status Thresholds</h3>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-300">Qualified Threshold:</span>
                <span className="font-bold text-green-400">&gt;= {config.qualified_threshold} / 100</span>
              </div>
              <input
                type="range"
                min={60}
                max={95}
                step={1}
                value={config.qualified_threshold}
                onChange={(e) => setConfig({ ...config, qualified_threshold: Number(e.target.value) })}
                className="w-full accent-green-500 cursor-pointer"
              />
            </div>
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-300">Needs More Information Threshold:</span>
                <span className="font-bold text-yellow-400">&gt;= {config.needs_info_threshold} / 100</span>
              </div>
              <input
                type="range"
                min={30}
                max={65}
                step={1}
                value={config.needs_info_threshold}
                onChange={(e) => setConfig({ ...config, needs_info_threshold: Number(e.target.value) })}
                className="w-full accent-yellow-500 cursor-pointer"
              />
              <p className="text-xs text-slate-400 mt-1">Scores below {config.needs_info_threshold} are marked as Low Priority.</p>
            </div>
          </div>

          {/* Criteria Weights */}
          <div className="bg-slate-700/50 p-4 rounded-lg border border-slate-600/50 space-y-4">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">Criteria Weights</h3>
              <span className={`text-xs px-2 py-0.5 rounded font-mono font-bold ${isWeightValid ? 'bg-green-900/50 text-green-300 border border-green-700' : 'bg-red-900/50 text-red-300 border border-red-700'}`}>
                Sum: {totalWeight.toFixed(2)} / 1.00
              </span>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-300">Product/Technical Fit:</span>
                <span className="font-mono text-blue-400 font-semibold">{Math.round(config.fit_weight * 100)}%</span>
              </div>
              <input
                type="range"
                min={0.05}
                max={0.50}
                step={0.05}
                value={config.fit_weight}
                onChange={(e) => handleWeightChange('fit_weight', Number(e.target.value))}
                className="w-full accent-blue-500 cursor-pointer"
              />
            </div>

            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-300">Readiness (Timeline & Budget):</span>
                <span className="font-mono text-blue-400 font-semibold">{Math.round(config.readiness_weight * 100)}%</span>
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
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-300">Opportunity Scale:</span>
                <span className="font-mono text-purple-400 font-semibold">{Math.round(config.opportunity_weight * 100)}%</span>
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
              <div className="flex justify-between text-sm mb-1">
                <span className="text-slate-300">Risk Mitigation Weight:</span>
                <span className="font-mono text-red-400 font-semibold">{Math.round(config.risk_weight * 100)}%</span>
              </div>
              <input
                type="range"
                min={0.05}
                max={0.50}
                step={0.05}
                value={config.risk_weight}
                onChange={(e) => handleWeightChange('risk_weight', Number(e.target.value))}
                className="w-full accent-red-500 cursor-pointer"
              />
            </div>
          </div>

          <div className="p-3 bg-slate-900/60 rounded-lg text-xs text-slate-400 font-mono border border-slate-700/60">
            <strong>Formula:</strong> Score = (Fit × {config.fit_weight.toFixed(2)}) + (Readiness × {config.readiness_weight.toFixed(2)}) + (Opp × {config.opportunity_weight.toFixed(2)}) + ((100 − Risk) × {config.risk_weight.toFixed(2)})
          </div>

          <div className="flex gap-3 justify-end pt-2">
            <button
              type="button"
              onClick={handleResetDefaults}
              className="px-4 py-2 text-sm text-slate-300 hover:text-white bg-slate-700 hover:bg-slate-600 rounded-lg flex items-center gap-1.5 transition cursor-pointer active:scale-95"
            >
              <RefreshCw size={14} /> Reset Defaults
            </button>
            <button
              type="button"
              onClick={handleSave}
              disabled={saving || !isWeightValid}
              className={`px-5 py-2 text-sm font-semibold rounded-lg text-white transition cursor-pointer active:scale-95 flex items-center gap-1.5 ${
                saving
                  ? 'bg-blue-600/70 text-blue-100 cursor-wait'
                  : savedSuccess
                  ? 'bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-500/20'
                  : !isWeightValid
                  ? 'bg-blue-600/50 text-slate-300 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 shadow-md shadow-blue-500/20'
              }`}
            >
              {saving ? (
                <>
                  <RefreshCw size={14} className="animate-spin" />
                  <span>Applying...</span>
                </>
              ) : savedSuccess ? (
                <>
                  <CheckCircle2 size={15} className="text-white" />
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
