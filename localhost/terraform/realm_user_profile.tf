
resource "keycloak_realm_user_profile" "userprofile" {
    realm_id = keycloak_realm.realm.id
    unmanaged_attribute_policy = "ENABLED"
    attribute {
        name = "email"
        enabled_when_scope = ["offline_access"]
        required_for_roles  = ["user", "admin"]
        required_for_scopes = ["offline_access"]
        permissions {
            view = ["admin", "user"]
            edit = ["admin", "user"]
        }
    }

    attribute {
        name = "username"
        enabled_when_scope = ["offline_access"]
        required_for_roles  = ["user", "admin"]
        required_for_scopes = ["offline_access"]
        permissions {
            view = ["admin", "user"]
            edit = ["admin"]
        }
    }

    attribute {
        name = "firstName"
        enabled_when_scope = ["offline_access"]
        required_for_roles  = [ ]
        required_for_scopes = [ ]
        permissions {
            view = ["admin", "user"]
            edit = ["admin"]
        }
    }

    attribute {
        name = "lastName"
        enabled_when_scope = ["offline_access"]
        required_for_roles  = [ ]
        required_for_scopes = [ ]
        permissions {
            view = ["admin", "user"]
            edit = ["admin"]
        }
    }
}

