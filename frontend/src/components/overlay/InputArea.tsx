import { motion, AnimatePresence } from 'framer-motion';
import React from 'react';
import { SuggestionText } from './SuggestionText';
import styles from './Overlay.module.css';

interface InputAreaProps {
    samState: 'IDLE' | 'LISTENING' | 'THINKING' | 'SPEAKING';
    inputMode: 'voice' | 'text';
    setInputMode: (mode: 'voice' | 'text') => void;
    inputText: string;
    setInputText: (text: string) => void;
    onMicClick: () => void;
    onTextSubmit: (e: React.FormEvent) => void;
}

export const InputArea: React.FC<InputAreaProps> = ({
    samState, inputMode, setInputMode, inputText, setInputText, onMicClick, onTextSubmit
}) => {
    const isListening = samState === 'LISTENING';

    return (
        <div className={styles.inputAreaContainer}>
            <AnimatePresence>
                {samState === 'IDLE' && <SuggestionText />}
            </AnimatePresence>

            <AnimatePresence mode="wait">
                {inputMode === 'voice' ? (
                    <motion.div
                        key="voice-input"
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        className={styles.voiceInputWrapper}
                    >
                        <div className={styles.micButtonWrapper}>
                            {isListening && (
                                <>
                                    <motion.div
                                        animate={{ scale: [1, 2], opacity: [0.5, 0] }}
                                        transition={{ repeat: Infinity, duration: 2, ease: "easeOut" }}
                                        className={styles.pulseCircle}
                                    />
                                    <motion.div
                                        animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
                                        transition={{ repeat: Infinity, duration: 2, delay: 0.5, ease: "easeOut" }}
                                        className={styles.pulseCircleDelayed}
                                    />
                                </>
                            )}
                            <motion.button
                                onClick={onMicClick}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                className={`${styles.micButton} ${isListening ? styles.micButtonListening : ''}`}
                            >
                                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M12 2C10.34 2 9 3.34 9 5V11C9 12.66 10.34 14 12 14C13.66 14 15 12.66 15 11V5C15 3.34 13.66 2 12 2Z" fill={isListening ? "white" : "white"} fillOpacity={isListening ? 1 : 0.8} />
                                    <path d="M19 11C19 14.87 15.87 18 12 18C8.13 18 5 14.87 5 11" stroke={isListening ? "white" : "white"} strokeOpacity={isListening ? 1 : 0.8} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    <path d="M12 18V22M8 22H16" stroke={isListening ? "white" : "white"} strokeOpacity={isListening ? 1 : 0.8} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                            </motion.button>
                        </div>
                        <p className={styles.statusText}>
                            {samState === 'THINKING' ? "Analyzing intent..." : (isListening ? "Listening..." : "Tap to speak")}
                        </p>

                        <button
                            onClick={() => setInputMode('text')}
                            className={styles.switchModeButton}
                        >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                            </svg>
                            Type instead
                        </button>
                    </motion.div>
                ) : (
                    <motion.div
                        key="text-input"
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 10 }}
                        className={styles.textInputWrapper}
                    >
                        <p className={styles.statusText}>
                            {samState === 'THINKING' ? "Analyzing intent..." : ""}
                        </p>
                        <form onSubmit={onTextSubmit} className={styles.textInputForm}>
                            <div className={styles.textInputContainer}>
                                <input
                                    type="text"
                                    value={inputText}
                                    onChange={(e) => setInputText(e.target.value)}
                                    placeholder="Message SAM..."
                                    autoFocus
                                    className={styles.textInput}
                                />
                                <button
                                    type="submit"
                                    disabled={!inputText.trim()}
                                    className={`${styles.sendButton} ${inputText.trim() ? styles.sendButtonActive : ''}`}
                                >
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={inputText.trim() ? "black" : "rgba(255,255,255,0.3)"} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M5 12H19M19 12L12 5M19 12L12 19" />
                                    </svg>
                                </button>
                            </div>
                        </form>

                        <button
                            onClick={() => setInputMode('voice')}
                            className={styles.switchModeButton}
                        >
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                                <path d="M12 19v4" />
                                <path d="M8 23h8" />
                            </svg>
                            Use Voice
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

