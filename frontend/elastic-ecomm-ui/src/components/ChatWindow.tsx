import React, { useState } from 'react';
import { Box, TextField, Button, Paper, Typography, Divider } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

interface Message {
  id: number;
  text: string;
  sender: 'user' | 'agent';
  timestamp: Date;
}

const ChatWindow: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 1,
      text: 'Hello! How can I help you find products today?',
      sender: 'agent',
      timestamp: new Date(),
    },
  ]);
  const [newMessage, setNewMessage] = useState('');

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (newMessage.trim()) {
      // Add user message
      const userMessage: Message = {
        id: messages.length + 1,
        text: newMessage,
        sender: 'user',
        timestamp: new Date(),
      };
      
      // Add agent response (placeholder for now)
      const agentMessage: Message = {
        id: messages.length + 2,
        text: `I'll help you find information about "${newMessage}". Please use the search bar to look for products.`,
        sender: 'agent',
        timestamp: new Date(),
      };
      
      setMessages([...messages, userMessage, agentMessage]);
      setNewMessage('');
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
              justifyContent: message.sender === 'user' ? 'flex-end' : 'flex-start',
              mb: 2,
            }}
          >
            <Paper
              variant="outlined"
              sx={{
                p: 1,
                bgcolor: message.sender === 'user' ? 'primary.light' : 'grey.100',
                color: message.sender === 'user' ? 'white' : 'text.primary',
                maxWidth: '70%',
              }}
            >
              <Typography variant="body1">{message.text}</Typography>
              <Typography variant="caption" color={message.sender === 'user' ? 'white' : 'text.secondary'}>
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </Typography>
            </Paper>
          </Box>
        ))}
      </Box>
      
      <Divider />
      <Box component="form" onSubmit={handleSendMessage} sx={{ p: 2, display: 'flex' }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Type a message..."
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          size="small"
          sx={{ mr: 1 }}
        />
        <Button
          type="submit"
          variant="contained"
          color="primary"
          endIcon={<SendIcon />}
        >
          Send
        </Button>
      </Box>
    </Paper>
  );
};

export default ChatWindow;
