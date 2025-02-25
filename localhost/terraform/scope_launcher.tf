resource "keycloak_openid_client_scope" "launcher" {
  realm_id               = keycloak_realm.realm.id
  name                   = "launcher_scope"
  include_in_token_scope = true
}

resource "keycloak_openid_user_attribute_protocol_mapper" "launcher_memberof" {
  realm_id            = keycloak_realm.realm.id
  client_scope_id     = keycloak_openid_client_scope.launcher.id
  name                = "member_of"
  user_attribute      = "memberOf"
  claim_name          = "member_of"
  add_to_id_token     = true
  add_to_access_token = true
  add_to_userinfo     = true
  claim_value_type    = "String"
  multivalued         = true
}