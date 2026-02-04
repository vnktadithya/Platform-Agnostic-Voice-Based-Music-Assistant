import { useLocation } from 'wouter';
import { useEffect } from 'react';
import Features from '../components/Features';
import { motion } from 'framer-motion';

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
        <main style={{ backgroundColor: '#050505', minHeight: '100vh', position: 'relative' }}>
            <Features />

            {/* Floating Back Button */}
            <motion.button
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                onClick={() => setLocation('/')}
                style={{
                    position: 'fixed',
                    top: '2rem',
                    left: '2rem',
                    padding: '0.75rem 1.5rem',
                    fontSize: '0.9rem',
                    fontWeight: 500,
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    backdropFilter: 'blur(10px)',
                    color: 'white',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    borderRadius: '9999px',
                    cursor: 'pointer',
                    zIndex: 50,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    transition: 'all 0.2s ease'
                }}
                onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
                    e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                    e.currentTarget.style.transform = 'translateY(0)';
                }}
            >
                Back to Home
            </motion.button>
        </main>
    );
};
