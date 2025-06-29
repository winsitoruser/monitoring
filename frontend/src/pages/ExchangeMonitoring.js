import React, { useState, useEffect } from 'react';
import { useRecoilValue } from 'recoil';
import {
  Box, Typography, Paper, Grid, Tabs, Tab, Alert, CircularProgress,
  Table, TableBody, TableCell, TableContainer, TableHead, TableRow,
  Chip, MenuItem, FormControl, InputLabel, Select, Card, CardContent,
  Accordion, AccordionSummary, AccordionDetails
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import { Line } from 'react-chartjs-2';
import { userState } from '../utils/authAtoms';
import { format, parseISO } from 'date-fns';
import integrationService from '../services/integrationService';
import ExchangeAlertSettings from '../components/exchange/ExchangeAlertSettings';
import WebhookTester from '../components/exchange/WebhookTester';
import ApiTester from '../components/exchange/ApiTester';

// Panel for a single exchange tab
const ExchangePanel = ({ exchange }) => {
  const [apiEndpoints, setApiEndpoints] = useState([]);
  const [webhooks, setWebhooks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [historyData, setHistoryData] = useState(null);

  useEffect(() => {
    const fetchExchangeData = async () => {
      setIsLoading(true);
      try {
        const apiData = await integrationService.getExchangeApiEndpoints(exchange);
        const webhookData = await integrationService.getExchangeWebhooks(exchange);
        const historyData = await integrationService.getExchangeHistoricalData(exchange);
        
        setApiEndpoints(apiData);
        setWebhooks(webhookData);
        setHistoryData(historyData);
      } catch (error) {
        console.error(`Error fetching ${exchange} data:`, error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchExchangeData();
  }, [exchange]);

  // Prepare chart data
  const chartData = historyData ? {
    labels: historyData.map(item => item.date),
    datasets: [
      {
        label: 'API Uptime %',
        data: historyData.map(item => item.apiUptime),
        fill: false,
        backgroundColor: 'rgba(75,192,192,0.4)',
        borderColor: 'rgba(75,192,192,1)',
        tension: 0.1
      },
      {
        label: 'Webhook Uptime %',
        data: historyData.map(item => item.webhookUptime),
        fill: false,
        backgroundColor: 'rgba(255,99,132,0.4)',
        borderColor: 'rgba(255,99,132,1)',
        tension: 0.1
      },
      {
        label: 'Avg Response Time (ms)',
        data: historyData.map(item => item.responseTime),
        fill: false,
        backgroundColor: 'rgba(54,162,235,0.4)',
        borderColor: 'rgba(54,162,235,1)',
        tension: 0.1,
        yAxisID: 'responseTime'
      }
    ]
  } : null;

  const chartOptions = {
    scales: {
      y: {
        min: 90,
        max: 100,
        title: {
          display: true,
          text: 'Uptime %'
        }
      },
      responseTime: {
        position: 'right',
        min: 0,
        title: {
          display: true,
          text: 'Response Time (ms)'
        }
      }
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'down':
        return 'error';
      default:
        return 'default';
    }
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'N/A';
    try {
      return format(parseISO(timestamp), 'MMM d, yyyy HH:mm:ss');
    } catch (e) {
      return timestamp;
    }
  };

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ mt: 2 }}>
      {/* Historical Data Chart */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>Historical Performance ({exchange})</Typography>
          {historyData ? (
            <Box sx={{ height: 300 }}>
              <Line data={chartData} options={chartOptions} />
            </Box>
          ) : (
            <Alert severity="info">No historical data available</Alert>
          )}
        </CardContent>
      </Card>

      {/* API Endpoints Section */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">API Endpoints ({apiEndpoints.length})</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Endpoint</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Response Time</TableCell>
                  <TableCell>Success Rate</TableCell>
                  <TableCell>Last Checked</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {apiEndpoints.length > 0 ? (
                  apiEndpoints.map((endpoint) => (
                    <TableRow key={endpoint.id}>
                      <TableCell>{endpoint.name}</TableCell>
                      <TableCell><code>{endpoint.endpoint}</code></TableCell>
                      <TableCell>
                        <Chip 
                          label={endpoint.status} 
                          color={getStatusColor(endpoint.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{endpoint.responseTime}ms</TableCell>
                      <TableCell>{endpoint.successRate}%</TableCell>
                      <TableCell>{formatTimestamp(endpoint.lastChecked)}</TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      No API endpoints data available
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </AccordionDetails>
      </Accordion>

      {/* Webhooks Section */}
      <Accordion defaultExpanded sx={{ mt: 2 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">Webhooks ({webhooks.length})</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Endpoint</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Events Received</TableCell>
                  <TableCell>Success Rate</TableCell>
                  <TableCell>Last Event</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {webhooks.length > 0 ? (
                  webhooks.map((webhook) => (
                    <TableRow key={webhook.id}>
                      <TableCell>{webhook.name}</TableCell>
                      <TableCell><code>{webhook.endpoint}</code></TableCell>
                      <TableCell>
                        <Chip 
                          label={webhook.status} 
                          color={getStatusColor(webhook.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>{webhook.receivedEvents.toLocaleString()}</TableCell>
                      <TableCell>{webhook.successRate}%</TableCell>
                      <TableCell>{formatTimestamp(webhook.lastEvent)}</TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} align="center">
                      No webhook data available
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

// Main Exchange Monitoring Component
const ExchangeMonitoring = () => {
  const user = useRecoilValue(userState);
  const [currentExchange, setCurrentExchange] = useState('Binance');
  const [exchangeSummary, setExchangeSummary] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentTab, setCurrentTab] = useState(0);

  const exchanges = ['Binance', 'OKX', 'BitGet', 'ByBit', 'Indodax', 'Tokocrypto'];

  useEffect(() => {
    const fetchSummaryData = async () => {
      setIsLoading(true);
      try {
        const summaryData = await integrationService.getExchangeHealthSummary();
        setExchangeSummary(summaryData);
      } catch (error) {
        console.error('Error fetching exchange summary data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSummaryData();
  }, []);

  const handleExchangeChange = (event) => {
    setCurrentExchange(event.target.value);
  };

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };

  // Get summary for current exchange
  const currentSummary = exchangeSummary.find(summary => summary.exchange === currentExchange);

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'degraded':
        return 'warning';
      case 'down':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Xenorize Exchange Monitoring
      </Typography>

      {/* Status Overview Cards */}
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {isLoading ? (
          <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'center' }}>
            <CircularProgress />
          </Grid>
        ) : (
          exchangeSummary.map((summary) => (
            <Grid item xs={12} sm={6} md={4} lg={2} key={summary.exchange}>
              <Paper 
                sx={{ 
                  p: 2, 
                  textAlign: 'center',
                  cursor: 'pointer',
                  border: currentExchange === summary.exchange ? '2px solid #1976d2' : 'none',
                  backgroundColor: summary.overallStatus === 'down' 
                    ? 'rgba(211, 47, 47, 0.1)' 
                    : summary.overallStatus === 'degraded' 
                      ? 'rgba(255, 152, 0, 0.1)' 
                      : 'rgba(46, 125, 50, 0.1)'
                }}
                onClick={() => setCurrentExchange(summary.exchange)}
              >
                <Typography variant="h6" component="div">
                  {summary.exchange}
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mt: 1 }}>
                  <Chip 
                    label={`API: ${summary.apiStatus}`} 
                    color={getStatusColor(summary.apiStatus)}
                    size="small"
                  />
                  <Chip 
                    label={`Webhook: ${summary.webhookStatus}`} 
                    color={getStatusColor(summary.webhookStatus)}
                    size="small"
                  />
                </Box>
              </Paper>
            </Grid>
          ))
        )}
      </Grid>

      {/* Exchange Selection */}
      <Box sx={{ mb: 2, display: 'flex', alignItems: 'center' }}>
        <FormControl sx={{ minWidth: 200, mr: 3 }}>
          <InputLabel>Exchange</InputLabel>
          <Select
            value={currentExchange}
            onChange={handleExchangeChange}
            label="Exchange"
          >
            {exchanges.map((exchange) => (
              <MenuItem key={exchange} value={exchange}>{exchange}</MenuItem>
            ))}
          </Select>
        </FormControl>

        {/* Tab Selection */}
        <Tabs value={currentTab} onChange={handleTabChange} aria-label="exchange monitoring tabs">
          <Tab label="Overview" />
          <Tab label="Alert Settings" />
          <Tab label="Webhook Tester" />
          <Tab label="API Tester" />
        </Tabs>
      </Box>

      {/* Tab Content */}
      {currentTab === 0 && (
        <ExchangePanel exchange={currentExchange} />
      )}
      
      {currentTab === 1 && (
        <ExchangeAlertSettings exchange={currentExchange} />
      )}
      
      {currentTab === 2 && (
        <WebhookTester exchange={currentExchange} />
      )}
      
      {currentTab === 3 && (
        <ApiTester exchange={currentExchange} />
      )}
    </Box>
  );
};

export default ExchangeMonitoring;
