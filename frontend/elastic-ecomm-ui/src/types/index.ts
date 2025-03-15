export interface SearchQuery {
  query: string;
  user_id?: string;
  limit?: number;
}

export enum SearchType {
  BM25 = "bm25",
  VECTOR = "vector",
  CUSTOMER_SUPPORT = "customer_support",
  IMAGE = "image"
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
  alternatives?: Array<{[key: string]: string}>;
  explanation?: string;
}

export interface Message {
  id: number;
  text: string;
  sender: 'customer' | 'agent';
  timestamp: Date;
  type?: 'query_classification' | 'search_query' | 'search_results' | 'general';
}

export interface ChatState {
  messages: Message[];
  searchResults: SearchResult[];
  isSearching: boolean;
}
