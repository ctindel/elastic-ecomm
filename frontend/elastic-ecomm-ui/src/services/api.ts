import axios from 'axios';
import { SearchQuery, SearchResult } from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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
