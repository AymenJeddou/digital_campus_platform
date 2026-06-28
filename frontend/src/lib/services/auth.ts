import api from '../api';

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginRequest {
  username: string; // The backend uses OAuth2PasswordRequestForm which expects "username" instead of "email"
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export const authService = {
  register: async (data: RegisterRequest) => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  login: async (data: LoginRequest) => {
    // Backend expects x-www-form-urlencoded
    const formData = new URLSearchParams();
    formData.append('username', data.username);
    formData.append('password', data.password);

    const response = await api.post<AuthResponse>('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },

  verifyEmail: async (token: string) => {
    const response = await api.post('/auth/verify', { token });
    return response.data;
  },
};
