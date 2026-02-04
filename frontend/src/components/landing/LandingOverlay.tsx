import { motion } from 'framer-motion';
import { useLocation } from 'wouter';

interface LandingOverlayProps {
    showButton?: boolean;
}

export const LandingOverlay = ({ showButton = false }: LandingOverlayProps) => {
    const [, setLocation] = useLocation();

    return (
        <div style={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            pointerEvents: 'none', // Allow clicks to pass through main area if needed, but buttons need pointer-events-auto
            zIndex: 10
        }}>


            {/* Main Content */}
            <div style={{
                textAlign: 'center',
                pointerEvents: 'auto', // Re-enable pointer events for text/buttons
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '2rem'
            }}>
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 1, ease: "easeOut" }}
                >
                    <h1 style={{
                        fontSize: '5rem',
                        fontWeight: 700,
                        margin: 0,
                        letterSpacing: '-0.02em',
                        color: 'rgba(255, 255, 255, 0.95)',
                        lineHeight: 1
                    }}>

                    </h1>
                    <p style={{
                        fontSize: '1.5rem',
                        fontWeight: 400,
                        marginTop: '1rem',
                        color: 'rgba(255, 255, 255, 0.7)',
                        letterSpacing: '0.05em'
                    }}>

                    </p>
                </motion.div>

            </div>

            {showButton && (

                <>
                    {/* Learn More - Top Right */}
                    <motion.button
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.8 }}
                        onClick={() => setLocation('/features')}
                        style={{
                            position: 'absolute',
                            top: '2.5rem',
                            right: '2.5rem',
                            padding: '1rem 2rem',
                            fontSize: '0.9rem',
                            fontWeight: 500,
                            backgroundColor: 'rgba(255, 255, 255, 0.1)',
                            backdropFilter: 'blur(10px)',
                            color: 'white',
                            border: '1px solid rgba(255, 255, 255, 0.2)',
                            borderRadius: '9999px',
                            cursor: 'pointer',
                            pointerEvents: 'auto',
                            transition: 'all 0.2s ease',
                            zIndex: 20
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.2)';
                            e.currentTarget.style.transform = 'translateY(2px)';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                            e.currentTarget.style.transform = 'translateY(0)';
                        }}
                    >
                        Learn More
                    </motion.button>

                    {/* Get Started - Bottom Right */}
                    <motion.button
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.8, delay: 0.1 }}
                        onClick={() => setLocation('/platform-select')}
                        style={{
                            position: 'absolute',
                            bottom: '2.5rem',
                            right: '2.5rem',
                            padding: '1rem 2.5rem',
                            fontSize: '1rem',
                            fontWeight: 500,
                            backgroundColor: 'white',
                            color: 'black',
                            border: 'none',
                            borderRadius: '9999px',
                            cursor: 'pointer',
                            pointerEvents: 'auto',
                            transition: 'transform 0.2s ease, opacity 0.2s ease',
                            zIndex: 20
                        }}
                        onMouseEnter={(e) => {
                            e.currentTarget.style.transform = 'scale(1.05)';
                            e.currentTarget.style.opacity = '0.9';
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.transform = 'scale(1)';
                            e.currentTarget.style.opacity = '1';
                        }}
                    >
                        Get Started
                    </motion.button>
                </>
            )}

        </div>
    );
};
