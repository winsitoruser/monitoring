import React, { useState, useEffect } from 'react';
import {
  Box, Card, CardContent, Typography, Grid, Chip, CircularProgress,
  Tooltip, Divider, Stack, IconButton
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import WarningIcon from '@mui/icons-material/Warning';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import { format } from 'date-fns';
import integrationService from '../../services/integrationService';

const ConsolidatedStatusCard = () => {
  const [loading, setLoading] = useState(true);
  const [exchangeStatus, setExchangeStatus] = useState([]);
  const [systemStatus, setSystemStatus] = useState({
    xenorize: { api: 'unknown', bots: 'unknown', overall: 'unknown' },
    cryptellar: { api: 'unknown', bots: 'unknown', overall: 'unknown' }
  });
  const [lastUpdated, setLastUpdated] = useState(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch exchange status
      const exchangeData = await integrationService.getExchangeHealthSummary();
      setExchangeStatus(exchangeData);
      
      // Fetch system status
      const xenorizeApiStatus = await integrationService.getApiStatus('xenorize');
      const xenorizeBotStatus = await integrationService.getBotStatus('xenorize');
      const cryptellarApiStatus = await integrationService.getApiStatus('cryptellar');
      const cryptellarBotStatus = await integrationService.getBotStatus('cryptellar');
      
      const calculateOverallStatus = (apiStatus, botStatus) => {
        if (apiStatus === 'down' || botStatus === 'down') return 'down';
        if (apiStatus === 'degraded' || botStatus === 'degraded') return 'degraded';
        return 'healthy';
      };
      
      setSystemStatus({
        xenorize: {
          api: xenorizeApiStatus.status,
          bots: xenorizeBotStatus.status,
          overall: calculateOverallStatus(xenorizeApiStatus.status, xenorizeBotStatus.status)
        },
        cryptellar: {
          api: cryptellarApiStatus.status,
          bots: cryptellarBotStatus.status,
          overall: calculateOverallStatus(cryptellarApiStatus.status, cryptellarBotStatus.status)
        }
      });
      
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error fetching consolidated status:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    
    // Set up auto-refresh every 5 minutes
    const intervalId = setInterval(() => {
      fetchData();
    }, 5 * 60 * 1000);
    
    return () => clearInterval(intervalId);
  }, []);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon sx={{ color: 'success.main' }} />;
      case 'degraded':
        return <WarningIcon sx={{ color: 'warning.main' }} />;
      case 'down':
        return <ErrorIcon sx={{ color: 'error.main' }} />;
      default:
        return <CircularProgress size={20} />;
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

  const calculateOverallHealth = () => {
    // Count exchanges with issues
    const exchangesWithIssues = exchangeStatus.filter(
      exchange => exchange.overallStatus === 'down' || exchange.overallStatus === 'degraded'
    ).length;
    
    // Calculate overall system health
    const systemsWithIssues = 
      (systemStatus.xenorize.overall !== 'healthy' ? 1 : 0) + 
      (systemStatus.cryptellar.overall !== 'healthy' ? 1 : 0);
    
    if (systemsWithIssues > 0 || exchangesWithIssues > exchangeStatus.length / 2) {
      return 'critical';
    } else if (systemsWithIssues === 0 && exchangesWithIssues > 0) {
      return 'warning';
    } else {
      return 'healthy';
    }
  };

  return (
    <Card variant="outlined">
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5">Consolidated System Status</Typography>
          <Box>
            {lastUpdated && (
              <Tooltip title="Last updated">
                <Typography variant="caption" sx={{ mr: 2 }}>
                  {format(lastUpdated, 'MMM d, HH:mm:ss')}
                </Typography>
              </Tooltip>
            )}
            <Tooltip title="Refresh status">
              <IconButton onClick={fetchData} disabled={loading} size="small">
                {loading ? <CircularProgress size={20} /> : <RefreshIcon />}
              </IconButton>
            </Tooltip>
          </Box>
        </Box>
        
        {loading && !lastUpdated ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {/* Overall Health Banner */}
            <Box 
              sx={{ 
                p: 1, 
                mb: 2, 
                borderRadius: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: 
                  calculateOverallHealth() === 'critical' ? 'error.light' :
                  calculateOverallHealth() === 'warning' ? 'warning.light' :
                  'success.light'
              }}
            >
              {calculateOverallHealth() === 'critical' ? (
                <ErrorIcon sx={{ mr: 1, color: 'error.main' }} />
              ) : calculateOverallHealth() === 'warning' ? (
                <WarningIcon sx={{ mr: 1, color: 'warning.main' }} />
              ) : (
                <CheckCircleIcon sx={{ mr: 1, color: 'success.main' }} />
              )}
              <Typography variant="h6" component="div">
                {calculateOverallHealth() === 'critical' ? 'Critical Issues Detected' :
                 calculateOverallHealth() === 'warning' ? 'Some Services Degraded' :
                 'All Systems Operational'}
              </Typography>
            </Box>
            
            {/* Xenorize & Cryptellar Status */}
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={12} sm={6}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      {getStatusIcon(systemStatus.xenorize.overall)}
                      <Typography variant="h6" sx={{ ml: 1 }}>Xenorize Platform</Typography>
                    </Box>
                    <Divider sx={{ mb: 1 }} />
                    <Stack direction="row" spacing={1}>
                      <Chip 
                        label={`API: ${systemStatus.xenorize.api}`}
                        color={getStatusColor(systemStatus.xenorize.api)}
                        size="small"
                      />
                      <Chip 
                        label={`Bots: ${systemStatus.xenorize.bots}`}
                        color={getStatusColor(systemStatus.xenorize.bots)}
                        size="small"
                      />
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <Card variant="outlined" sx={{ height: '100%' }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      {getStatusIcon(systemStatus.cryptellar.overall)}
                      <Typography variant="h6" sx={{ ml: 1 }}>Cryptellar Platform</Typography>
                    </Box>
                    <Divider sx={{ mb: 1 }} />
                    <Stack direction="row" spacing={1}>
                      <Chip 
                        label={`API: ${systemStatus.cryptellar.api}`}
                        color={getStatusColor(systemStatus.cryptellar.api)}
                        size="small"
                      />
                      <Chip 
                        label={`Bots: ${systemStatus.cryptellar.bots}`}
                        color={getStatusColor(systemStatus.cryptellar.bots)}
                        size="small"
                      />
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
            
            {/* Exchange Status */}
            <Typography variant="h6" gutterBottom>Exchange Connectivity</Typography>
            <Grid container spacing={1}>
              {exchangeStatus.map((exchange) => (
                <Grid item xs={6} sm={4} md={2} key={exchange.exchange}>
                  <Card 
                    variant="outlined" 
                    sx={{ 
                      p: 1, 
                      textAlign: 'center',
                      backgroundColor: exchange.overallStatus === 'down' 
                        ? 'rgba(211, 47, 47, 0.1)' 
                        : exchange.overallStatus === 'degraded' 
                          ? 'rgba(255, 152, 0, 0.1)' 
                          : 'rgba(46, 125, 50, 0.1)'
                    }}
                  >
                    <Typography variant="subtitle2">
                      {exchange.exchange}
                    </Typography>
                    {getStatusIcon(exchange.overallStatus)}
                  </Card>
                </Grid>
              ))}
            </Grid>
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default ConsolidatedStatusCard;
