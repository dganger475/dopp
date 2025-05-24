import React from 'react';

// Card container
const cardStyle = {
  width: '140px',
  height: '203px',
  backgroundColor: '#ef4444',
  borderRadius: '6px',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  position: 'relative',
  boxSizing: 'border-box',
  padding: '12px 0 0 0',
};

// Badge pill
const badgePillStyle = {
  width: '130px',
  height: '26px',
  backgroundColor: '#000',
  borderRadius: '9999px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  position: 'absolute',
  top: '8px',
  left: '50%',
  transform: 'translateX(-50%)',
  zIndex: 2,
};
const badgeTextStyle = {
  color: '#fff',
  fontSize: '12px',
  fontFamily: 'Open Sans',
  fontWeight: 500,
  lineHeight: '16px',
};

// Image border
const imageBorderStyle = {
  width: '108px',
  height: '106px',
  border: '2.67px solid #000',
  borderRadius: '6px',
  background: 'rgba(0,0,0,0)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  margin: '38px 0 0 0',
};
// Image
const imageStyle = {
  width: '100px',
  height: '100px',
  backgroundPosition: 'center center',
  backgroundSize: 'cover',
  backgroundRepeat: 'no-repeat',
  borderRadius: '4px',
};

// Name pill
const namePillStyle = {
  width: '96px',
  height: '24px',
  backgroundColor: '#000',
  borderRadius: '9999px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  margin: '10px 0 0 0',
};
const nameTextStyle = {
  color: '#fff',
  fontSize: '12px',
  fontFamily: 'Open Sans',
  lineHeight: '16px',
  whiteSpace: 'nowrap',
  overflow: 'hidden',
  textOverflow: 'ellipsis',
};

// City/state
const cityTextStyle = {
  color: '#fff',
  fontSize: '11px',
  fontFamily: 'Open Sans',
  lineHeight: '14px',
  margin: '4px 0 0 0',
  textAlign: 'center',
};

// Similarity score
const similarityContainerStyle = {
  width: '87px',
  height: '16px',
  backgroundColor: '#fff',
  borderRadius: '6px',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  margin: '10px 0 0 0',
};
const similarityTextStyle = {
  color: '#000',
  fontSize: '12px',
  fontFamily: 'Open Sans',
  lineHeight: '16px',
};

const RegisteredMatchCard = ({
  image = 'https://assets.api.uizard.io/api/cdn/stream/31b53d07-f3cb-43df-afb7-72e4e358fa99.png',
  name = '@match2',
  cityState = 'New York, NY',
  similarity = 78,
  badgeText = 'REGISTERED USER',
}) => (
  <div style={cardStyle}>
    {/* Badge */}
    <div style={badgePillStyle}>
      <span style={badgeTextStyle}>{badgeText}</span>
    </div>
    {/* Image with border */}
    <div style={imageBorderStyle}>
      <div style={{ ...imageStyle, backgroundImage: `url(${image})` }} />
    </div>
    {/* Name pill */}
    <div style={namePillStyle}>
      <span style={nameTextStyle}>{name}</span>
    </div>
    {/* City/State */}
    <div style={cityTextStyle}>{cityState}</div>
    {/* Similarity score */}
    <div style={similarityContainerStyle}>
      <span style={similarityTextStyle}>Similarity: {similarity}%</span>
    </div>
  </div>
);

export default RegisteredMatchCard;
