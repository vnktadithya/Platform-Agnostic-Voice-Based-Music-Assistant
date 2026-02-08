import { useLocation } from 'wouter';
import { useEffect } from 'react';
import Features from '../components/Features';
import { motion } from 'framer-motion';
import styles from './FeaturesPage.module.css';

export const FeaturesPage = () => {
    const [, setLocation] = useLocation();

    // Handle anchor scrolling
    useEffect(() => {
        if (window.location.hash) {
            const id = window.location.hash.replace('#', '');
            const element = document.getElementById(id);
            if (element) {
                // Small timeout to ensure rendering is complete
                setTimeout(() => {
                    element.scrollIntoView({ behavior: 'smooth' });
                }, 100);
            }
        }
    }, []);

    return (
        <main className={styles.container}>
            <Features />

            {/* Floating Back Button */}
            <motion.button
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                onClick={() => setLocation('/')}
                className={styles.backButton}

            >
                Back to Home
            </motion.button>
        </main>
    );
};
