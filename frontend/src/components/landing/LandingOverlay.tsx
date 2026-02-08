import { motion } from 'framer-motion';
import { useLocation } from 'wouter';
import styles from './Landing.module.css';

interface LandingOverlayProps {
    showButton?: boolean;
}

export const LandingOverlay = ({ showButton = false }: LandingOverlayProps) => {
    const [, setLocation] = useLocation();

    return (
        <div className={styles.overlayContainer}>


            {showButton && (
                <>
                    {/* Learn More - Top Right */}
                    <motion.button
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.8 }}
                        onClick={() => setLocation('/features')}
                        className={styles.learnMoreButton}
                    >
                        Learn More
                    </motion.button>

                    {/* Get Started - Bottom Right */}
                    <motion.button
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.8, delay: 0.1 }}
                        onClick={() => setLocation('/platform-select')}
                        className={styles.getStartedButton}
                    >
                        Get Started
                    </motion.button>
                </>
            )}
        </div>
    );
};
