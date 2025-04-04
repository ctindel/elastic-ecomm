export interface Message {
  id: number;
  text: string;
  sender: 'customer' | 'agent';
  timestamp: Date;
  type?: 'general' | 'query_classification' | 'search_query' | 'search_results' | 'file_upload' | 'error' | 'support_answer';
  file?: {
    name: string;
    type: string;
  };
}

export interface SearchResult {
  query: string;
  product_id: string;
  product_name: string;
  product_description?: string;
  price?: number;
  image_url?: string;
  score: number;
  search_type: SearchType;
  alternatives?: Array<{
    item: string;
    quantity?: number;
    attributes?: string;
    matched_product_name?: string;
  }>;
  explanation?: string;
}

export interface SearchQuery {
  query: string;
  user_id?: string;
  limit?: number;
}

export enum SearchType {
  KEYWORD = 'keyword',
  SEMANTIC = 'semantic',
  CUSTOMER_SUPPORT = 'customer_support'
} 