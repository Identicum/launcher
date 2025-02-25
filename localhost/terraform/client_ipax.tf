resource "keycloak_openid_client" "ipax" {
  realm_id                        = keycloak_realm.realm.id
  name                            = "ipax"
  client_id                       = "ipax_client_id"
  client_secret                   = "ipax_client_secret"
  access_type                     = "CONFIDENTIAL"
  standard_flow_enabled           = true
  implicit_flow_enabled           = false
  direct_access_grants_enabled    = false
  service_accounts_enabled        = false
  root_url                        = "http://localhost"
  base_url                        = "/"
  valid_redirect_uris             = ["/private/redirect_uri", "/private/info"]
  valid_post_logout_redirect_uris = ["/logoutSuccess.html"]
}

resource "keycloak_openid_client_default_scopes" "ipax_defaultscopes" {
  realm_id       = keycloak_realm.realm.id
  client_id      = keycloak_openid_client.ipax.id
  default_scopes = [  ]
}

resource "keycloak_openid_client_optional_scopes" "ipax_optionalscopes" {
  depends_on      = [ keycloak_openid_client_default_scopes.ipax_defaultscopes ]
  realm_id        = keycloak_realm.realm.id
  client_id       = keycloak_openid_client.ipax.id
  optional_scopes = [ "profile", "email", keycloak_openid_client_scope.launcher.name ]
}

