import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error: error,
      errorInfo: errorInfo
    });
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          padding: '16px',
          margin: '16px',
          backgroundColor: '#fff',
          borderRadius: '8px',
          border: '1px solid #e0e0e0',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ color: '#dc2626', marginBottom: '8px' }}>Something went wrong</h3>
          <p style={{ color: '#4b5563', fontSize: '14px' }}>
            We're sorry, but there was an error displaying this post.
          </p>
          {process.env.NODE_ENV === 'development' && (
            <details style={{ marginTop: '8px', fontSize: '12px', color: '#6b7280' }}>
              <summary>Error Details</summary>
              <pre style={{ 
                marginTop: '8px', 
                padding: '8px', 
                backgroundColor: '#f3f4f6', 
                borderRadius: '4px',
                overflow: 'auto'
              }}>
                {this.state.error && this.state.error.toString()}
                {this.state.errorInfo && this.state.errorInfo.componentStack}
              </pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary; 