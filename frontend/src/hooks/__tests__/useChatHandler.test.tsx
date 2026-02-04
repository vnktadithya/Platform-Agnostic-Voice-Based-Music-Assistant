// @vitest-environment jsdom
import { renderHook, act } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { useChatHandler } from '../useChatHandler';
import { sendText, uploadAudio, executeAction } from '../../services/api';
import { voiceClient } from '../../services/VoiceClient';
import { useStore } from '../../store/useStore';
import { useToast } from '../../components/ui/Toast';

// --- MOCKS ---
vi.mock('../../services/api', () => ({
    sendText: vi.fn(),
    uploadAudio: vi.fn(),
    executeAction: vi.fn(),
}));

vi.mock('../../services/VoiceClient', () => ({
    voiceClient: {
        stopRecording: vi.fn(),
    },
}));

vi.mock('../../store/useStore', () => ({
    useStore: vi.fn(),
}));

vi.mock('../../components/ui/Toast', () => ({
    useToast: vi.fn(),
}));

describe('useChatHandler', () => {
    // Mock State Helpers
    const setSamStateMock = vi.fn();
    const addToastMock = vi.fn();

    beforeEach(() => {
        vi.clearAllMocks();

        // Default Store Mock
        (useStore as any).mockReturnValue({
            samState: 'IDLE',
            setSamState: setSamStateMock,
            activePlatform: 'spotify',
            accountId: 123,
        });

        // Default Toast Mock
        (useToast as any).mockReturnValue({
            addToast: addToastMock,
        });
    });

    it('should process text input correctly', async () => {
        const mockResponse = { reply: 'Hello there', action_outcome: 'SUCCESS' };
        (sendText as any).mockResolvedValue(mockResponse);

        const { result } = renderHook(() => useChatHandler());

        let response;
        await act(async () => {
            response = await result.current.processText('Hello');
        });

        expect(setSamStateMock).toHaveBeenCalledWith('THINKING');
        expect(sendText).toHaveBeenCalledWith('Hello', 'spotify', 123);
        expect(response).toEqual(mockResponse);
    });

    it('should handle text input errors gracefully', async () => {
        (sendText as any).mockRejectedValue(new Error('API Fail'));

        const { result } = renderHook(() => useChatHandler());

        await act(async () => {
            await result.current.processText('Hello');
        });

        expect(addToastMock).toHaveBeenCalledWith('Failed to send message.', 'error');
        expect(setSamStateMock).toHaveBeenCalledWith('IDLE');
    });

    it('should process voice input correctly', async () => {
        const mockBlob = new Blob(['audio'], { type: 'audio/wav' });
        (voiceClient.stopRecording as any).mockResolvedValue(mockBlob);

        const mockResponse = { reply: 'Voice processed', action_outcome: 'SUCCESS' };
        (uploadAudio as any).mockResolvedValue(mockResponse);

        const { result } = renderHook(() => useChatHandler());

        let response;
        await act(async () => {
            response = await result.current.processVoice();
        });

        expect(voiceClient.stopRecording).toHaveBeenCalled();
        expect(uploadAudio).toHaveBeenCalledWith(mockBlob, 'spotify', 123);
        expect(response).toEqual(mockResponse);
    });

    it('should handle deferred commands in response', () => {
        const { result } = renderHook(() => useChatHandler());

        const mockBackendResponse = {
            reply: "Sure",
            command: { type: "play", timing: "AFTER_TTS" }
        };

        let processed: any;
        act(() => {
            processed = result.current.handleBackendResponse(mockBackendResponse);
        });

        expect(processed?.command).toEqual(mockBackendResponse.command);
        expect(result.current.pendingCommand).toEqual(mockBackendResponse.command);
    });

    it('should execute deferred command', async () => {
        const { result } = renderHook(() => useChatHandler());
        const mockCommand = { type: "play", timing: "AFTER_TTS" };

        // Manually set pending command state (simulating handleBackendResponse)
        act(() => {
            result.current.setPendingCommand(mockCommand);
        });

        await act(async () => {
            await result.current.executePendingCommand();
        });

        expect(executeAction).toHaveBeenCalledWith(mockCommand, 'spotify', 123);
        expect(result.current.pendingCommand).toBeNull();
    });
});
