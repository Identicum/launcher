# administrator: Launcher_Administrators grants the admin page (ADMIN_ROLE)
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

# regular user: sees PUBLIC links and the links of App02, but not the admin page
resource "keycloak_user" "user" {
  depends_on     = [ keycloak_realm_user_profile.userprofile ]
  realm_id       = keycloak_realm.realm.id
  username       = "user"
  enabled        = true
  email          = "user@identicum.com"
  email_verified = true
  first_name     = "Regular"
  last_name      = "User"
  attributes     = {
    memberOf       = "CN=App02,OU=groups,OU=meta,DC=sherpa,DC=com"
  }
  initial_password { value = "user" }
}
