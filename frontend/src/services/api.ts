import axios from 'axios';

// Use environment variable for API URL or fallback to localhost
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/v1';

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
    withCredentials: true,
});

// Interceptor for Auth Expiry (401)
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response && error.response.status === 401) {
            console.warn("Authentication expired. Redirecting to login...");
            // Force redirect to platform selection
            window.location.href = '/platform-select?expired=true';
        }
        return Promise.reject(error);
    }
);

// Add response interceptor for global error handling/logging
api.interceptors.response.use(
    (response) => response,
    (error) => {
        console.error('API Error:', error.response?.data || error.message);
        return Promise.reject(error);
    }
);

import type { BackendResponse, Command, PlatformStatus } from '../types';

// ... (existing axios setup)

// Audio Upload
export const uploadAudio = async (audioBlob: Blob, platform: string, accountId: number, sessionId?: string): Promise<BackendResponse> => {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.wav');

    // Dynamic params
    let url = `/chat/process_voice?platform=${platform}&platform_account_id=${accountId}`;
    if (sessionId) {
        url += `&session_id=${sessionId}`;
    }

    const response = await api.post<BackendResponse>(url, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
};

// Text Chat
export const sendText = async (text: string, platform: string, accountId: number, sessionId?: string): Promise<BackendResponse> => {
    const response = await api.post<BackendResponse>(`/chat/process_text?platform=${platform}`, {
        text: text,
        platform_account_id: accountId,
        session_id: sessionId
    });
    return response.data;
};

// Trigger Action (Client-Side Sequencing)
export const executeAction = async (command: Command | { type: string, params: any }, platform: string, accountId: number, sessionId?: string): Promise<BackendResponse> => {
    const response = await api.post<BackendResponse>(`/chat/execute`, {
        action: command.type,
        parameters: command.params,
        platform: platform,
        platform_account_id: accountId,
        session_id: sessionId
    });
    return response.data;
};

// Auth
export const getAuthUrl = async (platform: string): Promise<string> => {
    const response = await api.get<{ auth_url: string }>(`/adapter/${platform}/login`);
    return response.data.auth_url;
};

// Status Check
export const getPlatformStatus = async (platform: string, accountId?: number): Promise<PlatformStatus> => {
    let url = `/adapter/${platform}/status`;
    if (accountId) {
        url += `?platform_account_id=${accountId}`;
    }
    const response = await api.get<PlatformStatus>(url);
    return response.data;
};

// Streaming TTS (Direct Audio Blob)
export const synthesizeSpeechStream = async (text: string) => {
    const response = await api.post(`/voice/tts/stream?text=${encodeURIComponent(text)}`, {}, {
        responseType: 'blob' // Important: Expect binary data
    });
    return response.data; // Returns Blob
};
