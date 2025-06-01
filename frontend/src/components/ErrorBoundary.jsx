import React from 'react';
import PropTypes from 'prop-types';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div style={{
          padding: '16px',
          background: '#fff3f3',
          border: '1px solid #ffcdd2',
          borderRadius: '4px',
          color: '#d32f2f',
          fontSize: '14px'
        }}>
          {this.props.errorMessage || 'Something went wrong loading this content.'}
        </div>
      );
    }

    return this.props.children;
  }
}

ErrorBoundary.propTypes = {
  children: PropTypes.node.isRequired,
  fallback: PropTypes.node,
  errorMessage: PropTypes.string
};

export default ErrorBoundary; 