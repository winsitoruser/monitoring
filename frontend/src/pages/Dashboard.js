import React, { useEffect, useState } from 'react';
import { useRecoilState, useSetRecoilState } from 'recoil';
import {
  Grid, Card, CardHeader, CardContent, Typography, Box,
  Divider, CircularProgress, Paper, Chip, Avatar,
  List, ListItem, ListItemText, ListItemAvatar,
  IconButton, Tooltip
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import StorageIcon from '@mui/icons-material/Storage';
import ApiIcon from '@mui/icons-material/Api';
import { useSnackbar } from 'notistack';
import { systemStatusState, apiMonitoringState, botMonitoringState, databaseMonitoringState } from '../utils/atoms';
import api from '../services/api';
import StatusCard from '../components/StatusCard';
import OverviewChart from '../components/OverviewChart';
import ConsolidatedStatusCard from '../components/exchange/ConsolidatedStatusCard';

const Dashboard = () => {
  const { enqueueSnackbar } = useSnackbar();
  const [loading, setLoading] = useState(true);
  const [systemStatus, setSystemStatus] = useRecoilState(systemStatusState);
  const setApiMonitoring = useSetRecoilState(apiMonitoringState);
  const setBotMonitoring = useSetRecoilState(botMonitoringState);
  const setDatabaseMonitoring = useSetRecoilState(databaseMonitoringState);
  const [refreshing, setRefreshing] = useState(false);
  
  const fetchAllData = async () => {
    setRefreshing(true);
    try {
      // Fetch system status
      const statusData = await api.getSystemStatus();
      setSystemStatus({
        ...systemStatus,
        ...statusData,
        lastUpdated: new Date().toISOString()
      });
      
      // Fetch API monitoring data
      const apiData = await api.getApiMonitoring();
      setApiMonitoring({
        endpoints: apiData.endpoints || [],
        lastChecked: apiData.lastChecked || new Date().toISOString(),
        loading: false
      });
      
      // Fetch bot monitoring data
      const botData = await api.getBotMonitoring();
      setBotMonitoring({
        bots: botData.bots || [],
        lastChecked: botData.lastChecked || new Date().toISOString(),
        loading: false
      });
      
      // Fetch database monitoring data
      const dbData = await api.getDatabaseMonitoring();
      setDatabaseMonitoring({
        databases: dbData.databases || [],
        lastChecked: dbData.lastChecked || new Date().toISOString(),
        loading: false
      });
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching monitoring data:', error);
      enqueueSnackbar('Failed to fetch monitoring data. Please check your connection and API settings.', { 
        variant: 'error',
        autoHideDuration: 5000
      });
    } finally {
      setRefreshing(false);
    }
  };
  
  useEffect(() => {
    fetchAllData();
    
    // Set up polling interval
    const interval = setInterval(() => {
      fetchAllData();
    }, 30000); // Poll every 30 seconds
    
    return () => clearInterval(interval);
  }, []);
  
  const handleRefresh = () => {
    fetchAllData();
  };
  
  // Helper function to get status counts
  const getStatusCounts = () => {
    if (!systemStatus || !systemStatus.targets) {
      return { healthy: 0, warning: 0, critical: 0, total: 0 };
    }
    
    const counts = {
      healthy: systemStatus.targets.filter(t => t.status === 'healthy').length,
      warning: systemStatus.targets.filter(t => t.status === 'warning').length,
      critical: systemStatus.targets.filter(t => t.status === 'failed').length,
      total: systemStatus.targets.length
    };
    
    return counts;
  };
  
  // Get platform specific counts
  const getPlatformCounts = (platform) => {
    if (!systemStatus || !systemStatus.targets) {
      return { healthy: 0, warning: 0, critical: 0, total: 0 };
    }
    
    const platformTargets = systemStatus.targets.filter(t => 
      t.group && t.group.toLowerCase() === platform.toLowerCase()
    );
    
    return {
      healthy: platformTargets.filter(t => t.status === 'healthy').length,
      warning: platformTargets.filter(t => t.status === 'warning').length,
      critical: platformTargets.filter(t => t.status === 'failed').length,
      total: platformTargets.length
    };
  };
  
  // Get status color
  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'warning':
        return 'warning';
      case 'failed':
        return 'error';
      default:
        return 'default';
    }
  };
  
  // Get status icon
  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon />;
      case 'warning':
        return <WarningIcon />;
      case 'failed':
        return <ErrorIcon />;
      default:
        return <CircularProgress size={24} />;
    }
  };
  
  // Get recent incidents from systemStatus
  const getRecentIncidents = () => {
    if (!systemStatus || !systemStatus.targets) {
      return [];
    }
    
    return systemStatus.targets
      .filter(t => t.status === 'failed' || t.status === 'warning')
      .sort((a, b) => new Date(b.lastCheck) - new Date(a.lastCheck))
      .slice(0, 5);
  };
  
  const statusCounts = getStatusCounts();
  const xenorizeCounts = getPlatformCounts('xenorize');
  const cryptellarCounts = getPlatformCounts('cryptellar');
  const recentIncidents = getRecentIncidents();
  
  return (
    <Box className="dashboard-container">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          System Dashboard
        </Typography>
        <Tooltip title="Refresh Data">
          <IconButton onClick={handleRefresh} disabled={refreshing}>
            {refreshing ? <CircularProgress size={24} /> : <RefreshIcon />}
          </IconButton>
        </Tooltip>
      </Box>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 5 }}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          {/* Consolidated Status Overview */}
          <Grid item xs={12}>
            <ConsolidatedStatusCard />
          </Grid>
          
          {/* Overview Cards */}
          <Grid item xs={12} md={4}>
            <StatusCard 
              title="Overall Status" 
              counts={statusCounts}
              lastUpdated={systemStatus.lastUpdated}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <StatusCard 
              title="Xenorize Platform" 
              counts={xenorizeCounts}
              type="xenorize"
              lastUpdated={systemStatus.lastUpdated}
            />
          </Grid>
          <Grid item xs={12} md={4}>
            <StatusCard 
              title="Cryptellar Platform" 
              counts={cryptellarCounts}
              type="cryptellar"
              lastUpdated={systemStatus.lastUpdated}
            />
          </Grid>
          
          {/* Charts */}
          <Grid item xs={12} lg={8}>
            <Card>
              <CardHeader 
                title="Status Overview" 
                subheader="Last 24 hours" 
              />
              <CardContent>
                <OverviewChart />
              </CardContent>
            </Card>
          </Grid>
          
          {/* Recent Incidents */}
          <Grid item xs={12} lg={4}>
            <Card sx={{ height: '100%' }}>
              <CardHeader 
                title="Recent Incidents" 
                subheader={recentIncidents.length > 0 ? 
                  `${recentIncidents.length} incidents detected` : 
                  "No incidents detected"
                }
              />
              <CardContent>
                {recentIncidents.length > 0 ? (
                  <List>
                    {recentIncidents.map((incident) => (
                      <React.Fragment key={incident.id}>
                        <ListItem>
                          <ListItemAvatar>
                            <Avatar sx={{ 
                              bgcolor: incident.status === 'failed' ? 'error.main' : 'warning.main' 
                            }}>
                              {getStatusIcon(incident.status)}
                            </Avatar>
                          </ListItemAvatar>
                          <ListItemText 
                            primary={incident.name || incident.target}
                            secondary={`${incident.message || 'Check failed'} • ${new Date(incident.lastCheck).toLocaleTimeString()}`}
                          />
                          <Chip 
                            label={incident.group || 'Unknown'} 
                            size="small"
                            color={incident.group === 'xenorize' ? 'primary' : 'secondary'}
                          />
                        </ListItem>
                        <Divider variant="inset" component="li" />
                      </React.Fragment>
                    ))}
                  </List>
                ) : (
                  <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '200px' }}>
                    <Typography variant="body1" color="text.secondary">
                      All systems operational
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
          
          {/* Service Status */}
          <Grid item xs={12}>
            <Card>
              <CardHeader title="Service Status" />
              <CardContent>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2, display: 'flex', alignItems: 'center' }}>
                      <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                        <ApiIcon />
                      </Avatar>
                      <Box>
                        <Typography variant="h6">API Services</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {statusCounts.critical > 0 ? (
                            <span>
                              <ErrorIcon fontSize="small" color="error" /> Issues detected
                            </span>
                          ) : (
                            <span>
                              <CheckCircleIcon fontSize="small" color="success" /> Operational
                            </span>
                          )}
                        </Typography>
                      </Box>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2, display: 'flex', alignItems: 'center' }}>
                      <Avatar sx={{ bgcolor: 'secondary.main', mr: 2 }}>
                        <SmartToyIcon />
                      </Avatar>
                      <Box>
                        <Typography variant="h6">Bot Systems</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {systemStatus.botStatus === 'failed' ? (
                            <span>
                              <ErrorIcon fontSize="small" color="error" /> Issues detected
                            </span>
                          ) : (
                            <span>
                              <CheckCircleIcon fontSize="small" color="success" /> Operational
                            </span>
                          )}
                        </Typography>
                      </Box>
                    </Paper>
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Paper sx={{ p: 2, display: 'flex', alignItems: 'center' }}>
                      <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                        <StorageIcon />
                      </Avatar>
                      <Box>
                        <Typography variant="h6">Databases</Typography>
                        <Typography variant="body2" color="text.secondary">
                          {systemStatus.dbStatus === 'failed' ? (
                            <span>
                              <ErrorIcon fontSize="small" color="error" /> Issues detected
                            </span>
                          ) : (
                            <span>
                              <CheckCircleIcon fontSize="small" color="success" /> Operational
                            </span>
                          )}
                        </Typography>
                      </Box>
                    </Paper>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default Dashboard;
