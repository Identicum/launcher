resource "keycloak_openid_client" "launcher" {
  realm_id                        = keycloak_realm.realm.id
  name                            = "launcher"
  client_id                       = "launcher_client_id"
  client_secret                   = "launcher_client_secret"
  access_type                     = "CONFIDENTIAL"
  standard_flow_enabled           = true
  implicit_flow_enabled           = false
  direct_access_grants_enabled    = false
  service_accounts_enabled        = false
  root_url                        = "http://localhost:8081"
  base_url                        = "/"
  valid_redirect_uris             = ["/login"]
  valid_post_logout_redirect_uris = ["/logoutSuccess.html"]
}

resource "keycloak_openid_client_default_scopes" "launcher_defaultscopes" {
  realm_id       = keycloak_realm.realm.id
  client_id      = keycloak_openid_client.launcher.id
  default_scopes = [ ]
}

resource "keycloak_openid_client_optional_scopes" "launcher_optionalscopes" {
  depends_on      = [ keycloak_openid_client_default_scopes.launcher_defaultscopes ]
  realm_id        = keycloak_realm.realm.id
  client_id       = keycloak_openid_client.launcher.id
  optional_scopes = [ "profile", "email", keycloak_openid_client_scope.launcher.name ]
}

