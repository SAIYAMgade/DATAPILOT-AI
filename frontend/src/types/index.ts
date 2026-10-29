export interface ExecutiveMetrics {
  period: {
    start_date: string;
    end_date: string;
    comparison_start: string;
    comparison_end: string;
  };
  metrics: {
    total_revenue: number;
    previous_revenue: number;
    revenue_growth_pct: number;
    average_order_value: number;
    aov_growth_pct: number;
    total_orders: number;
    transacting_customers: number;
    active_customers_30d: number;
    total_registered_customers: number;
    new_acquired_customers: number;
    high_risk_customers: number;
  };
}

export interface TimeSeriesItem {
  period: string;
  revenue: number;
  transaction_count: number;
  average_amount: number;
  active_accounts: number;
  prev_period_revenue: number;
  growth_pct: number;
}

export interface Breakdowns {
  by_category: Array<{ name: string; orders: number; revenue: number; aov: number }>;
  by_channel: Array<{ channel: string; customers: number; orders: number; revenue: number }>;
  by_region: Array<{ region: string; customers: number; revenue: number }>;
}

export interface ParetoData {
  concentration_points: Array<{ rank: number; customer_pct: number; cumulative_revenue_pct: number }>;
  top_20_pct_generates: number;
  interpretation: string;
}

export interface CustomerItem {
  id: number;
  customer_ref: string;
  name: string;
  email: string | null;
  segment: string;
  acquisition_channel: string;
  region: string;
  signup_date: string | null;
  is_active: boolean;
  total_orders: number;
  total_spent: number;
  last_order_date: string | null;
  risk_score: number | null;
  risk_category: string | null;
  priority_score: number | null;
}

export interface CustomerDetail {
  customer: {
    id: number;
    customer_ref: string;
    name: string;
    email: string | null;
    segment: string;
    acquisition_channel: string;
    region: string;
    signup_date: string | null;
    is_active: boolean;
  };
  transactions: Array<{
    id: number;
    transaction_ref: string;
    timestamp: string;
    amount: number;
    status: string;
    payment_method: string;
    is_refund: boolean;
    category: string | null;
  }>;
  recent_prediction?: {
    risk_score: number;
    risk_category: string;
    priority_score: number;
    details: any;
    timestamp: string;
  } | null;
}

export interface CohortData {
  retention_matrix: Array<Record<string, any>>;
  revenue_matrix: Array<Record<string, any>>;
  period_columns: string[];
  cohort_summary: Array<{
    cohort: string;
    initial_size: number;
    total_revenue: number;
    revenue_per_customer: number;
    month_1_retention_pct: number | null;
    months_observed: number;
  }>;
  definition: string;
}

export interface SegmentationData {
  summary: Array<{
    segment: string;
    customer_count: number;
    total_revenue: number;
    avg_revenue_per_customer: number;
    avg_orders_per_customer: number;
  }>;
  thresholds: Record<string, any>;
  sample_customers: Array<any>;
  total_evaluated: number;
}

export interface StatisticalTestResult {
  business_question: string;
  null_hypothesis: string;
  alternative_hypothesis: string;
  test_applied: string;
  test_statistic?: number;
  p_value?: number;
  effect_size?: {
    metric: string;
    value: number;
    magnitude: string;
  };
  statistically_significant?: boolean;
  interpretation?: string;
  assumptions_and_limitations: string[];
  group_summaries?: Record<string, any>;
  sample_sizes?: Record<string, number>;
  contingency_table?: Record<string, any>;
  degrees_of_freedom?: number;
  error?: string;
}

export interface ModelVersionItem {
  id: number;
  version_tag: string;
  model_type: string;
  observation_days: number;
  prediction_days: number;
  threshold: number;
  is_active: boolean;
  metrics: {
    roc_auc: number;
    pr_auc: number;
    brier_score: number;
    precision: number;
    recall: number;
    f1_score: number;
    confusion_matrix: {
      true_negatives: number;
      false_positives: number;
      false_negatives: number;
      true_positives: number;
    };
    threshold_tradeoff_curve?: Array<{ threshold: number; precision: number; recall: number; f1: number }>;
  };
  feature_importance: Array<{ feature: string; importance: number }>;
  created_at: string;
}

export interface PrioritizedCustomer {
  customer_id: number;
  customer_ref: string;
  name: string;
  email: string | null;
  segment: string;
  risk_score: number;
  risk_category: string;
  priority_score: number;
  historical_value: number;
  recency_days: number;
  frequency: number;
  recommended_action: string;
}

export interface BusinessInsightItem {
  id: number;
  title: string;
  category: string;
  metric_name: string;
  comparison_period: string;
  current_value: number;
  previous_value: number | null;
  change_pct: number | null;
  severity: "info" | "warning" | "critical";
  supporting_evidence: Record<string, any>;
  limitations: string;
  created_at: string;
}

export interface IngestionBatch {
  id: number;
  batch_ref: string;
  source_type: string;
  records_received: number;
  records_accepted: number;
  records_rejected: number;
  status: string;
  rejection_summary: any;
  created_at: string;
}
