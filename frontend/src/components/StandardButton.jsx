import React from 'react';

/**
 * StandardButton component for consistent button styling across the application
 * 
 * @param {Object} props - Component props
 * @param {string} props.text - Button text
 * @param {function} props.onClick - Click handler function
 * @param {string} props.type - Button type: 'primary' (blue), 'secondary' (light gray), 'success' (green), 'danger' (red)
 * @param {boolean} props.fullWidth - Whether the button should take full width
 * @param {string} props.icon - Optional FontAwesome icon name
 * @param {string} props.className - Additional CSS classes
 */
const StandardButton = ({ 
  text, 
  onClick, 
  type = 'primary', 
  fullWidth = false, 
  icon = null,
  className = '',
  disabled = false,
  ...rest
}) => {
  // Define button colors based on type
  const getButtonStyles = () => {
    const baseStyle = {
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      gap: '8px',
      padding: '12px 20px',
      borderRadius: '8px',
      fontWeight: '600',
      fontSize: '16px',
      cursor: disabled ? 'not-allowed' : 'pointer',
      transition: 'all 0.2s ease',
      border: '1px solid #000000',
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      opacity: disabled ? 0.6 : 1,
      width: fullWidth ? '100%' : 'auto',
      fontFamily: 'Arial, sans-serif',
    };

    // Color variations
    switch (type) {
      case 'primary':
        return {
          ...baseStyle,
          backgroundColor: '#007bff',
          color: 'white',
        };
      case 'secondary':
        return {
          ...baseStyle,
          backgroundColor: '#e0e0e0',
          color: '#333333',
        };
      case 'success':
        return {
          ...baseStyle,
          backgroundColor: '#28a745',
          color: 'white',
        };
      case 'danger':
        return {
          ...baseStyle,
          backgroundColor: '#dc3545',
          color: 'white',
        };
      default:
        return {
          ...baseStyle,
          backgroundColor: '#007bff',
          color: 'white',
        };
    }
  };

  return (
    <button
      onClick={disabled ? null : onClick}
      style={getButtonStyles()}
      className={className}
      disabled={disabled}
      {...rest}
    >
      {icon && <span className="button-icon">{icon}</span>}
      {text}
    </button>
  );
};

export default StandardButton;
