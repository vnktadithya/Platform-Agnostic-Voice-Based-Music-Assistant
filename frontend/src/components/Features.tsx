import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Link2, Zap, MessageSquare, Smartphone, Layers } from 'lucide-react';
import React, { Suspense } from 'react';
import styles from './Features.module.css';

// Lazy load the heavy 3D background component
const FeaturesBackground = React.lazy(() => import('./FeaturesBackground'));

const features = [
    {
        icon: Mic,
        title: 'Voice-Powered Intelligence',
        description: 'Simply speak naturally - SAM understands context and intent to deliver exactly what you want to hear.',
        color1: '#7c3aed', color2: '#ec4899',
    },
    {
        icon: Link2,
        title: 'Universal Platform Access',
        description: 'Seamlessly works across Spotify, Apple Music, YouTube Music, Amazon Music, SoundCloud and more - all in one place.',
        color1: '#2563eb', color2: '#06b6d4',
    },
    {
        icon: Zap,
        title: 'Seamless Integration',
        description: 'Unified control across all your music services. Switch between platforms effortlessly without missing a beat.',
        color1: '#06b6d4', color2: '#14b8a6',
    },
    {
        icon: MessageSquare,
        title: 'Context-Aware',
        description: 'SAM remembers what you just said. Ask follow-up questions or refine your requests naturally without repeating details.',
        color1: '#ec4899', color2: '#9333ea',
    },
    {
        icon: Smartphone,
        title: 'Real-Time Sync',
        description: 'Your music, playlists, and preferences sync instantly across all your devices - phone, tablet, desktop, and smart speakers.',
        color1: '#f97316', color2: '#ec4899',
    },
    {
        icon: Layers,
        title: 'Multi-Action Handling',
        description: 'Handle multi-step requests in a single breath. "Play Blinding Lights and add it to my Gym playlist" works instantly.',
        color1: '#f59e0b', color2: '#d97706',
    },
];

const Features = () => {
    return (
        <section id="features" className={styles.featuresSection}>
            {/* 3D Background - HeroParticles */}
            {/* 3D Background - Lazy Loaded with Fade-In */}
            <Suspense fallback={null}>
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 1.5, ease: "easeOut" }} // Smooth cinematic fade-in
                    className={styles.backgroundContainer}
                >
                    <FeaturesBackground />
                </motion.div>
            </Suspense>

            {/* Content Container */}
            <div className={styles.contentContainer}>
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    className={styles.headerWrapper}
                >
                    <h2 className={`text-gradient ${styles.title}`}>
                        Powerful Features
                    </h2>
                    <p className={styles.description}>
                        Effortlessly command, curate, and synchronize your entire music universe using just your voice.
                    </p>
                </motion.div>

                <div className={styles.grid}>
                    {features.map((feature, index) => (
                        <FeatureCard key={index} feature={feature} index={index} />
                    ))}
                </div>

                {/* --- Platform Capabilities Section --- */}
                <motion.div
                    id="platform-intelligence"
                    initial={{ opacity: 0, y: 30 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6, delay: 0.2 }}
                    className={styles.platformSection}
                >
                    <h2 className={`text-gradient ${styles.platformTitle}`}>
                        Platform Intelligence
                    </h2>

                    <div className={styles.platformGrid}>
                        {/* Spotify Card */}
                        <CapabilityCard
                            platform="Spotify"
                            color="#1DB954"
                            capabilities={[
                                "Playback Control: Play, Pause, Resume, Next, Previous",
                                "Precision Seeking: Jump to any specific timestamp",
                                "Smart Play: 'Play [Song] by [Artist]'",
                                "Play your 'Liked Songs' collection",
                                "Playlist Management: Create, Delete, & Rename playlists",
                                "Curate: Add or Remove tracks from any playlist",
                                "Organize: Reorder tracks within your playlists",
                                "Library: Like / Unlike the current song instantly",
                                "Context Aware: Controls active Spotify Connect devices"
                            ]}
                        />

                        {/* SoundCloud Card */}
                        <CapabilityCard
                            platform="SoundCloud"
                            color="#ff5500"
                            capabilities={[
                                "Search: Find untagged/remix tracks in the full catalog",
                                "Playback: Stream tracks via the visual widget",
                                "Playlist Creation: Create new public playlists",
                                "Playlist Editing: Delete playlists & clear tracks",
                                "Curate: Add any track to your playlists",
                                "Favorites: Like / Unlike tracks to your library",
                                "Library: Access your full Liked Tracks history",
                                "Import: Syncs your existing personal playlists",
                                "Metadata: View detailed track/artist info"
                            ]}
                        />
                    </div>
                </motion.div>
            </div>
        </section>
    );
};

const FeatureCard = ({ feature, index: _index }: { feature: any, index: number }) => {
    const [hovered, setHovered] = React.useState(false);

    return (
        <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.04 }}
            onHoverStart={() => setHovered(true)}
            onHoverEnd={() => setHovered(false)}
            animate={{
                y: hovered ? -10 : 0,
                scale: hovered ? 1.05 : 1,
            }}
            className={styles.featureCard}
            style={{
                /* Dynamic Shadow / Glow - kept inline as it depends on props */
                boxShadow: hovered
                    ? `0 20px 50px ${feature.color1}30, 0 0 0 1px ${feature.color1}40`
                    : '0 10px 30px rgba(0,0,0,0.2)',
            }}
        >
            {/* Icon Container with Gradient Glow */}
            <div
                className={styles.iconContainer}
                style={{
                    background: `linear-gradient(135deg, ${feature.color1}, ${feature.color2})`,
                    boxShadow: `0 8px 20px ${feature.color1}50`,
                }}
            >
                <feature.icon size={28} color="white" strokeWidth={2.5} />
            </div>

            <h3
                className={styles.cardTitle}
                style={{
                    textShadow: hovered ? `0 0 20px ${feature.color1}80` : 'none',
                }}
            >
                {feature.title}
            </h3>

            <p className={styles.cardDescription}>
                {feature.description}
            </p>

            {/* Bottom Glow Effect */}
            <div
                className={styles.bottomGlow}
                style={{
                    background: `linear-gradient(90deg, transparent, ${feature.color1}, transparent)`,
                    boxShadow: `0 -10px 30px ${feature.color1}`,
                    opacity: hovered ? 0.8 : 0,
                }}
            />
        </motion.div>
    );
};

const CapabilityCard = ({ platform, color, capabilities }: { platform: string, color: string, capabilities: string[] }) => {
    return (
        <div
            className={styles.capabilityCard}
            style={{
                border: `1px solid ${color}20`,
            }}
        >
            {/* Header / Logo Area */}
            <div className={styles.cardHeader}>
                <div
                    className={styles.platformDot}
                    style={{
                        background: color,
                        boxShadow: `0 0 15px ${color}`
                    }}
                />
                <h3 className={styles.platformName}>{platform}</h3>
            </div>

            {/* List */}
            <ul className={styles.capabilityList}>
                {capabilities.map((cap, i) => (
                    <li key={i} className={styles.capabilityItem}>
                        {/* Check Icon */}
                        <div
                            className={styles.checkIcon}
                            style={{
                                background: `${color}15`,
                                border: `1px solid ${color}40`,
                                color: color
                            }}
                        >✓</div>
                        <span className={styles.capabilityText}>{cap}</span>
                    </li>
                ))}
            </ul>

            {/* Bottom Glow */}
            <div
                className={styles.cardGlow}
                style={{
                    background: color,
                }}
            />
        </div>
    );
};

export default Features;
