import { motion, AnimatePresence } from 'framer-motion';

// Warning Message Component (Top Left)
export const DeviceWarning = ({ show }: { show: boolean }) => (
    <AnimatePresence>
        {show && (
            <motion.div
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.5 }}
                style={{
                    position: 'absolute',
                    top: '100px',
                    left: '30px',
                    zIndex: 50,
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                    background: 'rgba(239, 68, 68, 0.1)', // Red tint for warning
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    padding: '10px 16px',
                    borderRadius: '12px',
                    backdropFilter: 'blur(8px)',
                    boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
                }}
            >
                <div style={{
                    width: '8px', height: '8px', borderRadius: '50%',
                    background: '#ef4444', boxShadow: '0 0 8px #ef4444'
                }} />
                <span style={{
                    color: '#fca5a5', fontSize: '0.85rem', fontWeight: 500, letterSpacing: '0.5px',
                    fontFamily: '"Inter", sans-serif'
                }}>
                    No active Spotify device found. <br />
                    Please open Spotify on any device to continue.
                </span>
            </motion.div >
        )}
    </AnimatePresence >
);
