import React, { useState, useEffect } from 'react';
import {
  Box, Typography, Card, CardContent, Switch, FormControl,
  FormControlLabel, Grid, Slider, TextField, MenuItem, Select, InputLabel,
  Divider, Chip, Button, CircularProgress, Alert
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import { useSnackbar } from 'notistack';

const ExchangeAlertSettings = ({ exchange }) => {
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [settings, setSettings] = useState({
    enabled: true,
    notifyOnApiDown: true,
    notifyOnWebhookDown: true,
    notifyOnApiDegraded: true,
    notifyOnWebhookDegraded: false,
    apiResponseTimeThreshold: 500,
    webhookDelayThreshold: 120,
    notificationChannels: ['telegram', 'email'],
    criticalEndpoints: ['market', 'trade'],
  });

  const { enqueueSnackbar } = useSnackbar();

  // Simulating loading settings for the specific exchange
  useEffect(() => {
    setLoading(true);
    // In a real implementation, this would fetch from the backend
    setTimeout(() => {
      // This simulates loading exchange-specific settings
      setLoading(false);
    }, 800);
  }, [exchange]);

  const handleSwitchChange = (event) => {
    setSettings({
      ...settings,
      [event.target.name]: event.target.checked
    });
  };

  const handleSliderChange = (name) => (event, newValue) => {
    setSettings({
      ...settings,
      [name]: newValue
    });
  };

  const handleChannelChange = (event) => {
    setSettings({
      ...settings,
      notificationChannels: event.target.value
    });
  };

  const handleEndpointChange = (event) => {
    setSettings({
      ...settings,
      criticalEndpoints: event.target.value
    });
  };

  const handleSave = () => {
    setLoading(true);
    
    // Simulate saving to backend
    setTimeout(() => {
      setLoading(false);
      setSaved(true);
      enqueueSnackbar(`Alert settings for ${exchange} saved successfully`, { variant: 'success' });
      
      // Reset saved state after showing message
      setTimeout(() => setSaved(false), 3000);
    }, 1000);
  };

  const allEndpoints = ['market', 'trade', 'account', 'userdata', 'position', 'wallet', 'depth', 'ticker'];
  const notificationChannelOptions = ['telegram', 'email', 'sms', 'webhook'];

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Alert Settings for {exchange}
        </Typography>
        
        {saved && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Settings saved successfully
          </Alert>
        )}
        
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.enabled}
                  onChange={handleSwitchChange}
                  name="enabled"
                  color="primary"
                />
              }
              label="Enable Alerts"
            />
          </Grid>
          
          <Grid item xs={12}>
            <Divider>
              <Chip label="Notification Triggers" />
            </Divider>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.notifyOnApiDown}
                  onChange={handleSwitchChange}
                  name="notifyOnApiDown"
                  color="primary"
                  disabled={!settings.enabled}
                />
              }
              label="Notify when API is down"
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.notifyOnWebhookDown}
                  onChange={handleSwitchChange}
                  name="notifyOnWebhookDown"
                  color="primary"
                  disabled={!settings.enabled}
                />
              }
              label="Notify when Webhook is down"
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.notifyOnApiDegraded}
                  onChange={handleSwitchChange}
                  name="notifyOnApiDegraded"
                  color="primary"
                  disabled={!settings.enabled}
                />
              }
              label="Notify on API performance degradation"
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.notifyOnWebhookDegraded}
                  onChange={handleSwitchChange}
                  name="notifyOnWebhookDegraded"
                  color="primary"
                  disabled={!settings.enabled}
                />
              }
              label="Notify on Webhook delay"
            />
          </Grid>
          
          <Grid item xs={12}>
            <Divider>
              <Chip label="Thresholds" />
            </Divider>
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Typography id="api-response-time-slider" gutterBottom>
              API Response Time Threshold: {settings.apiResponseTimeThreshold} ms
            </Typography>
            <Slider
              value={settings.apiResponseTimeThreshold}
              onChange={handleSliderChange('apiResponseTimeThreshold')}
              aria-labelledby="api-response-time-slider"
              valueLabelDisplay="auto"
              step={50}
              marks
              min={100}
              max={2000}
              disabled={!settings.enabled || !settings.notifyOnApiDegraded}
            />
          </Grid>
          
          <Grid item xs={12} sm={6}>
            <Typography id="webhook-delay-slider" gutterBottom>
              Webhook Delay Threshold: {settings.webhookDelayThreshold} seconds
            </Typography>
            <Slider
              value={settings.webhookDelayThreshold}
              onChange={handleSliderChange('webhookDelayThreshold')}
              aria-labelledby="webhook-delay-slider"
              valueLabelDisplay="auto"
              step={10}
              marks
              min={10}
              max={300}
              disabled={!settings.enabled || !settings.notifyOnWebhookDegraded}
            />
          </Grid>
          
          <Grid item xs={12}>
            <Divider>
              <Chip label="Notification Channels" />
            </Divider>
          </Grid>
          
          <Grid item xs={12}>
            <FormControl fullWidth disabled={!settings.enabled}>
              <InputLabel>Notification Channels</InputLabel>
              <Select
                multiple
                value={settings.notificationChannels}
                onChange={handleChannelChange}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => (
                      <Chip key={value} label={value} />
                    ))}
                  </Box>
                )}
              >
                {notificationChannelOptions.map((channel) => (
                  <MenuItem key={channel} value={channel}>
                    {channel}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12}>
            <Divider>
              <Chip label="Critical Endpoints" />
            </Divider>
          </Grid>
          
          <Grid item xs={12}>
            <FormControl fullWidth disabled={!settings.enabled}>
              <InputLabel>Critical Endpoints</InputLabel>
              <Select
                multiple
                value={settings.criticalEndpoints}
                onChange={handleEndpointChange}
                renderValue={(selected) => (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                    {selected.map((value) => (
                      <Chip key={value} label={value} />
                    ))}
                  </Box>
                )}
              >
                {allEndpoints.map((endpoint) => (
                  <MenuItem key={endpoint} value={endpoint}>
                    {endpoint}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
            <Button 
              variant="contained" 
              color="primary"
              startIcon={<SaveIcon />}
              onClick={handleSave}
              disabled={loading}
            >
              {loading ? <CircularProgress size={24} /> : 'Save Settings'}
            </Button>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default ExchangeAlertSettings;
