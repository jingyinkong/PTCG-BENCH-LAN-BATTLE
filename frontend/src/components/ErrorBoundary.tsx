import React from 'react';

interface Props { children: React.ReactNode; fallback?: React.ReactNode }
interface State { hasError: boolean; error: Error | null }

class ErrorBoundary extends React.Component<Props, State> {
  state: State = { hasError: false, error: null };
  static getDerivedStateFromError(e: Error) { return { hasError: true, error: e }; }
  componentDidCatch(e: Error, info: React.ErrorInfo) { console.error('ErrorBoundary:', e, info); }
  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div style={{ padding: 24, textAlign: 'center', color: '#f44' }}>
          <h3>发生错误</h3><p>{this.state.error?.message || '未知错误'}</p>
          <button onClick={() => this.setState({ hasError: false, error: null })}
            style={{ marginTop: 12, padding: '8px 16px' }}>重试</button>
        </div>);
    }
    return this.props.children;
  }
}
export default ErrorBoundary;
