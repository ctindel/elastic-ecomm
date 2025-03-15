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
      return `I'll search for "${query}" using keyword matching to find the most relevant products.`;
    case SearchType.VECTOR:
      return `I'll search for "${query}" using semantic understanding to find products that match your description.`;
    case SearchType.CUSTOMER_SUPPORT:
      return `I'll help answer your question about "${query}" and find relevant products if needed.`;
    case SearchType.IMAGE:
      return `I'll search for products that visually match "${query}".`;
    default:
      return `I'll search for "${query}" to find relevant products.`;
  }
};
