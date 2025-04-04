import React, { useState, useEffect, useRef, forwardRef } from 'react';
import { Box, TextField, Button, Paper, Typography, Divider, CircularProgress, IconButton } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import { Message, SearchResult, SearchType } from '../types';
import { searchProducts, classifySearchQuery, generateSearchExplanation, uploadImage } from '../services/api';

interface ChatWindowProps {
  onSearchResults: (results: SearchResult[], error?: string) => void;
}

const ChatWindow = forwardRef<{ handleSearch: (query: string) => Promise<void> }, ChatWindowProps>(({ onSearchResults }, ref) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: 'Hello! I\'m your product assistant. How can I help you find products today?',
      sender: 'agent',
      timestamp: new Date(),
      type: 'general'
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const sendButtonRef = useRef<HTMLButtonElement>(null);
  
  const handleSendMessage = async (): Promise<void> => {
    if (!inputMessage.trim() || isSearching) return;
    
    const newMessage: Message = {
      id: messages.length + 1,
      text: inputMessage,
      sender: 'customer',
      timestamp: new Date(),
      type: 'general'
    };
    
    setMessages(prevMessages => [...prevMessages, newMessage]);
    setInputMessage('');
    setIsSearching(true);
    
    try {
      // Step 1: Classify the query
      const analysis = await classifySearchQuery(inputMessage);
      const searchType = analysis.type;
      
      // Add classification message with detailed analysis
      const classificationMessage: Message = {
        id: messages.length + 2,
        text: `Query Analysis:

• Type: ${searchType.toLowerCase()}
• Confidence: ${analysis.confidence || 'unknown'}
• Explanation: ${analysis.explanation || 'No explanation provided'}
• Search Strategy: ${analysis.search_strategy || 'No strategy provided'}${analysis.examples?.length > 0 ? `

• Similar queries:
  - ${analysis.examples.join('\n  - ')}` : ''}${analysis.support_answer ? `

• Support Answer:
  ${analysis.support_answer}` : ''}`,
        sender: 'agent',
        timestamp: new Date(),
        type: 'query_classification'
      };
      
      setMessages(prevMessages => [...prevMessages, classificationMessage]);
      
      // If it's a customer support query, add the support answer in a separate message
      if (searchType === SearchType.CUSTOMER_SUPPORT && analysis.support_answer) {
        // Simulate a slight delay between messages for a more natural conversation flow
        await new Promise(resolve => setTimeout(resolve, 800));
        
        const supportMessage: Message = {
          id: messages.length + 3,
          text: analysis.support_answer,
          sender: 'agent',
          timestamp: new Date(),
          type: 'support_answer'
        };
        setMessages(prevMessages => [...prevMessages, supportMessage]);
        setIsSearching(false);
        return;
      }
      
      // If it's a customer support query but no support answer, we're done
      if (searchType === SearchType.CUSTOMER_SUPPORT) {
        setIsSearching(false);
        return;
      }
      
      // Simulate a slight delay between messages for a more natural conversation flow
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Step 2: Generate search explanation
      const searchExplanationText = generateSearchExplanation(inputMessage, searchType);
      
      // Add search explanation message
      const searchQueryMessage: Message = {
        id: messages.length + 3,
        text: searchExplanationText,
        sender: 'agent',
        timestamp: new Date(),
        type: 'search_query'
      };
      
      setMessages(prevMessages => [...prevMessages, searchQueryMessage]);
      
      // Simulate a slight delay for search processing
      await new Promise(resolve => setTimeout(resolve, 1200));
      
      // Step 3: Perform the actual search
      const searchResults = await searchProducts({ query: inputMessage });
      
      // Step 4: Add results message
      const resultsMessage: Message = {
        id: messages.length + 4,
        text: searchResults.length > 0 
          ? `I found ${searchResults.length} products that match your search. Here they are!` 
          : 'I couldn\'t find any products matching your search. Could you try a different query?',
        sender: 'agent',
        timestamp: new Date(),
        type: 'search_results'
      };
      
      setMessages(prevMessages => [...prevMessages, resultsMessage]);
      
      // Update search results in parent component
      onSearchResults(searchResults);
    } catch (error) {
      console.error('Error processing message:', error);
      const errorMessage: Message = {
        id: messages.length + 2,
        text: 'Sorry, I encountered an error processing your request. Please try again.',
        sender: 'agent',
        timestamp: new Date(),
        type: 'error'
      };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
      setIsSearching(false);
    }
  };

  // Expose handleSearch method to parent component
  React.useImperativeHandle(ref, () => ({
    handleSearch: async (query: string) => {
      // Set the input message
      setInputMessage(query);
      // Add the message to the messages list
      const newMessage: Message = {
        id: messages.length + 1,
        text: query,
        sender: 'customer',
        timestamp: new Date(),
        type: 'general'
      };
      setMessages(prevMessages => [...prevMessages, newMessage]);
      // Trigger the search process
      setIsSearching(true);
      
      try {
        // Step 1: Classify the query
        const analysis = await classifySearchQuery(query);
        const searchType = analysis.type;
        
        // Add classification message with detailed analysis
        const classificationMessage: Message = {
          id: messages.length + 2,
          text: `Query Analysis:

• Type: ${searchType.toLowerCase()}
• Confidence: ${analysis.confidence || 'unknown'}
• Explanation: ${analysis.explanation || 'No explanation provided'}
• Search Strategy: ${analysis.search_strategy || 'No strategy provided'}${analysis.examples?.length > 0 ? `

• Similar queries:
  - ${analysis.examples.join('\n  - ')}` : ''}${analysis.support_answer ? `

• Support Answer:
  ${analysis.support_answer}` : ''}`,
          sender: 'agent',
          timestamp: new Date(),
          type: 'query_classification'
        };
        
        setMessages(prevMessages => [...prevMessages, classificationMessage]);
        
        // If it's a customer support query, add the support answer in a separate message
        if (searchType === SearchType.CUSTOMER_SUPPORT && analysis.support_answer) {
          // Simulate a slight delay between messages for a more natural conversation flow
          await new Promise(resolve => setTimeout(resolve, 800));
          
          const supportMessage: Message = {
            id: messages.length + 3,
            text: analysis.support_answer,
            sender: 'agent',
            timestamp: new Date(),
            type: 'support_answer'
          };
          setMessages(prevMessages => [...prevMessages, supportMessage]);
          setIsSearching(false);
          return;
        }
        
        // If it's a customer support query but no support answer, we're done
        if (searchType === SearchType.CUSTOMER_SUPPORT) {
          setIsSearching(false);
          return;
        }
        
        // Simulate a slight delay between messages for a more natural conversation flow
        await new Promise(resolve => setTimeout(resolve, 800));
        
        // Step 2: Generate search explanation
        const searchExplanationText = generateSearchExplanation(query, searchType);
        
        // Add search explanation message
        const searchQueryMessage: Message = {
          id: messages.length + 3,
          text: searchExplanationText,
          sender: 'agent',
          timestamp: new Date(),
          type: 'search_query'
        };
        
        setMessages(prevMessages => [...prevMessages, searchQueryMessage]);
        
        // Simulate a slight delay for search processing
        await new Promise(resolve => setTimeout(resolve, 1200));
        
        // Step 3: Perform the actual search
        const searchResults = await searchProducts({ query });
        
        // Step 4: Add results message
        const resultsMessage: Message = {
          id: messages.length + 4,
          text: searchResults.length > 0 
            ? `I found ${searchResults.length} products that match your search. Here they are!` 
            : 'I couldn\'t find any products matching your search. Could you try a different query?',
          sender: 'agent',
          timestamp: new Date(),
          type: 'search_results'
        };
        
        setMessages(prevMessages => [...prevMessages, resultsMessage]);
        
        // Update search results in parent component
        onSearchResults(searchResults);
      } catch (error) {
        console.error('Error processing message:', error);
        const errorMessage: Message = {
          id: messages.length + 2,
          text: 'Sorry, I encountered an error processing your request. Please try again.',
          sender: 'agent',
          timestamp: new Date(),
          type: 'error'
        };
        setMessages(prevMessages => [...prevMessages, errorMessage]);
      } finally {
        setIsSearching(false);
        setInputMessage('');
      }
    }
  }));
  
  // Handle file selection
  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      const file = event.target.files[0];
      
      // Add a message showing the selected file
      const fileMessage: Message = {
        id: messages.length + 1,
        text: `Selected file: ${file.name}`,
        sender: 'customer',
        timestamp: new Date(),
        type: 'file_upload',
        file: {
          name: file.name,
          type: file.type
        }
      };
      
      setMessages(prevMessages => [...prevMessages, fileMessage]);
      
      // Automatically upload the file after selection
      handleFileUpload(file);
    }
  };
  
  // Handle file upload
  const handleFileUpload = async (file: File) => {
    setIsSearching(true);
    
    try {
      // Add processing message
      const processingMessage: Message = {
        id: messages.length + 1,
        text: `Processing file: ${file.name}...`,
        sender: 'agent',
        timestamp: new Date(),
        type: 'general'
      };
      
      setMessages(prevMessages => [...prevMessages, processingMessage]);
      
      // Upload the file and get product recommendations
      const results = await uploadImage(file);
      
      // Find the summary result (first result with all item matches)
      const summaryResult = results.find(r => r.product_id === 'summary');
      const itemMatches = summaryResult?.alternatives || [];
      
      // Format the item list for display
      const itemList = itemMatches.map((item: { item: string; quantity?: number; attributes?: string; matched_product_name?: string; image_url?: string }) => {
        const itemName = item.item || '';
        const quantity = item.quantity ? `${item.quantity} of ` : '';
        const attributes = item.attributes ? ` (${item.attributes})` : '';
        const matchedProduct = item.matched_product_name 
          ? ` → Matched with: ${item.matched_product_name}${item.image_url ? `\n  <img src="${item.image_url}" alt="${item.matched_product_name}" style="max-width: 100px; max-height: 100px; margin-top: 8px;" />` : ''}`
          : ' → No matching product found';
        
        return `• ${quantity}${itemName}${attributes}${matchedProduct}`;
      }).join('\n');
      
      // Add results message
      const resultsMessage: Message = {
        id: messages.length + 2,
        text: results.length > 0 
          ? `I analyzed your image and found these items:\n\n${itemList}\n\nHere are the recommended products!` 
          : 'I couldn\'t identify any items in your image. Could you try a clearer image?',
        sender: 'agent',
        timestamp: new Date(),
        type: 'search_results'
      };
      
      setMessages(prevMessages => [...prevMessages, resultsMessage]);
      
      // Update search results in parent component - filter out the summary result
      const productResults = results.filter(r => r.product_id !== 'summary');
      onSearchResults(productResults);
    } catch (error) {
      console.error('Error processing file:', error);
      
      // Add error message
      const errorMessage: Message = {
        id: messages.length + 3,
        text: 'Sorry, I encountered an error while processing your file. Please try again.',
        sender: 'agent',
        timestamp: new Date(),
        type: 'error'
      };
      
      setMessages(prevMessages => [...prevMessages, errorMessage]);
      onSearchResults([], 'Sorry, I encountered an error while processing your file. Please try again.');
    } finally {
      setIsSearching(false);
    }
  };

  // Auto-scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const getMessageBackgroundColor = (message: Message) => {
    switch (message.type) {
      case 'query_classification':
        return '#E8F1FF';
      case 'search_query':
        return '#FFEBF5';
      case 'search_results':
        return '#E2F8F0';
      case 'support_answer':
        return '#E2F8F0';
      default:
        return message.sender === 'agent' ? '#F6F9FC' : '#C9F3E3';
    }
  };

  const getMessageTextColor = (message: Message) => {
    switch (message.type) {
      case 'query_classification':
      case 'search_query':
      case 'search_results':
        return '#000000';
      default:
        return message.sender === 'agent' ? '#000000' : '#000000';
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
        {messages.map((message) => (
          <Box
            key={message.id}
            sx={{
              display: 'flex',
              justifyContent: message.sender === 'customer' ? 'flex-end' : 'flex-start',
              mb: 2
            }}
          >
            <Paper
              elevation={1}
              sx={{
                p: 1.5,
                bgcolor: getMessageBackgroundColor(message),
                color: getMessageTextColor(message),
                maxWidth: '80%',
                borderRadius: '12px',
                borderTopRightRadius: message.sender === 'customer' ? '4px' : '12px',
                borderTopLeftRadius: message.sender === 'agent' ? '4px' : '12px',
              }}
            >
              {message.sender === 'agent' && (
                <Typography variant="subtitle2" fontWeight="bold" color="text.secondary">
                  {message.type === 'query_classification' || message.type === 'search_query' ? 'DEBUG' : 'Agent'}
                </Typography>
              )}
              {message.sender === 'customer' && (
                <Typography variant="subtitle2" fontWeight="bold" color="text.secondary">
                  You
                </Typography>
              )}
              {message.type === 'search_query' ? (
                <Box sx={{ whiteSpace: 'pre-wrap' }}>
                  <Typography variant="body1" dangerouslySetInnerHTML={{ __html: message.text.replace(/```json([\s\S]*?)```/g, '<pre style="background-color: #f5f5f5; padding: 8px; border-radius: 4px; overflow-x: auto;"><code>$1</code></pre>') }} />
                </Box>
              ) : message.type === 'query_classification' || message.type === 'search_results' ? (
                <Box sx={{ whiteSpace: 'pre-wrap' }}>
                  <Typography variant="body1" component="div" dangerouslySetInnerHTML={{ 
                    __html: message.text.split('\n').map((line, index) => {
                      const trimmedLine = line.trim();
                      if (trimmedLine.startsWith('•')) {
                        return `<div style="margin-bottom: 8px;">${trimmedLine}</div>`;
                      } else if (trimmedLine.startsWith('-')) {
                        return `<div style="margin-left: 16px; margin-bottom: 8px;">${trimmedLine}</div>`;
                      }
                      return `<div style="margin-bottom: 8px;">${line}</div>`;
                    }).join('')
                  }} />
                </Box>
              ) : message.type === 'support_answer' ? (
                <Box sx={{ whiteSpace: 'pre-wrap' }}>
                  <Typography variant="body1" sx={{ fontWeight: 'medium' }}>{message.text}</Typography>
                </Box>
              ) : (
                <Typography variant="body1">{message.text}</Typography>
              )}
            </Paper>
          </Box>
        ))}
        <div ref={messagesEndRef} />
      </Box>
      
      <Divider />
      
      <Box sx={{ p: 2, display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Type your message..."
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          disabled={isSearching}
        />
        <IconButton
          color="primary" 
          onClick={() => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/jpeg,image/png,image/gif,.pdf,*/*';
            input.onchange = (e) => {
              const file = (e.target as HTMLInputElement).files?.[0];
              if (file) {
                handleFileUpload(file);
              }
            };
            input.click();
          }}
          disabled={isSearching}
          sx={{ 
            bgcolor: 'background.paper',
            '&:hover': { bgcolor: 'action.hover' }
          }}
        >
          <AttachFileIcon />
        </IconButton>
        <Button
          ref={sendButtonRef}
          variant="contained"
          color="primary"
          onClick={handleSendMessage}
          disabled={!inputMessage.trim() || isSearching}
          endIcon={isSearching ? <CircularProgress size={20} /> : <SendIcon />}
        >
          Send
        </Button>
      </Box>
    </Box>
  );
});

export default ChatWindow;
