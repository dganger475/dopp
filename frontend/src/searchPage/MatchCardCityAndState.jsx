import React from "react";

const MatchCardCityAndState = ({ city = "Portland", state = "OR" }) => {
  return (
    <div>
      <strong>{city}</strong>, {state}
    </div>
  );
};

export default MatchCardCityAndState;
