import React from 'react';
import { Box, Typography, Grid, Card, CardContent, CardMedia, Button, Chip } from '@mui/material';
import { SearchResult } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface HomePageProps {
  onSearch: (query: string) => void;
  onMessage?: (message: string) => void;
}

const HomePage: React.FC<HomePageProps> = ({ onSearch, onMessage }) => {
  const handleSearch = (query: string) => {
    // Trigger the search
    onSearch(query);
  };

  const featuredCategories = [
    { name: 'Office Supplies', query: 'office supplies' },
    { name: 'Electronics', query: 'electronics' },
    { name: 'Furniture', query: 'office furniture' },
    { name: 'Paper Products', query: 'paper products' }
  ];

  const featuredProducts: SearchResult[] = [
    {
      product_id: "ea029887-0274-4929-a284-2fb14085d366",
      name: "Pyrex Essential Decor",
      description: "Essential kitchen decor from Pyrex",
      category: "Home & Kitchen",
      price: 132.13,
      brand: "Pyrex",
      image_url: `${API_URL}/static/images/product_ea029887-0274-4929-a284-2fb14085d366.png`
    },
    {
      product_id: "d23b818c-bbe3-48cd-860c-b0eec1eca587",
      name: "HP Modern Headphones",
      description: "Modern wireless headphones from HP",
      category: "Electronics",
      price: 200.82,
      brand: "HP",
      image_url: `${API_URL}/static/images/product_d23b818c-bbe3-48cd-860c-b0eec1eca587.png`
    },
    {
      product_id: "50211a61-d8c3-4892-a7be-d20109146070",
      name: "Papermate Professional Calendars",
      description: "Professional calendar set from Papermate",
      category: "Office Supplies",
      price: 21.48,
      brand: "Papermate",
      image_url: `${API_URL}/static/images/product_50211a61-d8c3-4892-a7be-d20109146070.png`
    },
    {
      product_id: "a8fd64c4-5793-494f-a21a-c0d8e411727a",
      name: "Avery Luxury Pens & Pencils",
      description: "Luxury writing instruments from Avery",
      category: "Office Supplies",
      price: 19.36,
      brand: "Avery",
      image_url: `${API_URL}/static/images/product_a8fd64c4-5793-494f-a21a-c0d8e411727a.png`
    }
  ];

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Welcome to Our Store
      </Typography>
      
      {/* Featured Categories */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Shop by Category
        </Typography>
        <Grid container spacing={2}>
          {featuredCategories.map((category) => (
            <Grid item xs={6} sm={3} key={category.name}>
              <Card 
                sx={{ 
                  height: '100%',
                  cursor: 'pointer',
                  '&:hover': { boxShadow: 6 }
                }}
                onClick={() => handleSearch(category.query)}
              >
                <CardContent>
                  <Typography variant="h6" align="center">
                    {category.name}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Popular Searches */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Popular Searches
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
          {['stapler', 'desk chair', 'printer', 'paper', 'laptop', 'monitor'].map((term) => (
            <Chip
              key={term}
              label={term}
              onClick={() => handleSearch(term)}
              sx={{ textTransform: 'capitalize' }}
            />
          ))}
        </Box>
      </Box>

      {/* Featured Products */}
      <Box>
        <Typography variant="h6" gutterBottom>
          Featured Products
        </Typography>
        <Grid container spacing={3}>
          {featuredProducts.map((product) => (
            <Grid item xs={12} sm={6} md={3} key={product.product_id}>
              <Card 
                sx={{ 
                  height: '100%',
                  cursor: 'pointer',
                  '&:hover': { boxShadow: 6 }
                }}
                onClick={() => handleSearch(product.name)}
              >
                <CardMedia
                  component="img"
                  height="140"
                  image={product.image_url}
                  alt={product.name}
                  sx={{ objectFit: 'contain', bgcolor: 'grey.100' }}
                />
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom noWrap>
                    {product.name}
                  </Typography>
                  <Typography variant="h6" color="primary">
                    ${product.price.toFixed(2)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>
    </Box>
  );
};

export default HomePage; 