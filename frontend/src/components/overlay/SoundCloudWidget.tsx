import { motion } from 'framer-motion';
import styles from './Overlay.module.css';

interface SoundCloudWidgetProps {
    trackUrl: string | null;
    onClose: () => void;
}

export const SoundCloudWidget = ({ trackUrl, onClose }: SoundCloudWidgetProps) => {
    if (!trackUrl) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 50 }}
            transition={{ duration: 0.5 }}
            className={styles.soundCloudWidget}
        // All styles moved to CSS class
        >
            <button
                onClick={onClose}
                aria-label="Close Music Widget"
                className={styles.closeButton}
            >
                &times;
            </button>
            <iframe
                id="sc-widget"
                className={styles.widgetFrame}
                src={`https://w.soundcloud.com/player/?url=${encodeURIComponent(trackUrl)}&color=%23ff5500&auto_play=true&hide_related=false&show_comments=false&show_user=true&show_reposts=false&show_teaser=true&visual=true`}
                allow="autoplay"
                scrolling="no"
                frameBorder="no"
            ></iframe>
        </motion.div >
    );
};
