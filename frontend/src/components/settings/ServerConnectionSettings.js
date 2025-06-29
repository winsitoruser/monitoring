import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  IconButton,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  Switch,
  FormControlLabel,
  CircularProgress,
  Tooltip,
  Alert,
  AlertTitle
} from '@mui/material';
import VisibilityIcon from '@mui/icons-material/Visibility';
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import SaveIcon from '@mui/icons-material/Save';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import { useSnackbar } from 'notistack';
import { useRecoilValue } from 'recoil';  
import { settingsState } from '../../atoms/settings';

const SERVER_TYPES = [
  { value: 'api', label: 'API Server' },
  { value: 'web', label: 'Web Server' },
  { value: 'database', label: 'Database Server' },
  { value: 'trading', label: 'Trading Server' },
  { value: 'proxy', label: 'Proxy Server' },
  { value: 'custom', label: 'Custom Server' },
];

const MONITORING_PROTOCOLS = [
  { value: 'http', label: 'HTTP' },
  { value: 'https', label: 'HTTPS' },
  { value: 'tcp', label: 'TCP' },
  { value: 'ping', label: 'PING' },
  { value: 'ssh', label: 'SSH' },
];

const DEFAULT_SERVER_CONFIG = {
  serverName: '',
  serverType: '',
  hostname: '',
  port: '',
  monitoringProtocol: 'http',
  healthEndpoint: '/health',
  authToken: '',
  sshKey: '',
  checkInterval: 60,
  isActive: true,
  lastTested: null,
  connectionStatus: null,
};

const ServerConnectionSettings = () => {
  const { enqueueSnackbar } = useSnackbar();
  const [configurations, setConfigurations] = useState([]);
  const [showSecrets, setShowSecrets] = useState({});
  const [loading, setLoading] = useState(true);
  const [testingConnection, setTestingConnection] = useState({});

  // Get API settings
  const settings = useRecoilValue(settingsState);
  
  useEffect(() => {
    // Load configurations from backend API
    loadConfigurations();
  }, []);

  const loadConfigurations = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${settings.apiUrl}/connections/servers`, {
        headers: {
          'X-API-Key': settings.apiKey
        }
      });
      
      if (response.data && response.data.length > 0) {
        setConfigurations(response.data);
      } else {
        // Initialize with an empty configuration if no saved configurations
        setConfigurations([{ ...DEFAULT_SERVER_CONFIG, id: null }]);
      }
    } catch (error) {
      console.error('Error loading server configurations:', error);
      enqueueSnackbar('Failed to load server configurations from API', { variant: 'error' });
      
      // Fallback to localStorage if available
      try {
        const savedConfigs = localStorage.getItem('serverConfigurations');
        if (savedConfigs) {
          const configs = JSON.parse(savedConfigs);
          setConfigurations(configs);
          enqueueSnackbar('Loaded configurations from local storage as fallback', { variant: 'warning' });
        } else {
          // Initialize with an empty configuration
          setConfigurations([{ ...DEFAULT_SERVER_CONFIG, id: null }]);
        }
      } catch (localError) {
        // Initialize with an empty configuration on error
        setConfigurations([{ ...DEFAULT_SERVER_CONFIG, id: null }]);
      }
    } finally {
      setLoading(false);
    }
  };

  const generateTempId = () => `temp_server_${Date.now()}_${Math.floor(Math.random() * 1000)}`;
  
  // Check if a configuration has a temporary ID (for new configs not yet saved to backend)
  const isTemporaryConfig = (config) => {
    return !config.id || config.id.toString().startsWith('temp_');
  };

  const toggleSecretVisibility = (id) => {
    setShowSecrets(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const handleInputChange = (id, field, value) => {
    setConfigurations(prevConfigs => 
      prevConfigs.map(config => 
        config.id === id ? { ...config, [field]: value } : config
      )
    );
  };

  const addNewConfiguration = () => {
    setConfigurations(prev => [
      ...prev,
      { ...DEFAULT_SERVER_CONFIG, id: generateTempId() }
    ]);
  };

  const removeConfiguration = async (id) => {
    try {
      // If it's a temporary configuration, just remove from state
      if (id.toString().startsWith('temp_')) {
        setConfigurations(prev => prev.filter(config => config.id !== id));
        return;
      }
      
      // Otherwise, delete from backend
      await axios.delete(`${settings.apiUrl}/connections/servers/${id}`, {
        headers: {
          'X-API-Key': settings.apiKey
        }
      });
      
      setConfigurations(prev => prev.filter(config => config.id !== id));
      enqueueSnackbar('Server configuration removed', { variant: 'success' });
    } catch (error) {
      console.error('Error removing server configuration:', error);
      enqueueSnackbar('Failed to remove server configuration', { variant: 'error' });
    }
  };

  const saveConfigurations = async () => {
    try {
      // Save all configurations to backend
      const savedConfigs = [];
      let hasErrors = false;
      
      // Process each configuration
      for (const config of configurations) {
        if (!config.serverName || !config.hostname) {
          enqueueSnackbar(`Server name and hostname are required for all configurations`, { variant: 'warning' });
          return;
        }
        
        try {
          // For new configurations, create them
          if (isTemporaryConfig(config)) {
            const { id, ...configData } = config;
            const response = await axios.post(`${settings.apiUrl}/connections/servers`, configData, {
              headers: {
                'X-API-Key': settings.apiKey
              }
            });
            savedConfigs.push(response.data);
          } 
          // For existing configurations, update them
          else {
            const response = await axios.put(`${settings.apiUrl}/connections/servers/${config.id}`, config, {
              headers: {
                'X-API-Key': settings.apiKey
              }
            });
            savedConfigs.push(response.data);
          }
        } catch (error) {
          console.error(`Error saving server configuration ${config.serverName}:`, error);
          hasErrors = true;
        }
      }
      
      // Also save to localStorage as backup
      try {
        localStorage.setItem('serverConfigurations', JSON.stringify(configurations));
      } catch (localError) {
        console.warn('Failed to save backup to localStorage:', localError);
      }
      
      if (hasErrors) {
        enqueueSnackbar('Some configurations could not be saved', { variant: 'warning' });
      } else {
        enqueueSnackbar('Server configurations saved successfully', { variant: 'success' });
      }
      
      // Reload configurations to get server-generated IDs
      loadConfigurations();
    } catch (error) {
      console.error('Error saving server configurations:', error);
      enqueueSnackbar('Failed to save server configurations', { variant: 'error' });
    }
  };

  const testConnection = async (config) => {
    if (!config.serverName || !config.hostname) {
      enqueueSnackbar('Server name and hostname are required', { variant: 'warning' });
      return;
    }

    setTestingConnection(prev => ({ ...prev, [config.id]: true }));
    
    try {
      enqueueSnackbar(`Testing connection to ${config.serverName}...`, { variant: 'info' });
      
      // Prepare connection test data
      const testData = {
        connectionType: 'server',
        connectionData: {
          hostname: config.hostname,
          port: config.port ? parseInt(config.port) : undefined,
          monitoringProtocol: config.monitoringProtocol,
          healthEndpoint: config.healthEndpoint,
          authToken: config.authToken,
          sshKey: config.sshKey
        }
      };
      
      // For existing configurations with IDs from backend, use connectionId instead
      if (!isTemporaryConfig(config)) {
        delete testData.connectionData;
        testData.connectionId = config.id;
      }
      
      // Call backend API to test the connection
      const response = await axios.post(
        `${settings.apiUrl}/connections/test/server`,
        testData,
        {
          headers: {
            'X-API-Key': settings.apiKey
          }
        }
      );
      
      const result = response.data;
      const success = result.success;
      
      // Update configuration status
      setConfigurations(prevConfigs => 
        prevConfigs.map(c => 
          c.id === config.id ? { 
            ...c, 
            connectionStatus: success, 
            lastTested: new Date().toISOString(),
            lastError: success ? null : result.message 
          } : c
        )
      );
      
      if (success) {
        enqueueSnackbar(`Connection to ${config.serverName} successful`, { variant: 'success' });
      } else {
        enqueueSnackbar(`Connection failed: ${result.message}`, { variant: 'error' });
      }
    } catch (error) {
      console.error('Error testing server connection:', error);
      let errorMessage = 'Connection failed';
      
      // Extract error message from API response if available
      if (error.response && error.response.data && error.response.data.detail) {
        errorMessage = error.response.data.detail;
      }
      
      enqueueSnackbar(`${errorMessage}`, { variant: 'error' });
      
      // Update connection status
      setConfigurations(prevConfigs => 
        prevConfigs.map(c => 
          c.id === config.id ? { 
            ...c, 
            connectionStatus: false, 
            lastTested: new Date().toISOString(),
            lastError: errorMessage
          } : c
        )
      );
    } finally {
      setTestingConnection(prev => ({ ...prev, [config.id]: false }));
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Server Connection Settings
        </Typography>
        <Typography variant="body2" color="textSecondary" paragraph>
          Configure server connections for monitoring and alerts. Add multiple servers to monitor their status.
        </Typography>
        
        {!settings.apiKey && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            <AlertTitle>API Key Required</AlertTitle>
            Please configure your API key in the main settings page to enable connection testing and secure storage.
          </Alert>
        )}
        
        {configurations.map((config, index) => (
          <Box key={config.id} sx={{ mb: 4 }}>
            {index > 0 && <Divider sx={{ my: 3 }} />}
            
            <Grid container spacing={2} alignItems="flex-start">
              <Grid item xs={12} sm={6} md={3}>
                <TextField
                  label="Server Name"
                  value={config.serverName}
                  onChange={(e) => handleInputChange(config.id, 'serverName', e.target.value)}
                  fullWidth
                  margin="normal"
                  required
                />
              </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth margin="normal">
                <InputLabel id={`server-type-select-${config.id}`}>Server Type</InputLabel>
                <Select
                  labelId={`server-type-select-${config.id}`}
                  value={config.serverType}
                  label="Server Type"
                  onChange={(e) => handleInputChange(config.id, 'serverType', e.target.value)}
                >
                  {SERVER_TYPES.map(option => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={4}>
              <TextField
                label="Hostname/IP"
                value={config.hostname}
                onChange={(e) => handleInputChange(config.id, 'hostname', e.target.value)}
                fullWidth
                margin="normal"
                required
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={2}>
              <TextField
                label="Port"
                value={config.port}
                onChange={(e) => handleInputChange(config.id, 'port', e.target.value)}
                fullWidth
                margin="normal"
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <FormControl fullWidth margin="normal">
                <InputLabel id={`protocol-select-${config.id}`}>Monitoring Protocol</InputLabel>
                <Select
                  labelId={`protocol-select-${config.id}`}
                  value={config.monitoringProtocol}
                  label="Monitoring Protocol"
                  onChange={(e) => handleInputChange(config.id, 'monitoringProtocol', e.target.value)}
                >
                  {MONITORING_PROTOCOLS.map(option => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                label="Health Check Endpoint"
                value={config.healthEndpoint}
                onChange={(e) => handleInputChange(config.id, 'healthEndpoint', e.target.value)}
                fullWidth
                margin="normal"
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                label="Check Interval (seconds)"
                type="number"
                value={config.checkInterval}
                onChange={(e) => handleInputChange(config.id, 'checkInterval', e.target.value)}
                fullWidth
                margin="normal"
                inputProps={{ min: 10, step: 5 }}
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={3}>
              <TextField
                label="Auth Token (if required)"
                value={config.authToken}
                onChange={(e) => handleInputChange(config.id, 'authToken', e.target.value)}
                fullWidth
                margin="normal"
                type={showSecrets[config.id] ? 'text' : 'password'}
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        onClick={() => toggleSecretVisibility(config.id)}
                        edge="end"
                      >
                        {showSecrets[config.id] ? <VisibilityOffIcon /> : <VisibilityIcon />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            </Grid>
            
            <Grid item xs={12} sm={6} md={12}>
              {(config.monitoringProtocol === 'ssh') && (
                <TextField
                  label="SSH Key"
                  value={config.sshKey}
                  onChange={(e) => handleInputChange(config.id, 'sshKey', e.target.value)}
                  fullWidth
                  margin="normal"
                  multiline
                  rows={3}
                  placeholder="-----BEGIN RSA PRIVATE KEY-----..."
                />
              )}
            </Grid>
            
            <Grid item xs={12} sx={{ mt: 1 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={config.isActive}
                    onChange={(e) => handleInputChange(config.id, 'isActive', e.target.checked)}
                    color="primary"
                  />
                }
                label="Monitor this server"
              />
            </Grid>
            
            <Grid item xs={12} sx={{ mt: 2, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, flexGrow: 1 }}>
                <Button
                  variant="outlined"
                  color="primary"
                  onClick={() => testConnection(config)}
                  disabled={testingConnection[config.id]}
                >
                  {testingConnection[config.id] ? (
                    <CircularProgress size={24} sx={{ mr: 1 }} />
                  ) : 'Test Connection'}
                </Button>
                
                <Typography variant="caption" display="block" gutterBottom>
                  {config.connectionStatus === true ? (
                    <Box sx={{ display: 'flex', alignItems: 'center', color: 'success.main' }}>
                      <CheckCircleOutlineIcon fontSize="small" sx={{ mr: 0.5 }} />
                      Last test: Successful
                      {config.lastTested && ` (${new Date(config.lastTested).toLocaleString()})`}
                    </Box>
                  ) : config.connectionStatus === false ? (
                    <Box sx={{ display: 'flex', alignItems: 'center', color: 'error.main' }}>
                      <ErrorOutlineIcon fontSize="small" sx={{ mr: 0.5 }} />
                      Last test: Failed
                      {config.lastTested && ` (${new Date(config.lastTested).toLocaleString()})`}
                      {config.lastError && (
                        <Tooltip title={config.lastError} arrow>
                          <HelpOutlineIcon fontSize="small" sx={{ ml: 0.5 }} />
                        </Tooltip>
                      )}
                    </Box>
                  ) : null}
                </Typography>
              </Box>
              
              <IconButton 
                color="error"
                onClick={() => removeConfiguration(config.id)}
                disabled={configurations.length === 1}
              >
                <DeleteIcon />
              </IconButton>
            </Grid>
            </Grid>
          </Box>
        ))}
        
        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
          <Button 
            startIcon={<AddIcon />} 
            onClick={addNewConfiguration}
          >
            Add Server
          </Button>
          
          <Button
            variant="contained"
            color="primary"
            startIcon={<SaveIcon />}
            onClick={saveConfigurations}
          >
            Save All Server Configurations
          </Button>
        </Box>
      </CardContent>
    </Card>
  );
};

export default ServerConnectionSettings;
