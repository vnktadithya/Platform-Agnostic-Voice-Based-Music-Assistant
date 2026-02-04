export { };

declare global {
    interface Window {
        SC: {
            Widget: (element: HTMLIFrameElement | string) => any;
        };
        audioInterval?: number; // Used in fallback logic
        webkitAudioContext?: typeof AudioContext;
    }
}
