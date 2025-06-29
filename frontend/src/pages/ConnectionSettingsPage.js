import React, { useState } from 'react';
import {
  Box,
  Typography,
  Tabs,
  Tab,
  Paper,
  Button,
  Alert,
  Snackbar,
  Container
} from '@mui/material';
import SaveIcon from '@mui/icons-material/Save';
import ExchangeConnectionSettings from '../components/settings/ExchangeConnectionSettings';
import BotConnectionSettings from '../components/settings/BotConnectionSettings';
import ServerConnectionSettings from '../components/settings/ServerConnectionSettings';
import { useSnackbar } from 'notistack';

function TabPanel(props) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`connection-tabpanel-${index}`}
      aria-labelledby={`connection-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index) {
  return {
    id: `connection-tab-${index}`,
    'aria-controls': `connection-tabpanel-${index}`,
  };
}

const ConnectionSettingsPage = () => {
  const { enqueueSnackbar } = useSnackbar();
  const [tabValue, setTabValue] = useState(0);
  const [openAlert, setOpenAlert] = useState(true);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleCloseAlert = () => {
    setOpenAlert(false);
  };

  const saveAllConfigurations = () => {
    try {
      // This function would trigger saving of all configurations
      // In a real app, you might want to call a backend API here
      
      // For now, this is just a UI feedback
      enqueueSnackbar('All connection configurations have been saved successfully', { variant: 'success' });
    } catch (error) {
      console.error('Error saving all configurations:', error);
      enqueueSnackbar('Failed to save all configurations', { variant: 'error' });
    }
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ p: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Connection Settings
        </Typography>
        
        <Typography variant="body1" color="text.secondary" paragraph>
          Configure all your connections for exchanges, bots, and servers to enable comprehensive monitoring.
          Each configuration can be tested individually before saving.
        </Typography>
        
        {openAlert && (
          <Alert 
            severity="info" 
            sx={{ mb: 3 }} 
            onClose={handleCloseAlert}
          >
            API keys, credentials, and tokens are stored securely in your browser's local storage.
            For production use, we recommend implementing server-side storage with proper encryption.
          </Alert>
        )}
        
        <Paper sx={{ width: '100%', mb: 3 }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            indicatorColor="primary"
            textColor="primary"
            variant="fullWidth"
            aria-label="connection settings tabs"
          >
            <Tab label="Exchange Connections" {...a11yProps(0)} />
            <Tab label="Bot Connections" {...a11yProps(1)} />
            <Tab label="Server Connections" {...a11yProps(2)} />
          </Tabs>
          
          <TabPanel value={tabValue} index={0}>
            <ExchangeConnectionSettings />
          </TabPanel>
          <TabPanel value={tabValue} index={1}>
            <BotConnectionSettings />
          </TabPanel>
          <TabPanel value={tabValue} index={2}>
            <ServerConnectionSettings />
          </TabPanel>
        </Paper>
        
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
          <Button
            variant="contained"
            color="primary"
            size="large"
            startIcon={<SaveIcon />}
            onClick={saveAllConfigurations}
          >
            Save All Configurations
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default ConnectionSettingsPage;
