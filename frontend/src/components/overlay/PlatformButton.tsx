import { motion } from 'framer-motion';
import { useLocation } from 'wouter';
import styles from './Overlay.module.css';

export const PlatformButton = () => {
    const [, setLocation] = useLocation();

    return (
        <motion.button
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            aria-label="Change Platform"
            onClick={() => setLocation('/platform-select')}
            className={styles.platformButton}

        // Mouse events handled by CSS :hover
        >
            Change Platform
        </motion.button>
    );
};
