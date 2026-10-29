import {
  ExecutiveMetrics, TimeSeriesItem, Breakdowns, ParetoData, CustomerItem, CustomerDetail,
  CohortData, SegmentationData, StatisticalTestResult, ModelVersionItem, PrioritizedCustomer,
  BusinessInsightItem, IngestionBatch
} from '../types';

const BASE_URL = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${url}`, options);
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(errorText || `Request failed with status ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Metrics
  getExecutiveSummary: (startDate?: string, endDate?: string) => {
    const params = new URLSearchParams();
    if (startDate) params.set('start_date', startDate);
    if (endDate) params.set('end_date', endDate);
    const query = params.toString() ? `?${params.toString()}` : '';
    return fetchJson<ExecutiveMetrics>(`/metrics/summary${query}`);
  },

  getTimeSeries: (granularity: 'monthly' | 'weekly' = 'monthly') =>
    fetchJson<TimeSeriesItem[]>(`/metrics/time-series?granularity=${granularity}`),

  getBreakdowns: () =>
    fetchJson<Breakdowns>('/metrics/breakdowns'),

  getPareto: () =>
    fetchJson<ParetoData>('/metrics/pareto'),

  // Customers
  getCustomers: (params: { page?: number; page_size?: number; search?: string; segment?: string; channel?: string; region?: string }) => {
    const sp = new URLSearchParams();
    if (params.page) sp.set('page', params.page.toString());
    if (params.page_size) sp.set('page_size', params.page_size.toString());
    if (params.search) sp.set('search', params.search);
    if (params.segment) sp.set('segment', params.segment);
    if (params.channel) sp.set('channel', params.channel);
    if (params.region) sp.set('region', params.region);
    return fetchJson<{ page: number; page_size: number; total_count: number; total_pages: number; customers: CustomerItem[] }>(`/customers?${sp.toString()}`);
  },

  getCustomerDetail: (id: number) =>
    fetchJson<CustomerDetail>(`/customers/${id}`),

  // Segmentation
  getSegmentation: () =>
    fetchJson<SegmentationData>('/segmentation/rfm'),

  // Cohorts
  getCohortMatrix: () =>
    fetchJson<CohortData>('/cohorts/matrix'),

  // Statistics
  getSegmentComparison: (groupCol: string = 'acquisition_channel') =>
    fetchJson<StatisticalTestResult>(`/stats/segment-comparison?group_col=${groupCol}`),

  getChannelRetentionTest: () =>
    fetchJson<StatisticalTestResult>('/stats/channel-retention'),

  getConfidenceIntervals: (confidence: number = 0.95) =>
    fetchJson<any>(`/stats/confidence-intervals?confidence=${confidence}`),

  getRevenueTrend: () =>
    fetchJson<StatisticalTestResult>('/stats/revenue-trend'),

  // Machine Learning
  getModelVersions: () =>
    fetchJson<ModelVersionItem[]>('/ml/versions'),

  getActiveModel: () =>
    fetchJson<{ active: boolean; id?: number; version_tag?: string; model_type?: string; metrics?: any; feature_importance?: any }>('/ml/active'),

  trainModel: (modelType: string, observationDays: number = 90, predictionDays: number = 60, targetRecall: number = 0.75) =>
    fetchJson<any>('/ml/train', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model_type: modelType,
        observation_days: observationDays,
        prediction_days: predictionDays,
        target_recall: targetRecall
      })
    }),

  getPredictions: (limit: number = 50) =>
    fetchJson<{
      model_version: string;
      decision_threshold: number;
      total_customers_scored: number;
      high_risk_count: number;
      prioritized_customers: PrioritizedCustomer[];
      formula_documentation: string;
    }>(`/ml/predictions?limit=${limit}`),

  // Insights
  getInsights: () =>
    fetchJson<BusinessInsightItem[]>('/insights'),

  refreshInsights: () =>
    fetchJson<BusinessInsightItem[]>('/insights/refresh', { method: 'POST' }),

  // Ingestion & Quality
  getBatches: () =>
    fetchJson<IngestionBatch[]>('/ingestion/batches'),

  getBatchRejections: (batchId: number) =>
    fetchJson<{ batch_ref: string; total_rejected: number; sample: any[] }>(`/ingestion/batches/${batchId}/rejections`),

  generateAndSeed: (nCustomers: number = 350, seed: number = 42, corrupt: boolean = false) =>
    fetchJson<any>('/ingestion/generate-and-seed', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        n_customers: nCustomers,
        seed: seed,
        corrupt: corrupt,
        corruption_rate: corrupt ? 0.08 : 0.0
      })
    }),

  // AI Assistant
  queryAssistant: (question: string) =>
    fetchJson<{ question: string; intent: string; answer: string; data: any; limitations: string }>('/assistant/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    })
};
