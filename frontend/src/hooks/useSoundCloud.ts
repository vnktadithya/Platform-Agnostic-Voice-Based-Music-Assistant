import { useEffect, useRef } from 'react';

export const useSoundCloud = (activePlatform: string, scTrackUrl: string | null) => {
    const scWidgetRef = useRef<any>(null);

    useEffect(() => {
        if (!window.SC) {
            const script = document.createElement('script');
            script.src = "https://w.soundcloud.com/player/api.js";
            script.async = true;
            document.body.appendChild(script);
        }
    }, []);

    useEffect(() => {
        if (activePlatform === 'soundcloud' && scTrackUrl) {
            const iframe = document.getElementById('sc-widget') as HTMLIFrameElement;
            if (iframe && window.SC) {
                const widget = window.SC.Widget(iframe);
                scWidgetRef.current = widget;
                console.log("SC Widget Bound");
            }
        }
    }, [activePlatform, scTrackUrl]);

    const setVolume = (volume: number) => {
        if (scWidgetRef.current) {
            scWidgetRef.current.setVolume(volume);
        }
    };

    const getVolume = (): Promise<number> => {
        return new Promise((resolve) => {
            if (scWidgetRef.current) {
                const timeoutId = setTimeout(() => {
                    resolve(100);
                }, 200);

                scWidgetRef.current.getVolume((vol: number) => {
                    clearTimeout(timeoutId);
                    resolve(vol);
                });
            } else {
                resolve(100); // Default if widget not ready
            }
        });
    };

    return { scWidgetRef, setVolume, getVolume };
};
