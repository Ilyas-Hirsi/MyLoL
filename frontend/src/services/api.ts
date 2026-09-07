import axios, { AxiosResponse } from 'axios';
import {
  User,
  UserLogin,
  AuthResponse,
  Match,
  ChampionRecommendation,
  ChampionStats,
  DifficultMatchup,
  MatchupStats,
  MatchupDetails,
} from '../types';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject({
      message: error.response?.data?.detail || error.message || 'An error occurred',
      status: error.response?.status || 500,
      details: error.response?.data,
    });
  }
);

const apiService = {
  // Authentication endpoints
  // Registration removed; login auto-creates users

  async login(credentials: UserLogin): Promise<AuthResponse> {
    const response: AxiosResponse<AuthResponse> = await api.post('/auth/login', credentials);
    return response.data;
  },

  // User endpoints
  async getUserProfile(): Promise<User> {
    const response: AxiosResponse<User> = await api.get('/users/profile');
    return response.data;
  },

  async getMatchHistory(): Promise<Match[]> {
    const response: AxiosResponse<Match[]> = await api.get('/users/match-history');
    return response.data;
  },

  async getDifficultMatchups(role?: string, game_mode?: string): Promise<DifficultMatchup[]> {
    const response: AxiosResponse<any> = await api.get('/matchups/difficult', { params: { role, game_mode } });
    // Extract the actual matchups array from the response
    return response.data.difficult_matchups || response.data || [];
  },

  async getDifficultMatchupsFull(role?: string, game_mode?: string): Promise<any> {
    const response: AxiosResponse<any> = await api.get('/matchups/difficult', { params: { role, game_mode } });
    return response.data;
  },

  async getChampionRecommendations(role?: string, game_mode?: string): Promise<ChampionRecommendation[]> {
    const response: AxiosResponse<any> = await api.get('/champions/recommendations', { params: { role, game_mode } });
    // Extract the actual recommendations array from the response
    return response.data.recommendations || response.data || [];
  },

  async getChampionCounters(champion: string): Promise<ChampionStats[]> {
    const response: AxiosResponse<ChampionStats[]> = await api.get(`/champions/counters/${champion}`);
    return response.data;
  },

  async getChampionStats(champion: string): Promise<ChampionStats> {
    const response: AxiosResponse<ChampionStats> = await api.get(`/champions/stats/${champion}`);
    return response.data;
  },

  async getChampionMatchupData(champion1: string, champion2: string): Promise<MatchupStats> {
    const response: AxiosResponse<MatchupStats> = await api.get(`/matchups/vs/${champion1}/${champion2}`);
    return response.data;
  },

  async getMatchupDetails(opponent: string, role?: string, game_mode?: string): Promise<MatchupDetails> {
    const params: Record<string, string> = {};
    if (role) params.role = role;
    if (game_mode) params.game_mode = game_mode;
    const response: AxiosResponse<MatchupDetails> = await api.get(`/matchups/details/${encodeURIComponent(opponent)}`, { params });
    return response.data;
  },

  async refreshUserData(): Promise<{ message: string }> {
    const response: AxiosResponse<{ message: string }> = await api.post('/users/refresh-data');
    return response.data;
  },

  async healthCheck(): Promise<{ status: string; database: string }> {
    const response: AxiosResponse<{ status: string; database: string }> = await api.get('/health');
    return response.data;
  },
};

export default apiService;