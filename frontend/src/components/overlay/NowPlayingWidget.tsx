import { motion } from 'framer-motion';
import styles from './Overlay.module.css';

// Animated Waveform Component
const Waveform = () => (
    <div className={styles.waveform}>
        {[1, 2, 3, 4].map((i) => (
            <motion.div
                key={i}
                animate={{ height: [4, 12, 6, 14, 4] }}
                transition={{
                    duration: 0.8,
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: i * 0.1
                }}
                className={styles.waveformBar}
            />
        ))}
    </div>
);

interface NowPlayingWidgetProps {
    data: {
        title: string;
        subtitle: string;
        image?: string;
        type: 'song' | 'playlist';
    };
}

export const NowPlayingWidget = ({ data }: NowPlayingWidgetProps) => {
    return (
        <motion.div
            initial={{ opacity: 0, x: 20, filter: 'blur(10px)' }}
            animate={{ opacity: 1, x: 0, filter: 'blur(0px)' }}
            exit={{ opacity: 0, x: 20, filter: 'blur(10px)' }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className={styles.nowPlayingWidget}
        >
            {/* Album Art / Icon */}
            <div className={styles.albumArtContainer}>
                <div className={styles.albumArt}>
                    {data.image ? (
                        <img
                            src={data.image}
                            alt="Art"
                            className={styles.albumArtImage}
                        />
                    ) : (
                        <>
                            {data.type === 'song' ? (
                                <div className={styles.albumArtFallback} />
                            ) : (
                                <div className={styles.playlistFallback}>
                                    <svg className={styles.playlistIcon} viewBox="0 0 24 24" fill="white" stroke="none">
                                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 14H9v-2h2v2zm1-5c-.77 0-1.47.3-2.03.79l-1.35-1.54C9.5 9.4 10.66 9 12 9c2.21 0 4 1.79 4 4 0 .88-.36 1.68-.93 2.25L13.83 17h-1.66l1.24-1.24c.3-.29.59-.62.59-1.01 0-1.1-.9-2-2-2z" />
                                        <path d="M9 16h6v-6h4V8h-4V6h-2v10z" fill="white" />
                                    </svg>
                                </div>
                            )}
                        </>
                    )}
                </div>
                {/* Beat Glow */}
                <motion.div
                    animate={{ opacity: [0.3, 0.6, 0.3], scale: [1, 1.05, 1] }}
                    transition={{ duration: 0.8, repeat: Infinity }}
                    className={styles.beatGlow}
                />
            </div>

            {/* Info */}
            <div className={styles.trackInfo}>
                <div className={styles.trackTitle}>
                    {data.title}
                </div>
                <div className={styles.trackSubtitleContainer}>
                    <div className={styles.trackSubtitle}>
                        {data.subtitle}
                    </div>
                    {data.type === 'song' && <Waveform />}
                </div>
            </div>
        </motion.div>
    );
};
