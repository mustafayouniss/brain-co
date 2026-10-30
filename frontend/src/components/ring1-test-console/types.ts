export interface TestRunEvent {
  sequence: number;
  timestamp: string;
  run_id: string;
  source_engine: string;
  destination_engine: string;
  capability: string;
  event_type: string;
  status: "running" | "completed" | "failed" | "denied" | "pending" | "blocked";
  duration_ms?: number | null;
  request_envelope?: Record<string, any> | null;
  response_envelope?: Record<string, any> | null;
  plan_version?: number | null;
  details?: Record<string, any>;
}

export interface DelegationEdge {
  source: string;
  target: string;
  capability?: string;
}

export interface PlanStepModel {
  step_id: string;
  capability: string;
  description: string;
  status: string;
  order?: number;
  depends_on?: string[];
  parameters?: Record<string, any>;
  actual_result?: Record<string, any>;
  failure_reason?: string | null;
  skip_reason?: string | null;
}

export interface PlanModel {
  plan_id: string;
  version: number;
  status: string;
  goal: string;
  replan_count: number;
  max_replans: number;
  steps: PlanStepModel[];
  completion_criteria?: string;
}

export interface ReplanDetails {
  plan_id?: string;
  old_version?: number;
  new_version?: number;
  reason?: string;
  steps_retained?: string[];
  steps_added?: PlanStepModel[];
  steps_skipped?: string[];
}

export interface ExtractedEntity {
  name: string;
  entity_type: string;
  page_number: number;
  confidence: number;
}

export interface ExtractedFact {
  fact_id: string;
  statement: string;
  category: string;
  page_number: number;
  source_excerpt: string;
  confidence: number;
  is_validated: boolean;
}

export interface ExtractedObligation {
  obligation_id: string;
  description: string;
  responsible_party?: string | null;
  deadline?: string | null;
  page_number: number;
}

export interface PDFPageContent {
  page_number: number;
  text: string;
  char_count: number;
  word_count: number;
  is_blank: boolean;
}

export interface DocumentStructuredKnowledge {
  document_id: string;
  document_type: string;
  title: string;
  summary: string;
  parties: string[];
  dates_and_events: Array<{ date?: string; event?: string; page_number?: number }>;
  entities: ExtractedEntity[];
  facts: ExtractedFact[];
  obligations: ExtractedObligation[];
  uncertainties: string[];
  total_facts_count: number;
  extraction_mode: string;
}

export interface ScorecardModel {
  processing_outcome: "SUCCESS" | "RECOVERED" | "FAILED" | "BLOCKED";
  pages_processed: number;
  candidate_facts: number;
  validated_facts: number;
  persisted_facts: number;
  retrieved_facts: number;
  isolation_verified: boolean;
  requires_ocr: boolean;
  warnings: string[];
}

export interface SavedKnowledgeRecord {
  record_id: string;
  record_type: string;
  created_at: string | null;
  payload: Record<string, any>;
  case_id: string;
  organization_id: string;
  provenance?: Record<string, any> | null;
}

export interface TestRunSummary {
  run_id: string;
  mode: string;
  status: "idle" | "running" | "completed" | "failed";
  duration_ms?: number;
  total_events: number;
  invoked_engines: string[];
  skipped_engines: string[];
  delegation_edges: DelegationEdge[];
  initial_plan?: PlanModel | null;
  replanned_payload?: ReplanDetails | null;
  current_plan?: PlanModel | null;
  scorecard?: ScorecardModel | null;
  structured_knowledge?: DocumentStructuredKnowledge | null;
  pages?: PDFPageContent[] | null;
}
