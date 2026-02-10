// User interfaces
export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'analyst' | 'manager';
  isActive: boolean;
  createdAt: string;
  lastLogin?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface AuthToken {
  accessToken: string;
  tokenType: string;
}

// Dashboard interfaces
export interface TriggerRate {
  triggerType: string;
  rate: number;
  count: number;
  targetMin: number;
  targetMax: number;
  status: 'within_target' | 'below_target' | 'above_target';
}

export interface ExecutiveKPIs {
  floodTriggerRate: TriggerRate;
  droughtTriggerRate: TriggerRate;
  cropFailureTriggerRate: TriggerRate;
  combinedTriggerRate: number;
  lossRatio: number;
  sustainabilityStatus: 'sustainable' | 'warning' | 'unsustainable';
  totalTriggersYtd: number;
  estimatedPayoutsYtd: number;
}

// Model interfaces
export interface ModelMetrics {
  modelName: string;
  r2Score: number;
  rmse: number;
  mae: number;
  mape: number;
  trainingDate: string;
  experimentId: string;
  // Cross-validation metrics (more reliable)
  cvR2Mean?: number;
  cvR2Std?: number;
  cvR2CiLower?: number;
  cvR2CiUpper?: number;
  cvRmseMean?: number;
  cvRmseStd?: number;
  cvMaeMean?: number;
  cvMaeStd?: number;
  cvNSplits?: number;
  // Feature selection info
  nFeatures?: number;
  featureToSampleRatio?: number;
  // Sample counts (for dynamic metrics)
  trainingSamples?: number;
  valSamples?: number;
  testSamples?: number;
  // Model configuration
  hyperparameters?: Record<string, any>;
}

export interface FeatureImportance {
  featureName: string;
  importance: number;
  rank: number;
}

export interface ModelComparison {
  models: ModelMetrics[];
  bestModel: string;
  comparisonMetric: string;
}

// Trigger interfaces
export interface TriggerEvent {
  id: number;
  date: string;
  triggerType: string;
  confidence: number;
  severity: number;
  payoutAmount: number;
  locationLat?: number;
  locationLon?: number;
  location?: string;  // Location name from backend
}

export interface TriggerForecast {
  targetDate: string;
  triggerType: string;
  probability: number;
  confidenceLower: number;
  confidenceUpper: number;
}

export interface EarlyWarning {
  alertType: string;
  severity: 'low' | 'medium' | 'high';
  message: string;
  triggerProbability: number;
  targetDate: string;
  recommendedAction: string;
}

// Climate interfaces
export interface TimeSeriesPoint {
  date: string;
  median: number;
  min: number;
  max: number;
  value?: number; // Deprecated, for backward compatibility
}

export interface ClimateTimeSeries {
  variable: string;
  data: TimeSeriesPoint[];
}

export interface Anomaly {
  date: string;
  variable: string;
  value: number;
  expectedValue: number;
  deviation: number;
}

// Risk interfaces
export interface PortfolioMetrics {
  totalPremiumIncome: number;
  expectedPayouts: number;
  lossRatio: number;
  totalExposure: number;
  numberOfPolicies: number;
  totalFarmers?: number; // Mapped from total_farmers
  reserves?: number; // Added for dashboard
}

export interface ScenarioResult {
  scenarioName: string;
  expectedPayouts: number;
  lossRatio: number;
  triggerProbability: number;
  impact: string;
}

// Chart data interfaces
export interface ChartData {
  x: (string | number)[];
  y: (string | number)[];
  type: 'scatter' | 'bar' | 'line';
  name?: string;
  mode?: string;
  marker?: any;
}
