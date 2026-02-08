import { motion } from 'framer-motion';
import styles from './Overlay.module.css';

export const GhostMessage = ({ message }: { message: string }) => (
    <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 0.6, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.8 }}
        className={styles.ghostMessage}
    >
        {message}
    </motion.div>
);
