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
      {/* Header */}
      <div className="bg-slate-800 border border-slate-700 rounded-xl p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-2 bg-blue-900/50 text-blue-400 rounded-lg">
                <Database size={24} />
              </div>
              <h1 className="text-2xl font-bold text-white">Product & Service Knowledge Base</h1>
            </div>
            <p className="text-slate-300 text-sm">
              Ground truth catalog for the RAG engine. The Proposal Agent strictly draws commercial terms,
              capabilities, SLAs, and timelines from these verified entries.
            </p>
          </div>

          {/* Search bar */}
          <form onSubmit={handleSearch} className="flex gap-2 min-w-[300px]">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 text-slate-400" size={16} />
              <input
                type="text"
                placeholder="Search catalog or test RAG..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-700 border border-slate-600 rounded-lg pl-9 pr-3 py-2 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-blue-500"
              />
            </div>
            <button
              type="submit"
              disabled={searching}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition cursor-pointer active:scale-95"
            >
              {searching ? 'Querying...' : 'Search'}
            </button>
            {searchResults !== null && (
              <button
                type="button"
                onClick={clearSearch}
                className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg text-sm font-medium transition cursor-pointer active:scale-95"
              >
                Clear
              </button>
            )}
          </form>
        </div>

        {/* Tab switcher */}
        <div className="flex gap-3 mt-6 border-b border-slate-700">
          <button
            type="button"
            onClick={() => { setActiveTab('products'); setSearchResults(null); }}
            className={`pb-3 px-2 font-medium text-sm border-b-2 transition flex items-center gap-2 cursor-pointer active:scale-95 ${
              activeTab === 'products'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-300'
            }`}
          >
            <Layers size={16} /> Products ({products.length})
          </button>
          <button
            type="button"
            onClick={() => { setActiveTab('services'); setSearchResults(null); }}
            className={`pb-3 px-2 font-medium text-sm border-b-2 transition flex items-center gap-2 cursor-pointer active:scale-95 ${
              activeTab === 'services'
                ? 'border-blue-500 text-blue-400'
                : 'border-transparent text-slate-400 hover:text-slate-300'
            }`}
          >
            <ExternalLink size={16} /> Professional Services ({services.length})
          </button>
        </div>
      </div>

      {/* Search results banner if active */}
      {searchResults !== null && (
        <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4 text-blue-200 text-sm flex justify-between items-center">
          <span>
            RAG Semantic Match for <strong>"{searchQuery}"</strong>: {searchResults.length} verified item(s) found.
          </span>
          <button type="button" onClick={clearSearch} className="text-xs text-blue-400 hover:underline cursor-pointer">Show all</button>
        </div>
      )}

      {/* Content area */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 bg-slate-800/40 border border-slate-700/60 rounded-xl">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mb-4"></div>
          <span className="text-slate-400 text-sm font-medium">Loading verified catalog from RAG service...</span>
        </div>
      ) : activeTab === 'products' ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {(searchResults ? searchResults.map(r => r.product || r) : products).map((product: KBProduct) => (
            <div key={product.id} className="bg-slate-800 border border-slate-700 rounded-xl p-6 hover:border-slate-600 transition flex flex-col justify-between">
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <span className="text-xs font-mono font-bold text-blue-400 uppercase tracking-wider bg-blue-950/60 px-2.5 py-1 rounded-md border border-blue-800">
                      {product.id}
                    </span>
                    <h2 className="text-xl font-bold text-white mt-2">{product.name}</h2>
                    <span className="text-xs text-slate-400">{product.category}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-bold text-green-400 bg-green-950/60 px-3 py-1.5 rounded-lg border border-green-800 block">
                      {product.pricing}
                    </span>
                  </div>
                </div>

                <p className="text-slate-300 text-sm mb-4 leading-relaxed">{product.description}</p>

                {/* Features */}
                <div className="mb-4">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Verified Features</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                    {(product.features || []).map((feat, idx) => (
                      <div key={idx} className="flex items-center gap-1.5 text-xs text-slate-300">
                        <Check size={13} className="text-emerald-400 flex-shrink-0" />
                        <span>{feat}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Badges footer */}
              <div className="pt-4 border-t border-slate-700/80 flex flex-wrap gap-2 items-center text-xs">
                {product.implementation_timeline && (
                  <span className="inline-flex items-center gap-1 bg-slate-700 px-2.5 py-1 rounded text-slate-300">
                    <Clock size={12} className="text-amber-400" /> Timeline: {product.implementation_timeline}
                  </span>
                )}
                {product.uptime_sla && (
                  <span className="inline-flex items-center gap-1 bg-slate-700 px-2.5 py-1 rounded text-slate-300">
                    <ShieldCheck size={12} className="text-blue-400" /> SLA: {product.uptime_sla}
                  </span>
                )}
                {(product.certifications || []).map((cert, idx) => (
                  <span key={idx} className="bg-purple-900/40 border border-purple-800 text-purple-300 px-2 py-0.5 rounded">
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
            <div key={service.id} className="bg-slate-800 border border-slate-700 rounded-xl p-6 hover:border-slate-600 transition flex flex-col justify-between">
              <div>
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <span className="text-xs font-mono font-bold text-purple-400 uppercase tracking-wider bg-purple-950/60 px-2.5 py-1 rounded-md border border-purple-800">
                      {service.id}
                    </span>
                    <h2 className="text-xl font-bold text-white mt-2">{service.name}</h2>
                    <span className="text-xs text-slate-400">{service.category}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-bold text-green-400 bg-green-950/60 px-3 py-1.5 rounded-lg border border-green-800 block">
                      {service.pricing}
                    </span>
                  </div>
                </div>

                <p className="text-slate-300 text-sm mb-4 leading-relaxed">{service.description}</p>

                {service.deliverables && (
                  <div className="mb-4">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2">Deliverables</h3>
                    <div className="space-y-1">
                      {service.deliverables.map((del, idx) => (
                        <div key={idx} className="flex items-center gap-1.5 text-xs text-slate-300">
                          <Check size={13} className="text-purple-400 flex-shrink-0" />
                          <span>{del}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              <div className="pt-4 border-t border-slate-700/80 flex flex-wrap gap-2 items-center text-xs">
                {service.delivery_timeline && (
                  <span className="inline-flex items-center gap-1 bg-slate-700 px-2.5 py-1 rounded text-slate-300">
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
