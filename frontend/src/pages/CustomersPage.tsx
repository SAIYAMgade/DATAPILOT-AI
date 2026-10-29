import React, { useEffect, useState } from 'react';
import { Search, Filter, ChevronLeft, ChevronRight, X, ExternalLink, ShieldAlert, CheckCircle } from 'lucide-react';
import { api } from '../services/api';
import { CustomerItem, CustomerDetail } from '../types';

export const CustomersPage: React.FC = () => {
  const [customers, setCustomers] = useState<CustomerItem[]>([]);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [segment, setSegment] = useState('');
  const [channel, setChannel] = useState('');
  const [loading, setLoading] = useState(true);
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(null);
  const [customerDetail, setCustomerDetail] = useState<CustomerDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    loadCustomers();
  }, [page, segment, channel]);

  const loadCustomers = async () => {
    try {
      setLoading(true);
      const res = await api.getCustomers({
        page,
        page_size: 20,
        search: search || undefined,
        segment: segment || undefined,
        channel: channel || undefined,
      });
      setCustomers(res.customers);
      setTotalPages(res.total_pages);
      setTotalCount(res.total_count);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadCustomers();
  };

  const openCustomerModal = async (id: number) => {
    try {
      setSelectedCustomerId(id);
      setDetailLoading(true);
      const detail = await api.getCustomerDetail(id);
      setCustomerDetail(detail);
    } catch (err) {
      console.error(err);
    } finally {
      setDetailLoading(false);
    }
  };

  return (
    <div className="p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-slate-100">Customer Explorer & Activity Profiles</h2>
        <p className="text-xs text-slate-400 mt-1">
          Search and inspect individual customer transaction histories, segment assignments, and ML churn predictions.
        </p>
      </div>

      {/* Filters Toolbar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-slate-900 p-4 rounded-xl border border-slate-800">
        <form onSubmit={handleSearchSubmit} className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search account name, reference, or email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-400 focus:outline-none focus:border-indigo-500"
          />
        </form>

        <div className="flex items-center gap-3">
          <select
            value={segment}
            onChange={(e) => { setSegment(e.target.value); setPage(1); }}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 focus:outline-none"
          >
            <option value="">All Segments</option>
            <option value="VIP">VIP</option>
            <option value="Frequent">Frequent</option>
            <option value="Declining">Declining</option>
            <option value="New">New</option>
            <option value="Inactive">Inactive</option>
            <option value="Irregular">Irregular</option>
          </select>

          <select
            value={channel}
            onChange={(e) => { setChannel(e.target.value); setPage(1); }}
            className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-slate-300 focus:outline-none"
          >
            <option value="">All Channels</option>
            <option value="Organic">Organic</option>
            <option value="Direct Sales">Direct Sales</option>
            <option value="Partner Referral">Partner Referral</option>
            <option value="Paid Search">Paid Search</option>
            <option value="Events">Events</option>
          </select>
        </div>
      </div>

      {/* Customers Table */}
      <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 border-b border-slate-800 text-slate-400 font-medium">
              <tr>
                <th className="py-3 px-4">Account Reference</th>
                <th className="py-3 px-4">Name</th>
                <th className="py-3 px-4">Segment</th>
                <th className="py-3 px-4">Channel</th>
                <th className="py-3 px-4 text-right">Orders</th>
                <th className="py-3 px-4 text-right">Total Revenue</th>
                <th className="py-3 px-4">Last Order</th>
                <th className="py-3 px-4">Churn Risk</th>
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-300">
              {loading ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400 font-mono">
                    Loading records from database...
                  </td>
                </tr>
              ) : customers.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400">
                    No customers match the current search filters.
                  </td>
                </tr>
              ) : (
                customers.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-mono font-medium text-indigo-400">
                      {c.customer_ref}
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-200">
                      <div>{c.name}</div>
                      <div className="text-[10px] text-slate-400">{c.email}</div>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-800 border border-slate-700 text-slate-300">
                        {c.segment}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-400">{c.acquisition_channel}</td>
                    <td className="py-3 px-4 text-right font-mono">{c.total_orders}</td>
                    <td className="py-3 px-4 text-right font-mono font-medium text-slate-100">
                      ${c.total_spent.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-400">{c.last_order_date || 'None'}</td>
                    <td className="py-3 px-4">
                      {c.risk_category ? (
                        <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${
                          c.risk_category === 'High'
                            ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            : c.risk_category === 'Medium'
                            ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                            : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                        }`}>
                          {c.risk_category} ({((c.risk_score || 0) * 100).toFixed(0)}%)
                        </span>
                      ) : (
                        <span className="text-slate-400 text-[10px]">Unscored</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => openCustomerModal(c.id)}
                        className="p-1 hover:text-indigo-400 text-slate-400 transition"
                        title="View Customer Profile"
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing <span className="text-slate-200 font-mono">{customers.length}</span> of{' '}
            <span className="text-slate-200 font-mono">{totalCount}</span> accounts
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page === 1}
              className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <span className="font-mono text-slate-300">Page {page} of {totalPages}</span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page === totalPages}
              className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 disabled:opacity-40 transition"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Customer Detail Modal */}
      {selectedCustomerId && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
              <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
                <span>Account Profile</span>
                {customerDetail && (
                  <span className="font-mono text-indigo-400 text-xs font-normal">
                    ({customerDetail.customer.customer_ref})
                  </span>
                )}
              </h3>
              <button
                onClick={() => { setSelectedCustomerId(null); setCustomerDetail(null); }}
                className="text-slate-400 hover:text-slate-200 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-6 flex-1 text-xs">
              {detailLoading || !customerDetail ? (
                <div className="py-12 flex justify-center">
                  <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : (
                <>
                  {/* Account Summary Cards */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                      <div className="text-slate-400 text-[10px]">Segment</div>
                      <div className="font-semibold text-slate-200 mt-0.5">{customerDetail.customer.segment}</div>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                      <div className="text-slate-400 text-[10px]">Channel</div>
                      <div className="font-semibold text-slate-200 mt-0.5">{customerDetail.customer.acquisition_channel}</div>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                      <div className="text-slate-400 text-[10px]">Region</div>
                      <div className="font-semibold text-slate-200 mt-0.5">{customerDetail.customer.region}</div>
                    </div>
                    <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                      <div className="text-slate-400 text-[10px]">Member Since</div>
                      <div className="font-mono text-slate-200 mt-0.5">{customerDetail.customer.signup_date}</div>
                    </div>
                  </div>

                  {/* Prediction Card */}
                  {customerDetail.recent_prediction && (
                    <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-200 flex items-center gap-1.5">
                          <ShieldAlert className="w-4 h-4 text-amber-400" />
                          Churn Risk Assessment
                        </span>
                        <span className="text-[10px] font-mono text-slate-400">
                          Freshness: {customerDetail.recent_prediction.timestamp}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 pt-1">
                        <div>
                          <div className="text-[10px] text-slate-400">Risk Probability</div>
                          <div className="text-lg font-bold font-mono text-amber-400">
                            {(customerDetail.recent_prediction.risk_score * 100).toFixed(1)}%
                          </div>
                        </div>
                        <div>
                          <div className="text-[10px] text-slate-400">Priority Score</div>
                          <div className="text-lg font-bold font-mono text-slate-100">
                            {customerDetail.recent_prediction.priority_score}
                          </div>
                        </div>
                      </div>
                      <div className="pt-2 text-slate-300 text-[11px] border-t border-slate-800/80">
                        <span className="text-slate-400">Recommended Action: </span>
                        {customerDetail.recent_prediction.details?.recommended_action || 'Monitor normally.'}
                      </div>
                    </div>
                  )}

                  {/* Transaction History */}
                  <div className="space-y-3">
                    <h4 className="font-semibold text-slate-200">Recent Transactions ({customerDetail.transactions.length})</h4>
                    <div className="max-h-48 overflow-y-auto border border-slate-800 rounded-lg">
                      <table className="w-full text-left text-[11px]">
                        <thead className="bg-slate-950/80 border-b border-slate-800 text-slate-400 sticky top-0">
                          <tr>
                            <th className="py-2 px-3">Date</th>
                            <th className="py-2 px-3">Reference</th>
                            <th className="py-2 px-3">Category</th>
                            <th className="py-2 px-3 text-right">Amount</th>
                            <th className="py-2 px-3 text-center">Status</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800 text-slate-300">
                          {customerDetail.transactions.map((tx) => (
                            <tr key={tx.id} className="hover:bg-slate-800/30">
                              <td className="py-2 px-3 font-mono">{tx.timestamp?.split(' ')[0]}</td>
                              <td className="py-2 px-3 font-mono text-slate-400">{tx.transaction_ref}</td>
                              <td className="py-2 px-3">{tx.category || 'General'}</td>
                              <td className="py-2 px-3 text-right font-mono">${tx.amount.toFixed(2)}</td>
                              <td className="py-2 px-3 text-center">
                                <span className={`px-1.5 py-0.2 rounded text-[9px] font-mono ${
                                  tx.status === 'completed' ? 'text-emerald-400 bg-emerald-500/10' : 'text-rose-400 bg-rose-500/10'
                                }`}>
                                  {tx.status}
                                </span>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
