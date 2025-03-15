import { useState } from 'react';
import { Box, Container, CssBaseline, ThemeProvider, createTheme, Typography, Divider } from '@mui/material';
import SearchBar from './components/SearchBar';
import ProductList from './components/ProductList';
import ChatWindow from './components/ChatWindow';
import { searchProducts } from './services/api';
import { SearchResult } from './types';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    info: {
      main: '#0288d1',
      light: '#e3f2fd',
    },
    success: {
      main: '#2e7d32',
      light: '#e8f5e9',
    },
  },
});

function App() {
  const [products, setProducts] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // This function is now only used by the SearchBar component
  // The actual search is handled by the ChatWindow component
  const handleSearch = async (query: string) => {
    // When search is triggered from the search bar, we need to pass it to the chat window
    // This would require a ref to the chat window component, which is beyond the scope
    // of this implementation. For now, we'll just perform the search directly
    setLoading(true);
    setError(null);
    
    try {
      const results = await searchProducts({ query });
      setProducts(results);
    } catch (err) {
      setError('Failed to fetch products. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };
  
  const handleSearchResults = (results: SearchResult[]) => {
    setProducts(results);
    setLoading(false);
    setError(null);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Elastic E-Commerce Search
        </Typography>
        <Divider sx={{ mb: 3 }} />
        
        <Box sx={{ display: 'flex', height: 'calc(100vh - 150px)' }}>
          {/* Left side - Search and Products (70%) */}
          <Box sx={{ width: '70%', pr: 2 }}>
            <SearchBar onSearch={handleSearch} />
            <ProductList products={products} loading={loading} error={error} />
          </Box>
          
          {/* Right side - Chat Window (30%) */}
          <Box sx={{ width: '30%', pl: 2 }}>
            <ChatWindow onSearchResults={handleSearchResults} />
          </Box>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
