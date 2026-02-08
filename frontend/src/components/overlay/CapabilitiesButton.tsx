import { motion } from 'framer-motion';
import { useLocation } from 'wouter';
import styles from './Overlay.module.css';
import { PLATFORMS } from '../canvas/PlatformOrbit';

interface CapabilitiesButtonProps {
    activePlatform: string;
    theme: { color: string; label?: string } | undefined;
}

export const CapabilitiesButton = ({ activePlatform, theme }: CapabilitiesButtonProps) => {
    const [, setLocation] = useLocation();

    return (
        <motion.button
            initial={{ opacity: 0, y: 20 }}
            animate={{
                opacity: 1,
                y: 0,
                boxShadow: `0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px ${theme?.color}30, 0 0 15px ${theme?.color}20`
            }}
            transition={{
                opacity: { duration: 0.8, delay: 0.5 },
                y: { type: "spring", stiffness: 50 },
                boxShadow: { duration: 0.5 }
            }}
            whileHover={{
                y: -3,
                scale: 1.02,
                boxShadow: `0 20px 60px rgba(0,0,0,0.6), 0 0 0 2px ${theme?.color}60, 0 0 80px ${theme?.color}50`,
                background: 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(0,0,0,0.4) 100%)'
            }}
            whileTap={{ scale: 0.98, y: 1 }}
            aria-label={`View ${PLATFORMS.find(p => p.id === activePlatform)?.name || activePlatform} Capabilities`}
            onClick={() => setLocation('/features#platform-intelligence')}
            className={`${styles.capabilitiesButton} ${styles.capabilitiesButtonWithBorder}`}
            style={{
                /* Border Lighting (Top highlight, Bottom shadow) */
                borderTop: `1px solid ${theme?.color}40`,
            }}
        >
            <span>View {PLATFORMS.find(p => p.id === activePlatform)?.name || activePlatform} Capabilities</span>
        </motion.button>
    );
};
