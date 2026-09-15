export interface User {
  id: number;
  name: string;
  email: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Conversation {
  id: number;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

export interface ConversationDetail
  extends Conversation {
  messages: Message[];
}

export interface AgentMetadata {
  action: "final_answer" | "tool" | null;
  tool_name: string | null;
  status: string | null;
  verification_required: boolean;
  verification_action_id: number | null;
  verification_status: string | null;
}

export interface ChatResponse {
  conversation_id: number;
  user_message_id: number;
  assistant_message_id: number;
  response: string;
  created_at: string;

  agent?: AgentMetadata | null;
}

export interface Memory {
  id: number;
  memory_type: string;
  content: string;
  importance: number;
  confidence: number;
  source_type: string;
  source_id: string | null;
  is_active: boolean;
  confirmation_count: number;
  created_at: string;
  updated_at: string;
}

export interface MemorySearchResult {
  id: number;
  memory_type: string;
  content: string;
  importance: number;
  confidence: number;
  confirmation_count: number;
  similarity_distance: number | null;
  source_type: string;
  source_id: string | null;
}

export interface MemorySearchResponse {
  query: string;
  results: MemorySearchResult[];
}

export interface MemoryConflict {
  id: number;
  old_memory_id: number;
  new_memory_id: number;
  winning_memory_id: number | null;
  comparison_type: string;
  conflict_type: string | null;
  old_confidence: number;
  new_confidence: number;
  old_score: number;
  new_score: number;
  resolution: string;
  reason: string;
  created_at: string;
  resolved_at: string | null;
}

export interface MemoryIntelligenceSummary {
  total_conflicts: number;
  new_memory_wins: number;
  existing_memory_wins: number;
  latest_conflict_at: string | null;
}

export interface Document {
  id: number;
  filename: string;
  content_type: string;
  file_size: number;
  chunks: number;
  created_at: string;
}

export interface DocumentSearchResult {
  document_id: number;
  filename: string;
  chunk_index: number;
  content: string;
  similarity: number;
}

export interface VerificationAction {
  id: number;
  user_id: number;

  tool_name:
    | "send_email"
    | "create_calendar_event"
    | "update_calendar_event"
    | "delete_calendar_event"
    | string;

  action_type: string;
  request: string;

  status:
    | "PENDING"
    | "APPROVED"
    | "REJECTED"
    | "EXECUTING"
    | "VERIFIED"
    | "FAILED"
    | string;

  result: string | null;
  evidence: string | null;
  error: string | null;

  created_at: string;
  approved_at: string | null;
  rejected_at: string | null;
  executing_at: string | null;
  completed_at: string | null;
}

export interface GoogleConnection {
  id?: number;
  provider?: string;
  email?: string;
  connected?: boolean;
}