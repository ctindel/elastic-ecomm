import React, { useState, useEffect, useRef } from 'react';
import { Box, TextField, Button, Paper, Typography, Divider, CircularProgress, IconButton } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import { Message, SearchResult } from '../types';
import { searchProducts, classifySearchQuery, generateSearchExplanation, uploadImage } from '../services/api';

interface ChatWindowProps {
  onSearchResults: (results: SearchResult[]) => void;
}

const ChatWindow: React.FC<ChatWindowProps> = ({ onSearchResults }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: 'Hello! I\'m your product assistant. How can I help you find products today?',
      sender: 'agent',
      timestamp: new Date(),
      type: 'general'
    },
  ]);
  const [newMessage, setNewMessage] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Handle file selection
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setSelectedFile(event.target.files[0]);
      
      // Add a message showing the selected file
      const fileMessage: Message = {
        id: messages.length + 1,
        text: `Selected file: ${event.target.files[0].name}`,
        sender: 'customer',
        timestamp: new Date(),
        type: 'file_upload',
        file: {
          name: event.target.files[0].name,
          type: event.target.files[0].type
        }
      };
      
      setMessages(prevMessages => [...prevMessages, fileMessage]);
    }
  };
  
  // Handle file upload
  const handleFileUpload = async () => {
    if (!selectedFile) return;
    
    setIsSearching(true);
    
    try {
      // Add processing message
      const processingMessage: Message = {
        id: messages.length + 1,
        text: `Processing file: ${selectedFile.name}...`,
        sender: 'agent',
        timestamp: new Date(),
        type: 'general'
      };
      
      setMessages(prevMessages => [...prevMessages, processingMessage]);
      
      // Upload the file and get product recommendations
      const results = await uploadImage(selectedFile);
      
      // Add results message
      const resultsMessage: Message = {
        id: messages.length + 2,
        text: results.length > 0 
          ? `I found the following items in your image: ${results.map(r => r.product_name).join(', ')}. Here are some recommended products!` 
          : 'I couldn\'t identify any items in your image. Could you try a clearer image?',
        sender: 'agent',
        timestamp: new Date(),
        type: 'search_results'
      };
      
      setMessages(prevMessages => [...prevMessages, resultsMessage]);
      
      // Update search results in parent component
      onSearchResults(results);
      
      // Clear the selected file
      setSelectedFile(null);
    } catch (error) {
      console.error('Error processing file:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: messages.length + 3,
        text: 'Sorry, I encountered an error while processing your file. Please try again.',
        sender: 'agent',
        timestamp: new Date(),
        type: 'general'
      };
      
      setMessages(prevMessages => [...prevMessages, errorMessage]);
      onSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newMessage.trim()) {
      // Add customer message
      const customerMessage: Message = {
        id: messages.length + 1,
        text: newMessage,
        sender: 'customer',
        timestamp: new Date(),
        type: 'general'
      };
      
      setMessages(prevMessages => [...prevMessages, customerMessage]);
      setNewMessage('');
      setIsSearching(true);
      
      try {
        // Step 1: Classify the query
        const queryType = classifySearchQuery(newMessage);
        
        // Add classification message
        const classificationMessage: Message = {
          id: messages.length + 2,
          text: `I understand you're looking for ${queryType.toLowerCase()} information about "${newMessage}".`,
          sender: 'agent',
          timestamp: new Date(),
          type: 'query_classification'
        };
        
        setMessages(prevMessages => [...prevMessages, classificationMessage]);
        
        // Simulate a slight delay between messages for a more natural conversation flow
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // Step 2: Generate search explanation
        const searchExplanation = generateSearchExplanation(newMessage, queryType);
        
        // Add search explanation message
        const searchQueryMessage: Message = {
          id: messages.length + 3,
          text: searchExplanation,
          sender: 'agent',
          timestamp: new Date(),
          type: 'search_query'
        };
        
        setMessages(prevMessages => [...prevMessages, searchQueryMessage]);
        
        // Simulate a slight delay for search processing
        await new Promise(resolve => setTimeout(resolve, 1200));
        
        // Step 3: Perform the actual search
        const results = await searchProducts({ query: newMessage });
        
        // Step 4: Add results message
        const resultsMessage: Message = {
          id: messages.length + 4,
          text: results.length > 0 
            ? `I found ${results.length} products that match your search. Here they are!` 
            : 'I couldn\'t find any products matching your search. Could you try a different query?',
          sender: 'agent',
          timestamp: new Date(),
          type: 'search_results'
        };
        
        setMessages(prevMessages => [...prevMessages, resultsMessage]);
        
        // Update search results in parent component
        onSearchResults(results);
      } catch (error) {
        console.error('Error processing search:', error);
        
        // Add error message
        const errorMessage: Message = {
          id: messages.length + 5,
          text: 'Sorry, I encountered an error while searching. Please try again.',
          sender: 'agent',
          timestamp: new Date(),
          type: 'general'
        };
        
        setMessages(prevMessages => [...prevMessages, errorMessage]);
        onSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }
  };

  return (
    <Paper sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ p: 2, bgcolor: 'primary.main', color: 'white' }}>
        <Typography variant="h6">Product Assistant</Typography>
      </Box>
      <Divider />
      
      <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2, maxHeight: 'calc(100vh - 200px)' }}>
        {messages.map((message) => (
          <Box
            key={message.id}
            sx={{
              display: 'flex',
              justifyContent: message.sender === 'customer' ? 'flex-end' : 'flex-start',
              mb: 2,
            }}
          >
            <Paper
              variant="outlined"
              sx={{
                p: 1.5,
                bgcolor: message.sender === 'customer' ? 'primary.light' : 
                  message.type === 'query_classification' ? 'info.light' :
                  message.type === 'search_query' ? 'secondary.light' :
                  message.type === 'search_results' ? 'success.light' : 'grey.100',
                color: message.sender === 'customer' ? 'white' : 'text.primary',
                maxWidth: '80%',
                borderRadius: '12px',
                borderTopRightRadius: message.sender === 'customer' ? '4px' : '12px',
                borderTopLeftRadius: message.sender === 'agent' ? '4px' : '12px',
              }}
            >
              {message.sender === 'agent' && (
                <Typography variant="subtitle2" fontWeight="bold" color="text.secondary">
                  Agent
                </Typography>
              )}
              {message.sender === 'customer' && (
                <Typography variant="subtitle2" fontWeight="bold" color="white">
                  You
                </Typography>
              )}
              {message.type === 'search_query' ? (
                <Box sx={{ whiteSpace: 'pre-wrap' }}>
                  <Typography variant="body1" dangerouslySetInnerHTML={{ __html: message.text.replace(/```json([\s\S]*?)```/g, '<pre style="background-color: #f5f5f5; padding: 8px; border-radius: 4px; overflow-x: auto;"><code>$1</code></pre>') }} />
                </Box>
              ) : (
                <Typography variant="body1">{message.text}</Typography>
              )}
              <Typography variant="caption" color={message.sender === 'customer' ? 'white' : 'text.secondary'}>
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </Typography>
            </Paper>
          </Box>
        ))}
        {isSearching && (
          <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
            <CircularProgress size={24} />
          </Box>
        )}
        <div ref={messagesEndRef} />
      </Box>
      
      <Divider />
      <Box component="form" onSubmit={handleSendMessage} sx={{ p: 2, display: 'flex' }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Ask about products..."
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          size="small"
          sx={{ mr: 1 }}
          disabled={isSearching}
        />
        <input
          type="file"
          id="file-upload"
          style={{ display: 'none' }}
          onChange={handleFileSelect}
          accept="image/jpeg,image/png,application/pdf"
        />
        <label htmlFor="file-upload">
          <IconButton component="span" disabled={isSearching} sx={{ mr: 1 }}>
            <AttachFileIcon />
          </IconButton>
        </label>
        {selectedFile && (
          <Button
            variant="outlined"
            color="primary"
            onClick={handleFileUpload}
            disabled={isSearching}
            sx={{ mr: 1 }}
          >
            Upload
          </Button>
        )}
        <Button
          type="submit"
          variant="contained"
          color="primary"
          endIcon={<SendIcon />}
          disabled={isSearching || (!newMessage.trim() && !selectedFile)}
        >
          Send
        </Button>
      </Box>
    </Paper>
  );
};

export default ChatWindow;
