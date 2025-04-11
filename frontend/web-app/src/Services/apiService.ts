import axios from 'axios';
import { toast } from 'react-toastify';

// Change back to main backend URL - this should match your actual backend
const BASE_URL = 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface User {
  username: string;
  name?: string;
  phoneNumber?: string;
  email?: string;
  password?: string;
}

export interface SensorData {
  id: number;
  sensorId: number;
  timestamp: string;
  value: number;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

const apiService = {
  // Auth APIs
  createUser: async (username: string, password: string): Promise<void> => {
    try {
      await api.post('/users', { username, password });
      toast.success('User created successfully');
    } catch (error) {
      toast.error('Failed to create user');
      throw error;
    }
  },

  getToken: async (username: string, password: string): Promise<TokenResponse> => {
    try {
      const response = await api.post('/token', 
        new URLSearchParams({ username, password }),
        { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
      );
      return response.data;
    } catch (error) {
      toast.error('Login failed');
      throw error;
    }
  },

  getUser: async (username: string): Promise<User> => {
    try {
      const response = await api.get(`/users?username=${username}`);
      return response.data;
    } catch (error) {
      toast.error('Failed to fetch user data');
      throw error;
    }
  },

  deleteUser: async (): Promise<void> => {
    try {
      await api.delete('/users');
      toast.success('User deleted successfully');
    } catch (error) {
      toast.error('Failed to delete user');
      throw error;
    }
  },

  // Sensor Data APIs
  getSensorData: async (sensorId: number): Promise<SensorData[]> => {
    try {
      const response = await api.get(`/sensor_data/${sensorId}`);
      return response.data;
    } catch (error) {
      toast.error('Failed to fetch sensor data');
      throw error;
    }
  },

  deleteSensorData: async (readingId: number): Promise<void> => {
    try {
      await api.delete(`/sensor_data/${readingId}`);
      toast.success('Sensor data deleted successfully');
    } catch (error) {
      toast.error('Failed to delete sensor data');
      throw error;
    }
  },
};

export default apiService; 