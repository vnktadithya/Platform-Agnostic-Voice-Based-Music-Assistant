import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export const SuggestionText = () => {
    const suggestions = [
        "Ask anything",
        "Play 'Blinding Lights'",
        "Start my 'Gym' playlist",
        "Skip the song",
        "Add the current song to my favourites",
        "Create a new playlist for me"
    ];
    const [index, setIndex] = useState(0);

    useEffect(() => {
        const interval = setInterval(() => {
            setIndex((prev) => (prev + 1) % suggestions.length);
        }, 3500);
        return () => clearInterval(interval);
    }, []);

    return (
        <div style={{ position: 'relative', height: '24px', marginBottom: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <AnimatePresence mode="wait">
                <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 0.5, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.5 }}
                    style={{
                        position: 'absolute',
                        color: 'white',
                        fontSize: '0.9rem',
                        fontWeight: 300,
                        letterSpacing: '0.5px',
                        textAlign: 'center',
                        width: 'max-content'
                    }}
                >
                    {suggestions[index]}
                </motion.div>
            </AnimatePresence>
        </div>
    );
};
