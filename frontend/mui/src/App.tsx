import { useState } from 'react';
import { Box, Container, CssBaseline, ThemeProvider, createTheme, Typography, Divider } from '@mui/material';
import ProductList from './components/ProductList';
import ChatWindow from './components/ChatWindow';
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
          {/* Left side - Products Display (70%) */}
          <Box sx={{ width: '70%', pr: 2 }}>
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
