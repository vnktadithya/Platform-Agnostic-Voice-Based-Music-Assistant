import { motion } from 'framer-motion';

export const GhostMessage = ({ message }: { message: string }) => (
    <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 0.6, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.8 }}
        style={{
            position: 'absolute',
            top: '30%',
            width: '100%',
            textAlign: 'center',
            color: '#94a3b8',
            fontSize: '0.9rem',
            letterSpacing: '0.5px',
            pointerEvents: 'none',
            fontFamily: '"Inter", sans-serif',
            fontWeight: 300
        }}
    >
        {message}
    </motion.div>
);
