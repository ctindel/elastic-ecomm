import React from 'react';
import { Box, Typography, CircularProgress } from '@mui/material';
import ProductCard from './ProductCard';
import { SearchResult } from '../types';

interface ProductListProps {
  products: SearchResult[];
  loading: boolean;
  error: string | null;
}

const ProductList: React.FC<ProductListProps> = ({ products, loading, error }) => {
  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  if (products.length === 0) {
    return (
      <Box sx={{ p: 3 }}>
        <Typography>No products found. Try a different search term.</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 2 }}>
      {products.map((product) => (
        <ProductCard key={product.product_id} product={product} />
      ))}
    </Box>
  );
};

export default ProductList;
