import { Route, Switch } from 'wouter';
import { LandingPage } from './pages/LandingPage';
import PlatformSelect from './pages/PlatformSelect';
import { ChatOverlay } from './pages/ChatOverlay';
import { FeaturesPage } from './pages/FeaturesPage';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { ToastProvider } from '@/components/ui/Toast';

function App() {
  return (
    <div className="app-container">
      <ErrorBoundary>
        <ToastProvider>
          <Switch>
            <Route path="/" component={LandingPage} />
            <Route path="/platform-select" component={PlatformSelect} />
            <Route path="/chat" component={ChatOverlay} />
            <Route path="/features" component={FeaturesPage} />
          </Switch>
        </ToastProvider>
      </ErrorBoundary>
    </div>
  );
}

export default App;
