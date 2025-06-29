import { atom } from 'recoil';

// Get initial values from localStorage if available
const getInitialApiUrl = () => {
  try {
    return localStorage.getItem('apiUrl') || '';
  } catch {
    return '';
  }
};

const getInitialApiKey = () => {
  try {
    return localStorage.getItem('apiKey') || '';
  } catch {
    return '';
  }
};

const getInitialRefreshInterval = () => {
  try {
    return parseInt(localStorage.getItem('refreshInterval')) || 60000;
  } catch {
    return 60000;
  }
};

// Settings state atom
export const settingsState = atom({
  key: 'settingsState',
  default: {
    apiUrl: getInitialApiUrl(),
    apiKey: getInitialApiKey(),
    refreshInterval: getInitialRefreshInterval(),
    notificationsEnabled: true,
    darkMode: false,
    autoRefresh: true
  },
});
