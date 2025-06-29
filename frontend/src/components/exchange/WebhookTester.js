import React, { useState } from 'react';
import {
  Box, Typography, Card, CardContent, TextField, Button, MenuItem,
  Grid, Paper, CircularProgress, Divider, Select, FormControl, InputLabel,
  IconButton, Tooltip, Collapse, Alert, FormControlLabel, Checkbox
} from '@mui/material';
import { useSnackbar } from 'notistack';
import SendIcon from '@mui/icons-material/Send';
import RefreshIcon from '@mui/icons-material/Refresh';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import CodeIcon from '@mui/icons-material/Code';
import { format } from 'date-fns';

// Sample webhook templates for different exchanges
const webhookTemplates = {
  Binance: {
    trade: {
      eventType: "trade",
      eventTime: Date.now(),
      symbol: "BTCUSDT",
      price: "29451.23",
      quantity: "0.0345",
      tradeId: 12345678,
      buyerOrderId: 87654321,
      sellerOrderId: 98765432,
      isBuyerMaker: false
    },
    orderUpdate: {
      eventType: "executionReport",
      eventTime: Date.now(),
      symbol: "BTCUSDT",
      clientOrderId: "xrp123456",
      side: "BUY",
      orderType: "LIMIT",
      timeInForce: "GTC",
      quantity: "0.5",
      price: "29500.00",
      status: "NEW",
      orderTime: Date.now() - 1000,
      executedQty: "0.0"
    }
  },
  OKX: {
    trade: {
      op: "order",
      data: [{
        instType: "SPOT",
        instId: "BTC-USDT",
        ordId: "312269865356374016",
        clOrdId: "b1",
        tag: "",
        px: "29450.2",
        sz: "0.1",
        pnl: "0",
        ordType: "limit",
        side: "buy",
        posSide: "net",
        tdMode: "cash",
        accFillSz: "0",
        fillPx: "0",
        tradeId: "0",
        fillSz: "0",
        fillTime: "0",
        state: "live",
        avgPx: "0",
        lever: "0",
        tpTriggerPx: "",
        tpOrdPx: "",
        slTriggerPx: "",
        slOrdPx: "",
        feeCcy: "",
        fee: "",
        rebateCcy: "",
        rebate: "",
        category: "",
        uTime: Date.now().toString(),
        cTime: (Date.now() - 1000).toString()
      }]
    }
  },
  BitGet: {
    orderUpdate: {
      symbol: "BTCUSDT_SPBL",
      clientOrderId: "16559961137261",
      side: "BUY",
      orderType: "LIMIT",
      quoteSize: "3.0",
      baseSize: "0.0001",
      orderStatus: "NEW",
      executedQty: "0",
      quoteQty: "0",
      price: "29450",
      avgPrice: "0",
      fee: "0",
      feeCoin: "BTC",
      cTime: Date.now()
    }
  },
  ByBit: {
    trade: {
      topic: "execution",
      data: [{
        symbol: "BTCUSDT",
        orderId: "1362801-1562-3232-1561-1",
        orderLinkId: "test-001",
        side: "Buy",
        orderPrice: "29451.50",
        orderQty: "0.05",
        execFee: "0.00000171",
        feeRate: "0.000030",
        execId: "I-UID-001",
        tradeTime: format(new Date(), "yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"),
        lastLiquidityInd: "RemovedLiquidity",
        execPrice: "29451.50",
        execQty: "0.05",
        leavesQty: "0",
        execValue: "147.2575",
        execType: "Trade",
        execStatus: "COMPLETE"
      }]
    }
  },
  Indodax: {
    trade: {
      trading_pair: "btcidr",
      transaction_type: "buy",
      order_id: 12345,
      amount: "0.001",
      price: "435000000",
      fee: "0.000002",
      fee_currency: "btc",
      transaction_time: Math.floor(Date.now() / 1000)
    }
  },
  Tokocrypto: {
    executionReport: {
      e: "executionReport",
      E: Date.now(),
      s: "BTCUSDT",
      c: "TCO123456",
      S: "BUY",
      o: "LIMIT",
      f: "GTC",
      q: "0.01",
      p: "29450.5",
      X: "NEW",
      i: 123456789,
      l: "0",
      z: "0",
      L: "0",
      n: "0",
      N: "USDT",
      T: Date.now(),
      t: -1,
      O: Date.now() - 1000
    }
  }
};

const WebhookTester = ({ exchange }) => {
  const [webhookType, setWebhookType] = useState('trade');
  const [webhookUrl, setWebhookUrl] = useState('');
  const [payload, setPayload] = useState(JSON.stringify(webhookTemplates[exchange]?.trade || {}, null, 2));
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showResponse, setShowResponse] = useState(false);
  const [useMock, setUseMock] = useState(true);
  
  const { enqueueSnackbar } = useSnackbar();
  
  // Get available webhook types for the selected exchange
  const getAvailableWebhookTypes = () => {
    if (!webhookTemplates[exchange]) return [];
    return Object.keys(webhookTemplates[exchange]);
  };
  
  // Update payload when exchange or webhook type changes
  const handleWebhookTypeChange = (event) => {
    const newType = event.target.value;
    setWebhookType(newType);
    
    if (webhookTemplates[exchange]?.[newType]) {
      setPayload(JSON.stringify(webhookTemplates[exchange][newType], null, 2));
    }
  };
  
  // Handle payload editor changes
  const handlePayloadChange = (event) => {
    setPayload(event.target.value);
  };
  
  // Send webhook test
  const handleSendWebhook = async () => {
    if (!webhookUrl && !useMock) {
      enqueueSnackbar('Please enter a webhook URL', { variant: 'error' });
      return;
    }
    
    setLoading(true);
    setResponse(null);
    
    try {
      // Validate JSON
      const payloadObj = JSON.parse(payload);
      
      // Simulate sending webhook
      setTimeout(() => {
        const mockResponse = {
          success: true,
          timestamp: new Date().toISOString(),
          statusCode: 200,
          message: 'Webhook received successfully',
          processingTime: Math.floor(Math.random() * 200) + 50 + 'ms',
          details: useMock ? 
            'Mock response - no actual request was made' : 
            `Webhook sent to ${webhookUrl}`
        };
        
        setResponse(mockResponse);
        setShowResponse(true);
        setLoading(false);
        
        enqueueSnackbar(`Webhook test for ${exchange} ${webhookType} completed`, { 
          variant: 'success' 
        });
      }, 1500);
      
    } catch (error) {
      setLoading(false);
      enqueueSnackbar('Invalid JSON payload: ' + error.message, { variant: 'error' });
    }
  };
  
  // Copy webhook URL to clipboard
  const handleCopyUrl = () => {
    navigator.clipboard.writeText(webhookUrl);
    enqueueSnackbar('Webhook URL copied to clipboard', { variant: 'success' });
  };
  
  // Copy payload to clipboard
  const handleCopyPayload = () => {
    navigator.clipboard.writeText(payload);
    enqueueSnackbar('Payload copied to clipboard', { variant: 'success' });
  };
  
  // Generate new random webhook URL
  const generateWebhookUrl = () => {
    const randomId = Math.random().toString(36).substring(2, 15);
    setWebhookUrl(`https://api.xenorize.com/webhook/${exchange.toLowerCase()}/${webhookType}/${randomId}`);
  };
  
  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {exchange} Webhook Tester
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12} sm={6}>
            <FormControl fullWidth margin="normal">
              <InputLabel>Webhook Type</InputLabel>
              <Select
                value={webhookType}
                onChange={handleWebhookTypeChange}
                label="Webhook Type"
              >
                {getAvailableWebhookTypes().map((type) => (
                  <MenuItem key={type} value={type}>
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={useMock}
                  onChange={(e) => setUseMock(e.target.checked)}
                />
              }
              label="Use mock response (don't actually send the webhook)"
            />
          </Grid>
          
          <Grid item xs={12}>
            <TextField
              fullWidth
              label="Webhook URL"
              variant="outlined"
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              disabled={useMock}
              InputProps={{
                endAdornment: (
                  <Box>
                    <Tooltip title="Generate URL">
                      <IconButton onClick={generateWebhookUrl} size="small">
                        <RefreshIcon />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Copy URL">
                      <IconButton onClick={handleCopyUrl} size="small">
                        <ContentCopyIcon />
                      </IconButton>
                    </Tooltip>
                  </Box>
                ),
              }}
            />
          </Grid>
          
          <Grid item xs={12}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
              <Typography variant="subtitle1" sx={{ mr: 1 }}>
                <CodeIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                Payload
              </Typography>
              <Tooltip title="Copy Payload">
                <IconButton onClick={handleCopyPayload} size="small">
                  <ContentCopyIcon fontSize="small" />
                </IconButton>
              </Tooltip>
            </Box>
            <TextField
              fullWidth
              multiline
              rows={10}
              variant="outlined"
              value={payload}
              onChange={handlePayloadChange}
              InputProps={{
                sx: { fontFamily: 'monospace' }
              }}
            />
          </Grid>
          
          <Grid item xs={12} sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
            <Button 
              variant="contained" 
              color="primary"
              startIcon={loading ? <CircularProgress size={20} /> : <SendIcon />}
              onClick={handleSendWebhook}
              disabled={loading}
              sx={{ px: 4 }}
            >
              {loading ? 'Sending...' : 'Send Test Webhook'}
            </Button>
          </Grid>
          
          <Grid item xs={12}>
            <Collapse in={showResponse}>
              {response && (
                <Paper sx={{ p: 2, mt: 2, backgroundColor: response.success ? '#f0f7f0' : '#fff0f0' }}>
                  <Typography variant="h6" gutterBottom>
                    Response
                    {response.success ? 
                      <Alert severity="success" sx={{ mt: 1 }}>Success: {response.statusCode}</Alert> : 
                      <Alert severity="error" sx={{ mt: 1 }}>Error: {response.statusCode}</Alert>
                    }
                  </Typography>
                  
                  <Divider sx={{ my: 2 }} />
                  
                  <Box sx={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>
                    <Typography variant="body2">Timestamp: {response.timestamp}</Typography>
                    <Typography variant="body2">Processing Time: {response.processingTime}</Typography>
                    <Typography variant="body2">Message: {response.message}</Typography>
                    <Typography variant="body2">Details: {response.details}</Typography>
                  </Box>
                </Paper>
              )}
            </Collapse>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default WebhookTester;
