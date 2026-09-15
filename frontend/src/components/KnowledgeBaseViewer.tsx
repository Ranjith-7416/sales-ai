import React, { useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';
import { KBProduct, KBService } from '../types';
import { Database, Search, ShieldCheck, Clock, Check, Layers, ExternalLink } from 'lucide-react';

const KnowledgeBaseViewer: React.FC = () => {
  const api = useApi();
  const [products, setProducts] = useState<KBProduct[]>([]);
  const [services, setServices] = useState<KBService[]>([]);
  const [activeTab, setActiveTab] = useState<'products' | 'services'>('products');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[] | null>(null);
  const [searching, setSearching] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadCatalog = async () => {
      try {
        setLoading(true);
        const [prodList, servList] = await Promise.all([
          api.getProducts(),
          api.getServices(),
        ]);
        setProducts(prodList);
        setServices(servList);
      } catch (err) {
        console.error('Failed to load KB entries:', err);
      } finally {
        setLoading(false);
      }
    };
    loadCatalog();
  }, []);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    setSearching(true);
    try {
      const results = await api.searchKnowledgeBase(searchQuery, activeTab === 'products' ? 'product' : 'service');
      setSearchResults(results);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setSearching(false);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults(null);
  };

  return (
    <div className="space-y-6">
      {/* Header Glass Panel */}
      <div className="glass-panel border border-white/[0.08] rounded-2xl p-6 sm:p-8 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2.5 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 text-indigo-400 border border-indigo-500/30">
                <Database size={22} />
              </div>
              <h1 className="text-2xl font-bold text-white tracking-tight">Verified Product & Service Knowledge Base</h1>
            </div>
            <p className="text-slate-400 text-xs max-w-2xl leading-relaxed">
              Ground truth commercial catalog for RAG vector search. The Proposal Agent strictly draws pricing,
              capabilities, SLAs, and deliverables from these verified enterprise records.
            </p>
          </div>

          {/* Search bar */}
          <form onSubmit={handleSearch} className="flex gap-2 min-w-[300px]">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
              <input
                type="text"
                placeholder="Search catalog or test RAG..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-900/60 border border-white/10 rounded-xl pl-10 pr-3 py-2 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-cyan-500/60 focus:ring-2 focus:ring-cyan-500/20 transition"
              />
            </div>
            <button
              type="submit"
              disabled={searching}
              className="px-4 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white rounded-xl text-xs font-semibold transition cursor-pointer active:scale-95 shadow-lg shadow-indigo-500/20"
            >
              {searching ? 'Querying...' : 'Search'}
            </button>
            {searchResults !== null && (
              <button
                type="button"
                onClick={clearSearch}
                className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 border border-white/[0.08] rounded-xl text-xs font-semibold transition cursor-pointer active:scale-95"
              >
                Clear
              </button>
            )}
          </form>
        </div>

        {/* Tab switcher */}
        <div className="flex gap-2 mt-6 pt-4 border-t border-white/[0.08]">
          <button
            type="button"
            onClick={() => { setActiveTab('products'); setSearchResults(null); }}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-2 cursor-pointer active:scale-95 border ${
              activeTab === 'products'
                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white border-indigo-400/40 shadow-lg shadow-indigo-500/25'
                : 'bg-slate-900/50 text-slate-400 border-white/[0.06] hover:bg-slate-800/80 hover:text-white'
            }`}
          >
            <Layers size={14} /> Products ({products.length})
          </button>
          <button
            type="button"
            onClick={() => { setActiveTab('services'); setSearchResults(null); }}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition flex items-center gap-2 cursor-pointer active:scale-95 border ${
              activeTab === 'services'
                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white border-indigo-400/40 shadow-lg shadow-indigo-500/25'
                : 'bg-slate-900/50 text-slate-400 border-white/[0.06] hover:bg-slate-800/80 hover:text-white'
            }`}
          >
            <ExternalLink size={14} /> Professional Services ({services.length})
          </button>
        </div>
      </div>

      {/* Search results banner if active */}
      {searchResults !== null && (
        <div className="glass-card bg-indigo-500/[0.08] border border-indigo-500/30 rounded-2xl p-4 text-indigo-200 text-xs flex justify-between items-center">
          <span>
            RAG Semantic Match for <strong>"{searchQuery}"</strong>: {searchResults.length} verified item(s) found.
          </span>
          <button type="button" onClick={clearSearch} className="text-xs text-cyan-400 hover:underline cursor-pointer">Show all</button>
        </div>
      )}

      {/* Content area */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 glass-panel border border-white/[0.08] rounded-2xl">
          <div className="w-12 h-12 rounded-full border-2 border-indigo-500/30 border-t-indigo-400 animate-spin mb-3" />
          <span className="text-slate-400 text-xs font-medium">Loading verified catalog from RAG service...</span>
        </div>
      ) : activeTab === 'products' ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {(searchResults ? searchResults.map(r => r.product || r) : products).map((product: KBProduct) => (
            <div key={product.id} className="glass-card border border-white/[0.08] rounded-2xl p-6 hover:border-indigo-500/40 transition flex flex-col justify-between group">
              <div>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-wider bg-cyan-500/10 px-2.5 py-1 rounded-lg border border-cyan-500/20">
                      {product.id}
                    </span>
                    <h2 className="text-lg font-bold text-white group-hover:text-cyan-300 transition mt-2">{product.name}</h2>
                    <span className="text-xs text-slate-400">{product.category}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-xl border border-emerald-500/30 block">
                      {product.pricing}
                    </span>
                  </div>
                </div>

                <p className="text-slate-300 text-xs mb-4 leading-relaxed">{product.description}</p>

                {/* Features */}
                <div className="mb-4">
                  <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2">Verified Features</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                    {(product.features || []).map((feat, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-xs text-slate-200">
                        <Check size={13} className="text-emerald-400 flex-shrink-0" />
                        <span>{feat}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Badges footer */}
              <div className="pt-4 border-t border-white/[0.06] flex flex-wrap gap-2 items-center text-xs">
                {product.implementation_timeline && (
                  <span className="inline-flex items-center gap-1.5 bg-slate-900/60 border border-white/[0.06] px-2.5 py-1 rounded-xl text-slate-300 text-[11px]">
                    <Clock size={12} className="text-amber-400" /> Timeline: {product.implementation_timeline}
                  </span>
                )}
                {product.uptime_sla && (
                  <span className="inline-flex items-center gap-1.5 bg-slate-900/60 border border-white/[0.06] px-2.5 py-1 rounded-xl text-slate-300 text-[11px]">
                    <ShieldCheck size={12} className="text-cyan-400" /> SLA: {product.uptime_sla}
                  </span>
                )}
                {(product.certifications || []).map((cert, idx) => (
                  <span key={idx} className="bg-purple-500/10 border border-purple-500/20 text-purple-300 px-2 py-0.5 rounded-lg text-[10px] font-medium">
                    {cert}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {(searchResults ? searchResults.map(r => r.service || r) : services).map((service: KBService) => (
            <div key={service.id} className="glass-card border border-white/[0.08] rounded-2xl p-6 hover:border-indigo-500/40 transition flex flex-col justify-between group">
              <div>
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div>
                    <span className="text-[10px] font-mono font-bold text-purple-400 uppercase tracking-wider bg-purple-500/10 px-2.5 py-1 rounded-lg border border-purple-500/20">
                      {service.id}
                    </span>
                    <h2 className="text-lg font-bold text-white group-hover:text-purple-300 transition mt-2">{service.name}</h2>
                    <span className="text-xs text-slate-400">{service.category}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-bold text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-xl border border-emerald-500/30 block">
                      {service.pricing}
                    </span>
                  </div>
                </div>

                <p className="text-slate-300 text-xs mb-4 leading-relaxed">{service.description}</p>

                {service.deliverables && (
                  <div className="mb-4">
                    <h3 className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-2">Deliverables</h3>
                    <div className="space-y-1.5">
                      {service.deliverables.map((del, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-xs text-slate-200">
                          <Check size={13} className="text-purple-400 flex-shrink-0" />
                          <span>{del}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="pt-4 border-t border-white/[0.06] flex flex-wrap gap-2 items-center text-xs">
                {service.delivery_timeline && (
                  <span className="inline-flex items-center gap-1.5 bg-slate-900/60 border border-white/[0.06] px-2.5 py-1 rounded-xl text-slate-300 text-[11px]">
                    <Clock size={12} className="text-amber-400" /> Delivery: {service.delivery_timeline}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default KnowledgeBaseViewer;

