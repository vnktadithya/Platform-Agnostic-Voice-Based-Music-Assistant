import { Component, type ErrorInfo, type ReactNode } from "react";
import styles from './ErrorBoundary.module.css';

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
                <div className={styles.errorContainer}>
                    <div className={styles.errorBox}>
                        <div className={styles.icon}>🌌</div>
                        <h2 className={styles.title}>
                            System Malfunction
                        </h2>
                        <p className={styles.message}>
                            We encountered an unexpected anomaly in the space-time continuum.
                        </p>

                        <button
                            onClick={() => window.location.reload()}
                            className={styles.restartButton}
                        >
                            Reinitialize System
                        </button>

                        {import.meta.env.DEV && this.state.error && (
                            <details className={styles.debugDetails}>
                                <summary className={styles.debugSummary}>Debug Details</summary>
                                <div className={styles.debugContent}>
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
