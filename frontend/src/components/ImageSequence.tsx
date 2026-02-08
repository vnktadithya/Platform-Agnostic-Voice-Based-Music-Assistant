import { useEffect, useRef, useState } from 'react';
import styles from './ImageSequence.module.css';

// Global cache to prevent reloading images on navigation
const globalImageCache: HTMLImageElement[] = [];

/**
 * Renders a high-performance image sequence using an HTML5 Canvas.
 * Optimized for full-screen background loops.
 */
interface ImageSequenceProps {
    onCycleComplete?: () => void;
    instantStart?: boolean;
}

export const ImageSequence = ({ onCycleComplete, instantStart = false }: ImageSequenceProps) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [images, setImages] = useState<HTMLImageElement[]>([]);
    const [isLoaded, setIsLoaded] = useState(false);
    const requestRef = useRef<number | undefined>(undefined);
    // Configuration
    const TOTAL_FRAMES = 192;
    const FPS = 24; // Cinematic 24fps
    const FRAME_INTERVAL = 1000 / FPS;
    const SEQUENCE_PATH = '/landing_page_sequence/ezgif-frame-';

    const frameIndexRef = useRef(0);
    const lastFrameTimeRef = useRef(0);

    // 1. Preload Images
    useEffect(() => {
        // If images are already cached, use them immediately
        if (globalImageCache.length === TOTAL_FRAMES) {
            setImages(globalImageCache);
            setIsLoaded(true);
            return;
        }

        let loadedCount = 0;
        const loadedImages: HTMLImageElement[] = [];

        // Helper to pad numbers
        const pad = (num: number) => num.toString().padStart(3, '0');

        for (let i = 1; i <= TOTAL_FRAMES; i++) {
            const img = new Image();
            img.src = `${SEQUENCE_PATH}${pad(i)}.png`;
            img.onload = () => {
                loadedCount++;
                if (loadedCount === TOTAL_FRAMES) {
                    // Populate global cache
                    loadedImages.forEach((img, index) => {
                        globalImageCache[index] = img;
                    });
                    setImages(loadedImages);
                    setIsLoaded(true);
                }
            };
            img.onerror = () => {
                // Handle missing frames
                loadedCount++;
                if (loadedCount === TOTAL_FRAMES) {
                    loadedImages.forEach((img, index) => {
                        globalImageCache[index] = img;
                    });
                    setImages(loadedImages);
                    setIsLoaded(true);
                }
            };
            loadedImages[i - 1] = img; // maintain order
        }
    }, []);

    // State for ping-pong loop
    const directionRef = useRef(1); // 1 = forward, -1 = backward
    const isPausedRef = useRef(true); // Start PAUSED for the initial 500 ms delay

    // 2. Playback Loop
    useEffect(() => {
        if (!isLoaded || !canvasRef.current || images.length === 0) return;

        // 2s DELAY: Start animation 500 ms after page load (if instantStart is true)
        const delay = instantStart ? 0 : 500;

        const startTimeout = setTimeout(() => {
            isPausedRef.current = false;
        }, delay);

        const animate = (timestamp: number) => {
            if (!lastFrameTimeRef.current) lastFrameTimeRef.current = timestamp;
            const elapsed = timestamp - lastFrameTimeRef.current;

            if (elapsed > FRAME_INTERVAL) {

                if (!isPausedRef.current) {
                    // Update direction & Handle Pauses
                    if (frameIndexRef.current >= TOTAL_FRAMES - 1 && directionRef.current === 1) {
                        // Fully Dispersed -> Pause 1s -> Reverse
                        directionRef.current = -1;
                        isPausedRef.current = true;
                        if (onCycleComplete) onCycleComplete();
                        setTimeout(() => { isPausedRef.current = false; }, 1000);

                    } else if (frameIndexRef.current <= 0 && directionRef.current === -1) {
                        // Fully Reassembled -> Pause 200ms -> Forward
                        directionRef.current = 1;
                        isPausedRef.current = true;
                        setTimeout(() => { isPausedRef.current = false; }, 200);
                    }

                    // Determine next frame
                    if (!isPausedRef.current) {
                        frameIndexRef.current = frameIndexRef.current + directionRef.current;
                    }
                }

                // Safety clamp
                if (frameIndexRef.current < 0) frameIndexRef.current = 0;
                if (frameIndexRef.current >= TOTAL_FRAMES) frameIndexRef.current = TOTAL_FRAMES - 1;

                const img = images[frameIndexRef.current];

                const canvas = canvasRef.current!;
                const ctx = canvas.getContext('2d');

                if (ctx && img) {
                    // High DPI
                    const dpr = window.devicePixelRatio || 1;
                    if (canvas.width !== window.innerWidth * dpr) {
                        canvas.width = window.innerWidth * dpr;
                        canvas.height = window.innerHeight * dpr;
                        ctx.scale(dpr, dpr);
                    }

                    // Maximimize Quality
                    ctx.imageSmoothingEnabled = true;
                    ctx.imageSmoothingQuality = 'high';

                    const canvasWidth = canvas.width / dpr;
                    const canvasHeight = canvas.height / dpr;
                    const canvasRatio = canvasWidth / canvasHeight;
                    const imgRatio = img.width / img.height;

                    let drawWidth, drawHeight, offsetX, offsetY;

                    // Logic: CONTAIN (Fit entirely inside to ensure full visibility)
                    // We calculate aspect ratios to fit the image without cropping
                    if (canvasRatio > imgRatio) {
                        // Canvas is wider than image -> Fit Height
                        drawHeight = canvasHeight;
                        drawWidth = canvasHeight * imgRatio;
                        offsetX = (canvasWidth - drawWidth) / 2;
                        offsetY = 0;
                    } else {
                        // Canvas is taller than image -> Fit Width
                        drawWidth = canvasWidth;
                        drawHeight = canvasWidth / imgRatio;
                        offsetX = 0;
                        offsetY = (canvasHeight - drawHeight) / 2;
                    }

                    // Clear canvas
                    ctx.clearRect(0, 0, canvasWidth, canvasHeight);
                    ctx.drawImage(img, offsetX, offsetY, drawWidth, drawHeight);
                }

                lastFrameTimeRef.current = timestamp - (elapsed % FRAME_INTERVAL);
            }

            if (!document.hidden) {
                requestRef.current = requestAnimationFrame(animate);
            }
        };

        const handleVisibilityChange = () => {
            if (document.hidden) {
                if (requestRef.current) cancelAnimationFrame(requestRef.current);
            } else {
                lastFrameTimeRef.current = 0;
                requestRef.current = requestAnimationFrame(animate);
            }
        };

        document.addEventListener('visibilitychange', handleVisibilityChange);
        requestRef.current = requestAnimationFrame(animate);

        return () => {
            clearTimeout(startTimeout);
            if (requestRef.current) cancelAnimationFrame(requestRef.current);
            document.removeEventListener('visibilitychange', handleVisibilityChange);
        };
    }, [isLoaded, images]);

    // 3. Resize Handler
    useEffect(() => {
        const handleResize = () => {
            // Let the loop handle the resize logic
        };
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    return (
        <div className={styles.container}>
            <canvas
                ref={canvasRef}
                className={styles.canvas}
            />
            {/* VIGNETTE OVERLAY */}
            <div className={styles.vignette} />
        </div>
    );
};
