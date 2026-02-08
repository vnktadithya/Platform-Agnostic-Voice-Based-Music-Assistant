import { motion, AnimatePresence } from 'framer-motion';
import styles from './Overlay.module.css';

// Warning Message Component (Top Left)
export const DeviceWarning = ({ show }: { show: boolean }) => (
    <AnimatePresence>
        {show && (
            <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.5 }}
                className={styles.deviceWarning}
            >
                <div className={styles.warningDot} />
                <span className={styles.warningText}>
                    No active Spotify device found. <br />
                    Please open Spotify on any device to continue.
                </span>
            </motion.div >
        )}
    </AnimatePresence >
);
