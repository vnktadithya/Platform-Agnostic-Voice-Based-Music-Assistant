import { motion, AnimatePresence } from 'framer-motion';
import React from 'react';
import { SuggestionText } from './SuggestionText';

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
        <div style={{
            position: 'absolute', bottom: '10%', left: '50%', transform: 'translateX(-50%)',
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1.5rem',
            pointerEvents: 'auto'
        }}>
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
                        style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}
                    >
                        <div style={{ position: 'relative' }}>
                            {isListening && (
                                <>
                                    <motion.div
                                        animate={{ scale: [1, 2], opacity: [0.5, 0] }}
                                        transition={{ repeat: Infinity, duration: 2, ease: "easeOut" }}
                                        style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: '1px solid rgba(255,255,255,0.3)' }}
                                    />
                                    <motion.div
                                        animate={{ scale: [1, 1.5], opacity: [0.5, 0] }}
                                        transition={{ repeat: Infinity, duration: 2, delay: 0.5, ease: "easeOut" }}
                                        style={{ position: 'absolute', inset: 0, borderRadius: '50%', border: '1px solid rgba(255,255,255,0.2)' }}
                                    />
                                </>
                            )}
                            <motion.button
                                onClick={onMicClick}
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                style={{
                                    width: '72px', height: '72px', borderRadius: '50%',
                                    background: isListening ? '#ef4444' : 'rgba(255, 255, 255, 0.1)',
                                    backdropFilter: 'blur(10px)',
                                    border: '1px solid rgba(255, 255, 255, 0.2)',
                                    cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    boxShadow: isListening ? '0 0 30px rgba(239, 68, 68, 0.4)' : '0 10px 30px rgba(0,0,0,0.2)',
                                    transition: 'all 0.3s ease'
                                }}
                            >
                                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                    <path d="M12 2C10.34 2 9 3.34 9 5V11C9 12.66 10.34 14 12 14C13.66 14 15 12.66 15 11V5C15 3.34 13.66 2 12 2Z" fill={isListening ? "white" : "white"} fillOpacity={isListening ? 1 : 0.8} />
                                    <path d="M19 11C19 14.87 15.87 18 12 18C8.13 18 5 14.87 5 11" stroke={isListening ? "white" : "white"} strokeOpacity={isListening ? 1 : 0.8} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                    <path d="M12 18V22M8 22H16" stroke={isListening ? "white" : "white"} strokeOpacity={isListening ? 1 : 0.8} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                                </svg>
                            </motion.button>
                        </div>
                        <p style={{ opacity: 0.5, fontSize: '0.8rem', color: 'white' }}>
                            {samState === 'THINKING' ? "Analyzing intent..." : (isListening ? "Listening..." : "Tap to speak")}
                        </p>

                        <button
                            onClick={() => setInputMode('text')}
                            style={{
                                background: 'transparent', border: 'none', cursor: 'pointer',
                                color: 'rgba(255,255,255,0.4)', fontSize: '0.8rem',
                                display: 'flex', alignItems: 'center', gap: '6px',
                                marginTop: '0.5rem',
                                padding: '8px 16px', borderRadius: '20px',
                                transition: 'all 0.2s'
                            }}
                            onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                            onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
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
                        style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}
                    >
                        <p style={{ opacity: 0.5, fontSize: '0.8rem', color: 'white' }}>
                            {samState === 'THINKING' ? "Analyzing intent..." : ""}
                        </p>
                        <form onSubmit={onTextSubmit} style={{ width: '380px', position: 'relative' }}>
                            <div style={{
                                display: 'flex', alignItems: 'center',
                                background: 'rgba(20, 20, 25, 0.9)',
                                border: '1px solid rgba(255, 255, 255, 0.2)',
                                borderRadius: '30px',
                                padding: '8px 8px 8px 20px',
                                backdropFilter: 'blur(16px)',
                                boxShadow: '0 8px 32px rgba(0,0,0,0.5)'
                            }}>
                                <input
                                    type="text"
                                    value={inputText}
                                    onChange={(e) => setInputText(e.target.value)}
                                    placeholder="Message SAM..."
                                    autoFocus
                                    style={{
                                        flex: 1, background: 'transparent', border: 'none',
                                        color: 'white', fontSize: '0.95rem', outline: 'none'
                                    }}
                                />
                                <button
                                    type="submit"
                                    disabled={!inputText.trim()}
                                    style={{
                                        width: '36px', height: '36px', borderRadius: '50%',
                                        background: inputText.trim() ? 'white' : 'rgba(255,255,255,0.1)',
                                        border: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                        cursor: inputText.trim() ? 'pointer' : 'default',
                                        transition: 'all 0.2s'
                                    }}
                                >
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={inputText.trim() ? "black" : "rgba(255,255,255,0.3)"} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M5 12H19M19 12L12 5M19 12L12 19" />
                                    </svg>
                                </button>
                            </div>
                        </form>

                        <button
                            onClick={() => setInputMode('voice')}
                            style={{
                                background: 'transparent', border: 'none', cursor: 'pointer',
                                color: 'rgba(255,255,255,0.4)', fontSize: '0.8rem',
                                display: 'flex', alignItems: 'center', gap: '6px',
                                padding: '8px 16px', borderRadius: '20px'
                            }}
                            onMouseOver={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.05)'}
                            onMouseOut={(e) => e.currentTarget.style.background = 'transparent'}
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
