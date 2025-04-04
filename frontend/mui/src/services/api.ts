import axios from 'axios';
import { SearchQuery, SearchResult, SearchType } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const searchProducts = async (query: SearchQuery): Promise<SearchResult[]> => {
  try {
    const response = await axios.post<SearchResult[]>(`${API_URL}/api/search`, query);
    return response.data;
  } catch (error) {
    console.error('Error searching products:', error);
    throw error;
  }
};

export const getSearchMethods = async (): Promise<string[]> => {
  try {
    const response = await axios.get<string[]>(`${API_URL}/api/search/methods`);
    return response.data;
  } catch (error) {
    console.error('Error getting search methods:', error);
    throw error;
  }
};

// Helper function to classify search query type
export const classifySearchQuery = async (query: string): Promise<{
  type: SearchType;
  explanation: string;
  confidence: string;
  search_strategy: string;
  examples: string[];
  support_answer?: string;
}> => {
  try {
    const response = await axios.get<{
      type: string;
      explanation: string;
      confidence: string;
      search_strategy: string;
      examples: string[];
      support_answer?: string;
    }>(`${API_URL}/api/search/classify?query=${encodeURIComponent(query)}`);

    // Map the response type to SearchType enum
    const searchType = response.data.type === 'keyword' ? SearchType.KEYWORD :
                      response.data.type === 'semantic' ? SearchType.SEMANTIC :
                      response.data.type === 'customer_support' ? SearchType.CUSTOMER_SUPPORT :
                      SearchType.KEYWORD;

    return {
      ...response.data,
      type: searchType
    };
  } catch (error) {
    console.error('Error classifying query:', error);
    // Return a default classification
    return {
      type: SearchType.KEYWORD,
      explanation: 'Error during classification, defaulting to keyword search',
      confidence: 'low',
      search_strategy: 'keyword',
      examples: [],
      support_answer: undefined
    };
  }
};

// Function to generate search explanation based on query type
export const generateSearchExplanation = (query: string, searchType: SearchType): string => {
  switch (searchType) {
    case SearchType.KEYWORD:
      return `I'll search for "${query}" using keyword matching (BM25) with this Elasticsearch query:
\`\`\`json
{
  "query": {
    "multi_match": {
      "query": "${query}",
      "fields": ["name^2", "description", "category", "brand"],
      "type": "best_fields",
      "operator": "and"
    }
  }
}
\`\`\``;
    case SearchType.SEMANTIC:
      return `I'll search for "${query}" using semantic understanding (vector search) with this Elasticsearch query:
\`\`\`json
{
  "_source": true,
  "knn": {
    "field": "text_embedding",
    "query_vector": "${query}",
    "k": 10,
    "num_candidates": 100
  }
}
\`\`\``;
    case SearchType.CUSTOMER_SUPPORT:
      return `I'll help answer your question about "${query}" and find relevant products if needed. I'll use this Elasticsearch query:
\`\`\`json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "category": "support" } },
        { 
          "multi_match": {
            "query": "${query}",
            "fields": ["question^3", "answer^2", "keywords"]
          }
        }
      ]
    }
  },
  "size": 5
}
\`\`\``;
    default:
      return `I'll search for "${query}" using the default search method.`;
  }
};

// Function to upload an image file for OCR processing and product recommendations
export const uploadImage = async (file: File, userId?: string, limit: number = 10): Promise<SearchResult[]> => {
  try {
    const formData = new FormData();
    formData.append('image_file', file);
    if (userId) formData.append('user_id', userId);
    formData.append('limit', limit.toString());
    
    const response = await axios.post<SearchResult[]>(`${API_URL}/api/search/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  } catch (error) {
    console.error('Error uploading image:', error);
    throw error;
  }
};

export const getRandomProducts = async (count: number = 4): Promise<SearchResult[]> => {
  try {
    const response = await axios.get<SearchResult[]>(`${API_URL}/api/search/random?count=${count}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching random products:', error);
    return [];
  }
};
