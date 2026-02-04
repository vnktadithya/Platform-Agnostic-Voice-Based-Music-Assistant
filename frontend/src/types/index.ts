export interface TrackInfo {
    title: string;
    subtitle: string;
    type: 'song' | 'playlist';
    image?: string;
    permalink_url?: string;
}

export interface Command {
    type: string;
    params: Record<string, any>;
    timing?: 'IMMEDIATE' | 'AFTER_TTS';
}

export interface BackendResponse {
    session_id?: string;
    action_outcome: 'SUCCESS' | 'ERROR' | 'NEUTRAL';
    reply: string;
    audio_base64?: string; // Explicitly add audio_base64
    action_data?: Array<{
        track_info?: TrackInfo;
        [key: string]: any;
    }>;
    platform?: string; // Add platform if used in response
    command?: Command;
    [key: string]: any; // Keep loose typing for safety but minimize usage
}

export interface PlatformStatus {
    is_connected: boolean;
    has_active_device?: boolean;
    device?: any;
    reason?: string;
    account_id?: number;
    user_id?: string;
}
