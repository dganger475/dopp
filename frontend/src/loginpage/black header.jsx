import React from 'react';

const styles = {
  Header: {
    top: '0px',
    left: '0px',
    width: '375px',
    height: '84px',
    backgroundColor: '#000000',
  },
};

const Header = (props) => {
  return (
    <div style={styles.Header}>
      {props.children}
    </div>
  );
};

export default Header;