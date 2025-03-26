import axios from 'axios';
import { SearchQuery, SearchResult, SearchType } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const searchProducts = async (query: SearchQuery): Promise<SearchResult[]> => {
  try {
    const response = await axios.post<SearchResult[]>(`${API_URL}/api/search/text`, query);
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
export const classifySearchQuery = (query: string): SearchType => {
  const query_lower = query.toLowerCase();
  
  // Check for image search patterns
  if (query_lower.includes('image') || 
      query_lower.includes('picture') || 
      query_lower.includes('photo') || 
      query_lower.includes('look like')) {
    return SearchType.IMAGE;
  }
  
  // Check for customer support patterns
  if (query_lower.includes('help') || 
      query_lower.includes('support') || 
      query_lower.includes('question') || 
      query_lower.includes('problem') ||
      query_lower.includes('issue') ||
      query_lower.includes('how do i') ||
      query_lower.includes('can you help')) {
    return SearchType.CUSTOMER_SUPPORT;
  }
  
  // Check for vector search patterns (more specific queries)
  if (query_lower.includes('similar') || 
      query_lower.includes('like') || 
      query_lower.length > 15) {
    return SearchType.VECTOR;
  }
  
  // Default to BM25 for shorter, keyword-based queries
  return SearchType.BM25;
};

// Function to generate search explanation based on query type
export const generateSearchExplanation = (query: string, searchType: SearchType): string => {
  switch (searchType) {
    case SearchType.BM25:
      return `I'll search for "${query}" using keyword matching (BM25) with this Elasticsearch query:
\`\`\`json
{
  "query": {
    "bool": {
      "should": [
        { "match": { "name": { "query": "${query}", "boost": 3.0 } } },
        { "match": { "description": { "query": "${query}", "boost": 2.0 } } },
        { "match": { "subcategory": { "query": "${query}", "boost": 1.5 } } },
        { "match": { "category": { "query": "${query}", "boost": 1.0 } } }
      ]
    }
  },
  "size": 10
}
\`\`\``;
    case SearchType.VECTOR:
      return `I'll search for "${query}" using semantic understanding (vector search) with this Elasticsearch query:
\`\`\`json
{
  "query": {
    "script_score": {
      "query": { "match_all": {} },
      "script": {
        "source": "cosineSimilarity(params.query_vector, 'text_embedding') + 1.0",
        "params": { "query_vector": "[vector embedding for '${query}']" }
      }
    }
  },
  "size": 10
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
    case SearchType.IMAGE:
      return `I'll search for products that visually match "${query}" using this Elasticsearch query:
\`\`\`json
{
  "query": {
    "script_score": {
      "query": { "match_all": {} },
      "script": {
        "source": "cosineSimilarity(params.image_vector, 'image_embedding') + 1.0",
        "params": { "image_vector": "[image embedding for '${query}']" }
      }
    }
  },
  "size": 10
}
\`\`\``;
    default:
      return `I'll search for "${query}" to find relevant products using a standard query.`;
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
