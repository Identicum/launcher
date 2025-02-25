resource "keycloak_user" "demo" {
  depends_on     = [ keycloak_realm_user_profile.userprofile ]
  realm_id       = keycloak_realm.realm.id
  username       = "demo"
  enabled        = true
  email          = "demo@identicum.com"
  email_verified = true
  first_name     = "Demo"
  last_name      = "User"
  attributes     = {
    memberOf       = "CN=Launcher_Administrators,OU=groups,OU=meta,DC=sherpa,DC=com##CN=App01,OU=groups,OU=meta,DC=sherpa,DC=com"
  }
  initial_password { value = "demo" }
}
