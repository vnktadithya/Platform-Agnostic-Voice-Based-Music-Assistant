import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import styles from './Overlay.module.css';

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
        <div className={styles.suggestionContainer}>
            <AnimatePresence mode="wait">
                <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 0.5, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.5 }}
                    className={styles.suggestionText}
                >
                    {suggestions[index]}
                </motion.div>
            </AnimatePresence>
        </div>
    );
};
