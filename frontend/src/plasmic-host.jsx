import * as React from "react";
import { PlasmicCanvasHost, registerComponent } from "@plasmicapp/host";

// Root components
import RegisteredSearchResult from "./searchPage/RegisteredSearchResult.jsx";
import SearchPage from "./searchPage/SearchPage.jsx";
import SearchResult from "./searchPage/SearchResult.jsx";
import SearchResultsPage from "./searchPage/SearchResultsPage.jsx";
import UserCard from "./searchPage/UserCard.jsx";

// registeredSearchResult components
import RegisteredMatchCardCityAndState from "./searchPage/registeredSearchResult/match card city and state.jsx";
import RegisteredMatchCardBadgePill from "./searchPage/registeredSearchResult/registered match card badge pill.jsx";
import RegisteredMatchCardBadgeText from "./searchPage/registeredSearchResult/registered match card badge text.jsx";
import RegisteredMatchCardContainer from "./searchPage/registeredSearchResult/registered match card container.jsx";
import RegisteredMatchCardImageBorder from "./searchPage/registeredSearchResult/registered match card image border.jsx";
import RegisteredMatchCardNamePillText from "./searchPage/registeredSearchResult/registered match card name pill text.jsx";
import RegisteredMatchCardNamePill from "./searchPage/registeredSearchResult/registered match card name pill.jsx";
import RegisteredMatchCardSampleImage from "./searchPage/registeredSearchResult/registered match card sample image.jsx";
import RegisteredSimilarityScoreContainer from "./searchPage/registeredSearchResult/similarity score container.jsx";
import RegisteredSimilarityScoreText from "./searchPage/registeredSearchResult/similarity score text.jsx";

// searchResult components
import MatchCardContainer from "./searchPage/searchResult/match card container.jsx";
import MatchCardExampleImage from "./searchPage/searchResult/match card example image.jsx";
import MatchCardImageBorder from "./searchPage/searchResult/match card image border.jsx";
import MatchCardNamePillText from "./searchPage/searchResult/match card name pill text.jsx";
import MatchCardNamePill from "./searchPage/searchResult/match card name pill.jsx";
import MatchCardSampleImage from "./searchPage/searchResult/match card sample image.jsx";
import MatchCardStateAndDecade from "./searchPage/searchResult/match card state and decade.jsx";
import SimilarityScoreContainer from "./searchPage/searchResult/similarity score container.jsx";
import SimilarityScoreText from "./searchPage/searchResult/similarity score text.jsx";

// user card components
import UsercardCityAndState from "./searchPage/userCard/usercard city and state.jsx";
import UsercardContainer from "./searchPage/userCard/usercard container.jsx";
import UsercardExampleImage from "./searchPage/userCard/usercard example image.jsx";
import UsercardImageBorder from "./searchPage/userCard/usercard image border.jsx";
import UsercardNamePillText from "./searchPage/userCard/usercard name pill text.jsx";
import UsercardNamePill from "./searchPage/userCard/usercard name pill.jsx";

// ✅ Register components
registerComponent(UserCard, {
  name: "UserCard",
  props: {},
  meta: { importPath: "./searchPage/UserCard" }
});

registerComponent(SearchPage, {
  name: "SearchPage",
  props: {},
  meta: { importPath: "./searchPage/SearchPage" }
});

registerComponent(SearchResult, {
  name: "SearchResult",
  props: {},
  meta: { importPath: "./searchPage/SearchResult" }
});

registerComponent(SearchResultsPage, {
  name: "SearchResultsPage",
  props: {},
  meta: { importPath: "./searchPage/SearchResultsPage" }
});

registerComponent(RegisteredMatchCardCityAndState, {
  name: "RegisteredMatchCardCityAndState",
  props: {},
  meta: { importPath: "./searchPage/registeredSearchResult/match card city and state" }
});

registerComponent(RegisteredMatchCardBadgePill, {
  name: "RegisteredMatchCardBadgePill",
  props: {},
  meta: { importPath: "./searchPage/registeredSearchResult/registered match card badge pill" }
});

registerComponent(RegisteredMatchCardBadgeText, {
  name: "RegisteredMatchCardBadgeText",
  props: {},
  meta: { importPath: "./searchPage/registeredSearchResult/registered match card badge text" }
});

registerComponent(RegisteredMatchCardContainer, {
  name: "RegisteredMatchCardContainer",
  props: {},
  meta: { importPath: "./searchPage/registeredSearchResult/registered match card container" }
});

registerComponent(RegisteredMatchCardImageBorder, {
  name: "RegisteredMatchCardImageBorder",
  props: {},
  meta: { importPath: "./searchPage/registeredSearchResult/registered match card image border" }
});

registerComponent(RegisteredMatchCardNamePillText, {
  name: "RegisteredMatchCardNamePillText",
  props: {},
  meta: { importPath: "./searchPage/registeredSearchResult/registered match card name pill text" }
});

registerComponent(RegisteredMatchCardNamePill, {
  name: "RegisteredMatchCardNamePill",
  props: {},
  meta: { importPath: "./searchPage/registeredSearchResult/registered match card name pill" }
});

registerComponent(RegisteredMatchCardSampleImage, {
  name: "RegisteredMatchCardSampleImage",
  props: {},
  meta: { importPath: "./searchPage/registeredSearchResult/registered match card sample image" }
});

registerComponent(RegisteredSimilarityScoreContainer, {
  name: "RegisteredSimilarityScoreContainer",
  props: {},
  meta: { importPath: "./searchPage/registeredSearchResult/similarity score container" }
});

registerComponent(RegisteredSimilarityScoreText, {
  name: "RegisteredSimilarityScoreText",
  props: {},
  meta: { importPath: "./searchPage/registeredSearchResult/similarity score text" }
});

registerComponent(MatchCardContainer, {
  name: "MatchCardContainer",
  props: {},
  meta: { importPath: "./searchPage/searchResult/match card container" }
});

registerComponent(MatchCardExampleImage, {
  name: "MatchCardExampleImage",
  props: {},
  meta: { importPath: "./searchPage/searchResult/match card example image" }
});

registerComponent(MatchCardImageBorder, {
  name: "MatchCardImageBorder",
  props: {},
  meta: { importPath: "./searchPage/searchResult/match card image border" }
});

registerComponent(MatchCardNamePillText, {
  name: "MatchCardNamePillText",
  props: {},
  meta: { importPath: "./searchPage/searchResult/match card name pill text" }
});

registerComponent(MatchCardNamePill, {
  name: "MatchCardNamePill",
  props: {},
  meta: { importPath: "./searchPage/searchResult/match card name pill" }
});

registerComponent(MatchCardSampleImage, {
  name: "MatchCardSampleImage",
  props: {},
  meta: { importPath: "./searchPage/searchResult/match card sample image" }
});

registerComponent(MatchCardStateAndDecade, {
  name: "MatchCardStateAndDecade",
  props: {},
  meta: { importPath: "./searchPage/searchResult/match card state and decade" }
});

registerComponent(SimilarityScoreContainer, {
  name: "SimilarityScoreContainer",
  props: {},
  meta: { importPath: "./searchPage/searchResult/similarity score container" }
});

registerComponent(SimilarityScoreText, {
  name: "SimilarityScoreText",
  props: {},
  meta: { importPath: "./searchPage/searchResult/similarity score text" }
});

registerComponent(UsercardCityAndState, {
  name: "UsercardCityAndState",
  props: {},
  meta: { importPath: "./searchPage/userCard/usercard city and state" }
});

registerComponent(UsercardContainer, {
  name: "UsercardContainer",
  props: {},
  meta: { importPath: "./searchPage/userCard/usercard container" }
});

registerComponent(UsercardExampleImage, {
  name: "UsercardExampleImage",
  props: {},
  meta: { importPath: "./searchPage/userCard/usercard example image" }
});

registerComponent(UsercardImageBorder, {
  name: "UsercardImageBorder",
  props: {},
  meta: { importPath: "./searchPage/userCard/usercard image border" }
});

registerComponent(UsercardNamePillText, {
  name: "UsercardNamePillText",
  props: {},
  meta: { importPath: "./searchPage/userCard/usercard name pill text" }
});

registerComponent(UsercardNamePill, {
  name: "UsercardNamePill",
  props: {},
  meta: { importPath: "./searchPage/userCard/usercard name pill" }
});

export default function PlasmicHost() {
  return <PlasmicCanvasHost />;
}
