import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, TextField, Button, MenuItem,
  Grid, Paper, CircularProgress, Divider, Select, FormControl, InputLabel,
  IconButton, Tooltip, Collapse, Alert, Tabs, Tab, FormControlLabel, Checkbox,
  Table, TableHead, TableBody, TableRow, TableCell, TableContainer, Chip
} from '@mui/material';
import { useSnackbar } from 'notistack';
import SendIcon from '@mui/icons-material/Send';
import RefreshIcon from '@mui/icons-material/Refresh';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import DeleteIcon from '@mui/icons-material/Delete';
import SaveIcon from '@mui/icons-material/Save';

// Sample API endpoints for exchanges
const apiEndpoints = {
  Binance: [
    { name: 'Server Time', method: 'GET', url: 'https://api.binance.com/api/v3/time', params: {} },
    { name: 'Exchange Info', method: 'GET', url: 'https://api.binance.com/api/v3/exchangeInfo', params: {} },
    { name: 'Ticker Price', method: 'GET', url: 'https://api.binance.com/api/v3/ticker/price', params: { symbol: 'BTCUSDT' } },
    { name: 'Recent Trades', method: 'GET', url: 'https://api.binance.com/api/v3/trades', params: { symbol: 'BTCUSDT', limit: 5 } }
  ],
  OKX: [
    { name: 'Server Time', method: 'GET', url: 'https://www.okx.com/api/v5/public/time', params: {} },
    { name: 'Instruments', method: 'GET', url: 'https://www.okx.com/api/v5/public/instruments', params: { instType: 'SPOT' } },
    { name: 'Ticker', method: 'GET', url: 'https://www.okx.com/api/v5/market/ticker', params: { instId: 'BTC-USDT' } }
  ],
  BitGet: [
    { name: 'Server Time', method: 'GET', url: 'https://api.bitget.com/api/spot/v1/public/time', params: {} },
    { name: 'Ticker', method: 'GET', url: 'https://api.bitget.com/api/spot/v1/market/ticker', params: { symbol: 'BTCUSDT' } }
  ],
  ByBit: [
    { name: 'Server Time', method: 'GET', url: 'https://api.bybit.com/v2/public/time', params: {} },
    { name: 'Ticker', method: 'GET', url: 'https://api.bybit.com/v2/public/tickers', params: { symbol: 'BTCUSDT' } }
  ],
  Indodax: [
    { name: 'Server Info', method: 'GET', url: 'https://indodax.com/api/server_time', params: {} },
    { name: 'Ticker', method: 'GET', url: 'https://indodax.com/api/ticker/btcidr', params: {} }
  ],
  Tokocrypto: [
    { name: 'Ticker', method: 'GET', url: 'https://www.tokocrypto.com/open/v1/market/ticker', params: { symbol: 'BTC_USDT' } },
    { name: 'Recent Trades', method: 'GET', url: 'https://www.tokocrypto.com/open/v1/market/trades', params: { symbol: 'BTC_USDT', limit: 5 } }
  ]
};

const ApiTester = ({ exchange }) => {
  const [selectedEndpoint, setSelectedEndpoint] = useState(0);
  const [customEndpoint, setCustomEndpoint] = useState('');
  const [method, setMethod] = useState('GET');
  const [url, setUrl] = useState('');
  const [params, setParams] = useState('{}');
  const [headers, setHeaders] = useState('{}');
  const [useAuth, setUseAuth] = useState(false);
  const [testMode, setTestMode] = useState('preset'); // 'preset' or 'custom'
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showResponse, setShowResponse] = useState(false);
  const [history, setHistory] = useState([]);
  
  const { enqueueSnackbar } = useSnackbar();
  
  // Initialize with selected exchange's first endpoint
  useEffect(() => {
    if (apiEndpoints[exchange]?.length > 0) {
      handlePresetSelect(0);
    }
  }, [exchange]);
  
  const handlePresetSelect = (index) => {
    setSelectedEndpoint(index);
    const endpoint = apiEndpoints[exchange][index];
    setUrl(endpoint.url);
    setMethod(endpoint.method);
    setParams(JSON.stringify(endpoint.params, null, 2));
    setHeaders('{}');
  };
  
  const handleTestModeChange = (event, newValue) => {
    setTestMode(newValue);
  };
  
  const handleMethodChange = (event) => {
    setMethod(event.target.value);
  };
  
  const handleUrlChange = (event) => {
    setUrl(event.target.value);
  };
  
  const handleParamsChange = (event) => {
    setParams(event.target.value);
  };
  
  const handleHeadersChange = (event) => {
    setHeaders(event.target.value);
  };
  
  const handleUseAuthChange = (event) => {
    setUseAuth(event.target.checked);
  };
  
  // Parse JSON safely
  const safeParseJSON = (text) => {
    try {
      return JSON.parse(text);
    } catch (error) {
      enqueueSnackbar(`Invalid JSON: ${error.message}`, { variant: 'error' });
      return null;
    }
  };
  
  const handleSendRequest = async () => {
    setLoading(true);
    setResponse(null);
    
    try {
      // Parse parameters and headers
      const parsedParams = safeParseJSON(params);
      const parsedHeaders = safeParseJSON(headers);
      
      if (parsedParams === null || parsedHeaders === null) {
        setLoading(false);
        return;
      }
      
      // In a real implementation, this would make an actual API request
      // Here we simulate a request with random response time and data
      const simulateApiRequest = () => {
        return new Promise((resolve) => {
          setTimeout(() => {
            // Generate a mock response
            if (Math.random() > 0.1) { // 90% success rate
              const mockData = {
                success: true,
                timestamp: new Date().toISOString(),
                data: url.includes('ticker') ? 
                  { symbol: 'BTCUSDT', price: (Math.random() * 2000 + 29000).toFixed(2) } : 
                  { serverTime: Date.now() },
                requestParams: parsedParams,
                requestHeaders: parsedHeaders
              };
              resolve({
                ok: true,
                status: 200,
                statusText: 'OK',
                data: mockData,
                headers: {
                  'content-type': 'application/json',
                  'x-response-time': `${Math.floor(Math.random() * 200) + 50}ms`
                }
              });
            } else {
              // Simulate error
              resolve({
                ok: false,
                status: 429,
                statusText: 'Too Many Requests',
                data: { code: -1003, msg: "Too many requests; current limit is 1200 request weight per minute" },
                headers: {
                  'content-type': 'application/json',
                  'retry-after': '30'
                }
              });
            }
          }, Math.random() * 1000 + 500); // Random response time between 500-1500ms
        });
      };
      
      const response = await simulateApiRequest();
      
      setResponse({
        status: response.status,
        statusText: response.statusText,
        headers: response.headers,
        data: response.data,
        timing: response.headers['x-response-time'],
        ok: response.ok
      });
      
      setShowResponse(true);
      
      // Add to history
      const historyItem = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        exchange,
        method,
        url,
        status: response.status,
        success: response.ok
      };
      setHistory(prev => [historyItem, ...prev].slice(0, 10)); // Keep only last 10 items
      
    } catch (error) {
      setResponse({
        error: true,
        message: error.message,
        stack: error.stack
      });
      setShowResponse(true);
      enqueueSnackbar(`Error: ${error.message}`, { variant: 'error' });
    } finally {
      setLoading(false);
    }
  };
  
  const handleClearResponse = () => {
    setShowResponse(false);
    setResponse(null);
  };
  
  const handleCopyResponse = () => {
    if (response) {
      navigator.clipboard.writeText(JSON.stringify(response, null, 2));
      enqueueSnackbar('Response copied to clipboard', { variant: 'success' });
    }
  };
  
  const handleSaveCustom = () => {
    setCustomEndpoint(url);
    enqueueSnackbar('Custom endpoint saved', { variant: 'success' });
  };
  
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {exchange} API Tester
        </Typography>
        
        <Tabs value={testMode} onChange={handleTestModeChange} sx={{ mb: 2 }}>
          <Tab label="Preset Endpoints" value="preset" />
          <Tab label="Custom Request" value="custom" />
        </Tabs>
        
        {testMode === 'preset' && (
          <FormControl fullWidth margin="normal">
            <InputLabel>Select Endpoint</InputLabel>
            <Select
              value={selectedEndpoint}
              onChange={(e) => handlePresetSelect(e.target.value)}
              label="Select Endpoint"
            >
              {apiEndpoints[exchange]?.map((endpoint, index) => (
                <MenuItem key={index} value={index}>
                  {endpoint.name} - {endpoint.method} {endpoint.url.split('://')[1].split('/')[0]}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        )}
        
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} sm={2}>
            <FormControl fullWidth>
              <InputLabel>Method</InputLabel>
              <Select
                value={method}
                onChange={handleMethodChange}
                label="Method"
                disabled={testMode === 'preset'}
              >
                <MenuItem value="GET">GET</MenuItem>
                <MenuItem value="POST">POST</MenuItem>
                <MenuItem value="PUT">PUT</MenuItem>
                <MenuItem value="DELETE">DELETE</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sm={10}>
            <TextField
              fullWidth
              label="URL"
              variant="outlined"
              value={url}
              onChange={handleUrlChange}
              disabled={testMode === 'preset'}
              InputProps={{
                endAdornment: testMode === 'custom' && (
                  <Tooltip title="Save Custom Endpoint">
                    <IconButton onClick={handleSaveCustom} size="small">
                      <SaveIcon />
                    </IconButton>
                  </Tooltip>
                ),
              }}
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2" gutterBottom>Parameters (JSON)</Typography>
            <TextField
              fullWidth
              multiline
              rows={5}
              variant="outlined"
              value={params}
              onChange={handleParamsChange}
              InputProps={{
                sx: { fontFamily: 'monospace' }
              }}
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Typography variant="subtitle2" gutterBottom>Headers (JSON)</Typography>
            <TextField
              fullWidth
              multiline
              rows={5}
              variant="outlined"
              value={headers}
              onChange={handleHeadersChange}
              InputProps={{
                sx: { fontFamily: 'monospace' }
              }}
            />
            
            <FormControlLabel
              control={
                <Checkbox
                  checked={useAuth}
                  onChange={handleUseAuthChange}
                />
              }
              label="Use Authentication"
              sx={{ mt: 1 }}
            />
            {useAuth && (
              <Alert severity="info" sx={{ mt: 1 }}>
                API key and secret from your account settings will be used
              </Alert>
            )}
          </Grid>
          
          <Grid item xs={12} sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
            <Button 
              variant="contained" 
              color="primary"
              startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
              onClick={handleSendRequest}
              disabled={loading}
              sx={{ px: 4 }}
            >
              {loading ? 'Sending...' : 'Send Request'}
            </Button>
          </Grid>
          
          <Grid item xs={12}>
            <Collapse in={showResponse}>
              {response && (
                <Paper sx={{ 
                  p: 2, 
                  mt: 2, 
                  backgroundColor: response.ok === false ? '#fff0f0' : 
                                 response.error ? '#fff0f0' : '#f0f7f0'
                }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Typography variant="h6" gutterBottom>
                      Response
                    </Typography>
                    <Box>
                      <Tooltip title="Copy Response">
                        <IconButton onClick={handleCopyResponse} size="small">
                          <ContentCopyIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Clear Response">
                        <IconButton onClick={handleClearResponse} size="small">
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>
                  
                  {response.error ? (
                    <Alert severity="error" sx={{ mb: 2 }}>
                      Error: {response.message}
                    </Alert>
                  ) : (
                    <Alert severity={response.ok ? "success" : "error"} sx={{ mb: 2 }}>
                      Status: {response.status} {response.statusText}
                    </Alert>
                  )}
                  
                  <Divider sx={{ my: 2 }} />
                  
                  {!response.error && (
                    <>
                      <Typography variant="subtitle2" gutterBottom>Headers:</Typography>
                      <Box sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap', mb: 2, fontSize: '0.875rem' }}>
                        {Object.entries(response.headers).map(([key, value]) => (
                          <Typography key={key} variant="body2">{key}: {value}</Typography>
                        ))}
                      </Box>
                      
                      <Typography variant="subtitle2" gutterBottom>Response Time: {response.timing}</Typography>
                      
                      <Divider sx={{ my: 2 }} />
                      
                      <Typography variant="subtitle2" gutterBottom>Data:</Typography>
                      <Box 
                        sx={{ 
                          fontFamily: 'monospace', 
                          whiteSpace: 'pre-wrap', 
                          overflowX: 'auto',
                          p: 1,
                          borderRadius: 1,
                          bgcolor: 'rgba(0,0,0,0.04)',
                          fontSize: '0.875rem'
                        }}
                      >
                        {JSON.stringify(response.data, null, 2)}
                      </Box>
                    </>
                  )}
                </Paper>
              )}
            </Collapse>
          </Grid>
          
          {history.length > 0 && (
            <Grid item xs={12} sx={{ mt: 3 }}>
              <Typography variant="h6" gutterBottom>Request History</Typography>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Time</TableCell>
                      <TableCell>Exchange</TableCell>
                      <TableCell>Method</TableCell>
                      <TableCell>URL</TableCell>
                      <TableCell>Status</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {history.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell>{new Date(item.timestamp).toLocaleTimeString()}</TableCell>
                        <TableCell>{item.exchange}</TableCell>
                        <TableCell>{item.method}</TableCell>
                        <TableCell sx={{ maxWidth: 250, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {item.url}
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={item.status}
                            color={item.success ? 'success' : 'error'}
                            size="small"
                          />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>
          )}
        </Grid>
      </CardContent>
    </Card>
  );
};

// Table components are now imported at the top of the file

export default ApiTester;
