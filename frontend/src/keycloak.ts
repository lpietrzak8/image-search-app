import Keycloak from "keycloak-js";

const keycloak = new Keycloak({
  url: "http://localhost:8080",
  realm: "photo-search",
  clientId: "photo-search-app",
});

export default keycloak;
