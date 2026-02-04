import { create } from 'zustand';
import { persist } from 'zustand/middleware';

type SamState = 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING';

interface AppState {
    samState: SamState;
    setSamState: (state: SamState) => void;
    audioLevel: number; // 0.0 to 1.0 (for reactivity)
    setAudioLevel: (level: number) => void;

    // Auth Persistence
    activePlatform: string;
    setActivePlatform: (platform: string) => void;
    accountId: number | null;
    setAccountId: (id: number) => void;

    // UI Session State (Resets on reload)
    introSeen: boolean;
    setIntroSeen: (seen: boolean) => void;
}

export const useStore = create<AppState>()(
    persist(
        (set) => ({
            samState: 'IDLE',
            setSamState: (state) => set({ samState: state }),
            audioLevel: 0,
            setAudioLevel: (level) => set({ audioLevel: level }),

            activePlatform: 'spotify', // Default
            setActivePlatform: (platform) => set({ activePlatform: platform }),
            accountId: null,
            setAccountId: (id) => set({ accountId: id }),

            introSeen: false,
            setIntroSeen: (seen) => set({ introSeen: seen }),
        }),
        {
            name: 'sam-storage',
            partialize: (state) => ({ activePlatform: state.activePlatform, accountId: state.accountId }),
        }
    )
);
