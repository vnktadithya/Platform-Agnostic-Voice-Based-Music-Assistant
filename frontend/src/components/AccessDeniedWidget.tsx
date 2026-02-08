import { motion, AnimatePresence } from 'framer-motion';
import styles from './AccessDeniedWidget.module.css';

interface AccessDeniedWidgetProps {
    isOpen: boolean;
    onClose: () => void;
}

export const AccessDeniedWidget = ({ isOpen, onClose }: AccessDeniedWidgetProps) => {
    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className={styles.overlay}
                >
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0.9, opacity: 0 }}
                        transition={{ type: "spring", duration: 0.5 }}
                        className={styles.modal}
                    >
                        <div className={styles.icon}>⛔</div>
                        <h2 className={styles.title}>
                            Access Restricted
                        </h2>
                        <p className={styles.message}>
                            This application is currently in <strong>Development Mode</strong>.
                            Your Spotify account is not whitelisted in the developer dashboard.
                        </p>
                        <div className={styles.infoBox}>
                            <p className={styles.infoText}>
                                Please request the application owner to add your email address to the authorized users list.
                            </p>
                        </div>

                        <button
                            onClick={onClose}
                            className={styles.closeButton}
                        >
                            Close
                        </button>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};
