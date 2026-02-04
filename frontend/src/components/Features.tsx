import { motion } from 'framer-motion';
import { Mic, Link2, Zap, MessageSquare, Smartphone, Layers } from 'lucide-react';
import React, { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { HeroParticles } from './canvas/HeroParticles';

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
        <section id="features" style={{
            padding: '6rem 1.5rem',
            position: 'relative',
            overflow: 'hidden',
            color: 'white',
            minHeight: '100vh',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'flex-start'
        }}>
            {/* 3D Background - HeroParticles */}
            <div style={{ position: 'absolute', inset: 0, zIndex: 0 }}>
                <Canvas camera={{ position: [0, 0, 10], fov: 45 }}>
                    <Suspense fallback={null}>
                        <color attach="background" args={['#050505']} />
                        <HeroParticles />
                    </Suspense>
                </Canvas>
            </div>

            {/* Content Container */}
            <div style={{
                position: 'relative', zIndex: 10,
                maxWidth: '1280px', margin: '0 auto', width: '100%'
            }}>
                <motion.div
                    initial={{ opacity: 0, y: 30 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ duration: 0.6 }}
                    style={{ textAlign: 'center', marginBottom: '5rem' }}
                >
                    <h2 className="text-gradient" style={{
                        fontSize: '3.5rem', fontWeight: 700, marginBottom: '1.5rem',
                        lineHeight: 1.1,
                        textShadow: '0 0 20px rgba(255,255,255,0.1)'
                    }}>
                        Powerful Features
                    </h2>
                    <p style={{
                        fontSize: '1.25rem', color: '#9ca3af', maxWidth: '42rem', margin: '0 auto',
                        lineHeight: 1.6
                    }}>
                        Effortlessly command, curate, and synchronize your entire music universe using just your voice.
                    </p>
                </motion.div>

                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
                    gap: '2.5rem',
                }}>
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
                    style={{ marginTop: '8rem', scrollMarginTop: '100px' }}
                >
                    <h2 className="text-gradient" style={{
                        fontSize: '3.5rem', fontWeight: 700, marginBottom: '2rem',
                        textAlign: 'center', lineHeight: 1.3, paddingBottom: '0.5rem',
                        textShadow: '0 0 20px rgba(255,255,255,0.1)'
                    }}>
                        Platform Intelligence
                    </h2>

                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
                        gap: '2.5rem',
                        maxWidth: '1000px',
                        margin: '0 auto'
                    }}>
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
            style={{
                /* Glassmorphism */
                background: 'rgba(255, 255, 255, 0.02)',
                backdropFilter: 'blur(20px)',
                WebkitBackdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                borderRadius: '1.5rem',
                padding: '1.5rem',
                height: '320px',
                display: 'flex',
                flexDirection: 'column',
                position: 'relative',

                /* Dynamic Shadow / Glow */
                boxShadow: hovered
                    ? `0 20px 50px ${feature.color1}30, 0 0 0 1px ${feature.color1}40`
                    : '0 10px 30px rgba(0,0,0,0.2)',

                cursor: 'default',
            }}
        >
            {/* Icon Container with Gradient Glow */}
            <div style={{
                width: '3rem', height: '3rem',
                borderRadius: '1rem',
                background: `linear-gradient(135deg, ${feature.color1}, ${feature.color2})`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                marginBottom: '1.5rem',
                boxShadow: `0 8px 20px ${feature.color1}50`,
                flexShrink: 0
            }}>
                <feature.icon size={28} color="white" strokeWidth={2.5} />
            </div>

            <h3 style={{
                fontSize: '1.5rem',
                fontWeight: 700,
                marginBottom: '1rem',
                color: 'white',
                textShadow: hovered ? `0 0 20px ${feature.color1}80` : 'none',
                transition: 'text-shadow 0.3s ease'
            }}>
                {feature.title}
            </h3>

            <p style={{ color: 'rgba(255,255,255,0.7)', lineHeight: 1.7, fontSize: '1.05rem' }}>
                {feature.description}
            </p>

            {/* Bottom Glow Effect */}
            <div style={{
                position: 'absolute',
                bottom: '0',
                left: '20%',
                right: '20%',
                height: '1px',
                background: `linear-gradient(90deg, transparent, ${feature.color1}, transparent)`,
                boxShadow: `0 -10px 30px ${feature.color1}`,
                opacity: hovered ? 0.8 : 0,
                transition: 'opacity 0.5s ease',
            }} />
        </motion.div>
    );
};

const CapabilityCard = ({ platform, color, capabilities }: { platform: string, color: string, capabilities: string[] }) => {
    return (
        <div style={{
            background: 'rgba(255, 255, 255, 0.03)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
            border: `1px solid ${color}20`,
            borderRadius: '1.5rem',
            padding: '2.5rem',
            position: 'relative',
            overflow: 'hidden'
        }}>
            {/* Header / Logo Area */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
                <div style={{
                    width: '12px', height: '12px', borderRadius: '50%',
                    background: color,
                    boxShadow: `0 0 15px ${color}`
                }} />
                <h3 style={{ fontSize: '1.8rem', fontWeight: 700, color: 'white' }}>{platform}</h3>
            </div>

            {/* List */}
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {capabilities.map((cap, i) => (
                    <li key={i} style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'rgba(255,255,255,0.9)' }}>
                        {/* Check Icon */}
                        <div style={{
                            minWidth: '20px', height: '20px', borderRadius: '50%',
                            background: `${color}15`,
                            border: `1px solid ${color}40`,
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            color: color, fontSize: '0.7rem'
                        }}>✓</div>
                        <span style={{ fontSize: '0.95rem' }}>{cap}</span>
                    </li>
                ))}
            </ul>

            {/* Bottom Glow */}
            <div style={{
                position: 'absolute', bottom: '-20px', right: '-20px',
                width: '150px', height: '150px',
                background: color,
                filter: 'blur(80px)',
                opacity: 0.15,
                borderRadius: '50%'
            }} />
        </div>
    );
};

export default Features;
