import React, { useState, useRef } from 'react';
import { Box, Grid, Paper, Typography } from '@mui/material';
import ChatWindow from './components/ChatWindow';
import ProductList from './components/ProductList';
import HomePage from './components/HomePage';
import { SearchResult } from './types';

const App: React.FC = () => {
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [error, setError] = useState<string>();
  const [hasSearched, setHasSearched] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const chatWindowRef = useRef<{ handleSearch: (query: string) => Promise<void> }>(null);

  const handleSearchResults = (results: SearchResult[], error?: string) => {
    setSearchResults(results);
    setError(error);
    setHasSearched(true);
    setIsLoading(false);
  };

  const handleSearch = (query: string) => {
    // This will be called by the HomePage component
    // The actual search will be handled by the ChatWindow component
    setHasSearched(true);
    setIsLoading(true);
    // Set the input message and trigger send in ChatWindow
    chatWindowRef.current?.handleSearch(query);
  };

  const handleMessage = (message: string) => {
    // Add the message to the chat window without triggering a search
    chatWindowRef.current?.handleSearch(message);
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Paper sx={{ p: 2, bgcolor: 'primary.main', color: 'white' }}>
        <Typography variant="h5">Product Search Assistant</Typography>
      </Paper>
      
      <Grid container sx={{ flexGrow: 1, overflow: 'auto' }}>
        <Grid item xs={12} md={8} sx={{ height: '100%', overflow: 'auto' }}>
          {!hasSearched ? (
            <HomePage onSearch={handleSearch} />
          ) : (
            <ProductList products={searchResults} error={error} loading={isLoading} />
          )}
        </Grid>
        
        <Grid item xs={12} md={4} sx={{ height: '100%', overflow: 'hidden' }}>
          <ChatWindow ref={chatWindowRef} onSearchResults={handleSearchResults} />
        </Grid>
      </Grid>
    </Box>
  );
};

export default App;
