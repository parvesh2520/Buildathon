import { useState, useEffect } from 'react';
import { BookOpen, Search, X, Sparkles, Database, FileText } from 'lucide-react';
import { getRAGDocuments, queryRAGKnowledge } from '@/api/system';
import toast from 'react-hot-toast';
import { cn } from '@/lib/utils';

interface KnowledgeBaseModalProps {
  onClose: () => void;
}

export function KnowledgeBaseModal({ onClose }: KnowledgeBaseModalProps) {
  const [loading, setLoading] = useState(true);
  const [documents, setDocuments] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [querying, setQuerying] = useState(false);
  const [searchResults, setSearchResults] = useState<any[] | null>(null);

  useEffect(() => {
    getRAGDocuments()
      .then((data) => setDocuments(data.documents || []))
      .catch(() => toast.error('Failed to load knowledge base'))
      .finally(() => setLoading(false));
  }, []);

  const handleTestQuery = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setQuerying(true);
    try {
      const data = await queryRAGKnowledge(searchQuery, 3);
      setSearchResults(data.retrieved_chunks || []);
      toast.success(`Retrieved ${data.retrieved_chunks?.length || 0} semantic context chunks`);
    } catch {
      toast.error('RAG semantic query failed');
    } finally {
      setQuerying(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col overflow-hidden border border-border">
        {/* Header */}
        <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-slate-50">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-brand/10 text-brand flex items-center justify-center">
              <Database size={16} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900">Campaign Knowledge Base & Vector RAG</h3>
              <p className="text-2xs text-slate-500">
                Grounds AI agents in verified product specs, sales playbooks, case studies, and objection handling.
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 p-1.5 rounded hover:bg-slate-200/50">
            <X size={16} />
          </button>
        </div>

        {/* Semantic Query Tester */}
        <div className="p-5 border-b border-border bg-gradient-to-r from-brand/5 to-white">
          <form onSubmit={handleTestQuery} className="space-y-2">
            <label className="text-2xs font-bold text-slate-700 uppercase tracking-wide flex items-center gap-1.5">
              <Sparkles size={12} className="text-brand" /> Test Agent Semantic RAG Retrieval
            </label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                <input
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="e.g. How does our pricing scale for SaaS teams? Or gatekeeper objection..."
                  className="input pl-8 text-xs"
                />
              </div>
              <button
                type="submit"
                disabled={querying}
                className="btn-primary text-xs px-4"
              >
                {querying ? 'Searching...' : 'Test Retrieval'}
              </button>
            </div>
          </form>

          {/* Search results */}
          {searchResults && (
            <div className="mt-4 p-3 bg-white border border-brand/20 rounded-xl space-y-2">
              <div className="flex items-center justify-between text-2xs font-semibold text-slate-500">
                <span>Retrieved Context Chunks (Passed to Personalisation Agent)</span>
                <button
                  onClick={() => setSearchResults(null)}
                  className="text-brand hover:underline"
                >
                  Clear
                </button>
              </div>
              <div className="space-y-2">
                {searchResults.map((r, i) => (
                  <div key={i} className="p-2.5 rounded-lg bg-surface-secondary text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-800">{r.title}</span>
                      <span className="text-3xs font-mono bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded font-bold">
                        Cosine Match: {(r.similarity_score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-slate-600 text-2xs leading-relaxed">{r.content}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Documents list */}
        <div className="p-6 overflow-y-auto space-y-3 flex-1">
          <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wide">
            Indexed Campaign Knowledge Documents ({documents.length})
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {documents.map((doc) => (
              <div key={doc.id} className="card p-4 space-y-2 border border-border hover:border-brand/30 transition-all">
                <div className="flex items-center justify-between">
                  <span className="text-3xs uppercase font-bold px-1.5 py-0.5 rounded bg-brand/10 text-brand">
                    {doc.category}
                  </span>
                  <span className="text-3xs text-slate-400 font-mono">1536-dim vector</span>
                </div>
                <h5 className="text-xs font-bold text-slate-900">{doc.title}</h5>
                <p className="text-2xs text-slate-600 line-clamp-3 leading-relaxed">{doc.content}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-border bg-slate-50 flex items-center justify-between text-2xs text-slate-500">
          <span>Retrieval-Augmented Generation (RAG) prevents agent hallucinations</span>
          <button onClick={onClose} className="btn-secondary text-xs px-3 py-1">
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
