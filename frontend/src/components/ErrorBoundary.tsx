import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
    children?: ReactNode;
}

interface State {
    hasError: boolean;
    error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error("Uncaught error:", error, errorInfo);
    }

    public render() {
        if (this.state.hasError) {
            return (
                <div style={{
                    height: '100vh',
                    width: '100%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: 'radial-gradient(circle at 50% 50%, #1a1a2e 0%, #050505 100%)',
                    color: 'white',
                    fontFamily: "'Inter', sans-serif",
                    overflow: 'hidden'
                }}>
                    <div style={{
                        background: 'rgba(255, 255, 255, 0.03)',
                        backdropFilter: 'blur(20px)',
                        border: '1px solid rgba(255, 255, 255, 0.1)',
                        padding: '40px',
                        borderRadius: '24px',
                        maxWidth: '500px',
                        width: '90%',
                        textAlign: 'center',
                        boxShadow: '0 20px 50px rgba(0,0,0,0.5)'
                    }}>
                        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🌌</div>
                        <h2 style={{
                            fontSize: '1.8rem',
                            marginBottom: '0.5rem',
                            fontWeight: 600,
                            background: 'linear-gradient(to right, #fff, #aaa)',
                            WebkitBackgroundClip: 'text',
                            WebkitTextFillColor: 'transparent'
                        }}>
                            System Malfunction
                        </h2>
                        <p style={{ color: '#94a3b8', marginBottom: '2rem', lineHeight: '1.6' }}>
                            We encountered an unexpected anomaly in the space-time continuum.
                        </p>

                        <button
                            onClick={() => window.location.reload()}
                            style={{
                                padding: '12px 32px',
                                background: 'white',
                                color: 'black',
                                border: 'none',
                                borderRadius: '30px',
                                fontSize: '0.95rem',
                                fontWeight: 600,
                                cursor: 'pointer',
                                transition: 'transform 0.2s',
                                boxShadow: '0 0 20px rgba(255,255,255,0.2)'
                            }}
                            onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
                            onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
                        >
                            Reinitialize System
                        </button>

                        {import.meta.env.DEV && this.state.error && (
                            <details style={{ marginTop: '2rem', textAlign: 'left' }}>
                                <summary style={{ cursor: 'pointer', color: '#555', fontSize: '0.8rem' }}>Debug Details</summary>
                                <div style={{
                                    marginTop: '10px',
                                    background: 'rgba(0,0,0,0.5)',
                                    padding: '15px',
                                    borderRadius: '8px',
                                    fontSize: '0.75rem',
                                    color: '#ff5555',
                                    overflow: 'auto',
                                    maxHeight: '200px'
                                }}>
                                    {this.state.error.toString()}
                                </div>
                            </details>
                        )}
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
