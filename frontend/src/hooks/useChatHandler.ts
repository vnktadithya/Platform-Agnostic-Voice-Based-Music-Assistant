import { useState } from 'react';
import { useStore } from '../store/useStore';
import { useToast } from '../components/ui/Toast';
import { sendText, uploadAudio, executeAction } from '../services/api';
import { voiceClient } from '../services/VoiceClient';
import type { BackendResponse, Command, TrackInfo } from '../types';

export const useChatHandler = () => {
    const { setSamState, activePlatform, accountId } = useStore();
    const { addToast } = useToast();
    const [pendingCommand, setPendingCommand] = useState<Command | null>(null);
    const [sessionId, setSessionId] = useState<string | undefined>(undefined);

    const processText = async (text: string): Promise<BackendResponse | null> => {
        if (!text.trim() || !accountId) return null;
        setSamState('THINKING');
        try {
            const response = await sendText(text, activePlatform, accountId, sessionId);
            if (response.session_id) setSessionId(response.session_id);

            if (response.action_outcome === 'ERROR') {
                const isNotSupported = response.reply?.toLowerCase().includes("not support");
                // Use the backend's friendly reply as the toast message
                addToast(response.reply || (isNotSupported ? "Action Not Supported" : "Action failed. Check console."), 'error');
            }
            return response;
        } catch (error: any) {
            console.error(error);
            addToast(error.response?.data?.detail || "Failed to send message.", 'error');
            setSamState('IDLE');
            return null;
        }
    };

    const processVoice = async (): Promise<BackendResponse | null> => {
        try {
            const audioBlob = await voiceClient.stopRecording();
            const response = await uploadAudio(audioBlob, activePlatform, accountId || 1, sessionId);
            if (response.session_id) setSessionId(response.session_id);

            if (response.action_outcome === 'ERROR') {
                const isNotSupported = response.reply?.toLowerCase().includes("not support");
                // Use the backend's friendly reply as the toast message
                addToast(response.reply || (isNotSupported ? "Action Not Supported" : "Action failed. Check console."), 'error');
            }
            return response;
        } catch (error: any) {
            console.error(error);
            addToast(error.response?.data?.detail || "Failed to process voice.", 'error');
            setSamState('IDLE');
            return null;
        }
    };

    const handleBackendResponse = (response: BackendResponse) => {
        let trackInfo: TrackInfo | null = null;
        let command: Command | null = null;

        if (response) {
            // Extract Track Info (Immediate UI update)
            if (response.action_data && Array.isArray(response.action_data)) {
                // eslint-disable-next-line @typescript-eslint/no-explicit-any
                const trackAction = response.action_data.find((res: any) => res && res.track_info);
                if (trackAction && trackAction.track_info) trackInfo = trackAction.track_info;
            }

            // Extract Deferred Command (Sequencing)
            if (response.command && response.command.timing === 'AFTER_TTS') {
                command = response.command;
                setPendingCommand(command);
            }
        }

        return { trackInfo, command };
    };

    const executePendingCommand = async () => {
        if (pendingCommand) {
            console.log("Executing deferred command:", pendingCommand);
            try {
                await executeAction(pendingCommand, activePlatform, accountId || 1, sessionId);
            } catch (err: any) {
                console.error("Action Failed:", err);
                const errMsg = err.response?.data?.detail || "Action failed.";
                addToast(errMsg, 'error');
            }
            setPendingCommand(null);
        }
    };

    return {
        processText,
        processVoice,
        handleBackendResponse,
        executePendingCommand,
        pendingCommand,
        setPendingCommand
    };
};
