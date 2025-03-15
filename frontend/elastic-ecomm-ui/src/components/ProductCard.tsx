import React from 'react';
import { Card, CardContent, CardMedia, Typography, Box } from '@mui/material';
import { SearchResult } from '../types';

interface ProductCardProps {
  product: SearchResult;
}

const ProductCard: React.FC<ProductCardProps> = ({ product }) => {
  return (
    <Card sx={{ display: 'flex', mb: 2, height: '150px' }}>
      <CardMedia
        component="img"
        sx={{ width: 150, objectFit: 'contain' }}
        image={product.image_url || '/placeholder-image.png'}
        alt={product.product_name}
      />
      <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
        <CardContent sx={{ flex: '1 0 auto' }}>
          <Typography component="div" variant="h6">
            {product.product_name}
          </Typography>
          <Typography variant="subtitle1" color="text.secondary" component="div">
            ${product.price?.toFixed(2) || 'N/A'}
          </Typography>
          <Typography variant="body2" color="text.secondary" noWrap>
            {product.product_description || 'No description available'}
          </Typography>
        </CardContent>
      </Box>
    </Card>
  );
}

export default ProductCard;
