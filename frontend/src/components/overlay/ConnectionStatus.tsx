interface ConnectionStatusProps {
    activePlatform: string;
    theme: { color: string; label?: string } | undefined;
}

import styles from './Overlay.module.css';

export const ConnectionStatus = ({ activePlatform, theme }: ConnectionStatusProps) => {
    return (
        <div className={styles.connectionStatus}>
            <span className={styles.statusLabel}>CONNECTED TO</span>
            <span className={styles.platformName}>{theme?.label || activePlatform.toUpperCase()}</span>
            <div
                className={styles.connectionDot}
                style={{
                    background: theme?.color || '#333',
                    boxShadow: `0 0 8px ${theme?.color || '#333'}`
                }}
            />
        </div>
    );
};
