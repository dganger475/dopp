import React from "react";
import Card16 from "./navBar/Card (16).jsx";
import Card17 from "./navBar/Card (17).jsx";
import Icon8 from "./navBar/Icon (8).jsx";
import Icon9 from "./navBar/Icon (9).jsx";
import Icon10 from "./navBar/Icon (10).jsx";
import Icon11 from "./navBar/Icon (11).jsx";
import Image19 from "./navBar/Image (19).jsx";

function NavBar(props) {
  return (
    <Card16>
      <Image19 src={props.logo} />
      <Icon8 />
      <Icon9 />
      <Icon10 />
      <Icon11 />
      <Card17 />
    </Card16>
  );
}

export default NavBar;
