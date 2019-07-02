package com.identicum.config;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.security.oauth2.resource.AuthoritiesExtractor;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.AuthorityUtils;
import org.springframework.stereotype.Component;

import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

@Component
public class OAuthAuthoritiesExtractor implements AuthoritiesExtractor {
	private static final Logger logger = LogManager.getLogger();

	@Value("${app.roles.regex}")
	private String rolesRegex;

	@Override
	public List<GrantedAuthority> extractAuthorities(Map<String, Object> map) {
		logger.debug("Received map: {}", map);
		return this.readLdapGroups(map);
	}

	@SuppressWarnings("unchecked")
	private List<GrantedAuthority> readLdapGroups(Map<String, Object> userData) {
		Pattern groupPattern = Pattern.compile(this.rolesRegex);
		List<String> authorities = new ArrayList<>();
		Object memberOf = userData.get("member_of");
		if( memberOf != null) {
			List<String> ldapGroups = new ArrayList<String>();
			if(memberOf instanceof List) {
				ldapGroups = (List<String>) memberOf;
			}
			else {
				ldapGroups.add(memberOf.toString());
			}
			for(String ldapGroup : ldapGroups)
			{
				logger.debug("Parsing received group: {}", ldapGroup);
				Matcher matcher = groupPattern.matcher(ldapGroup);
				if(matcher.find()) {
					logger.debug("Adding role: {}", matcher.group(1));
					authorities.add( "ROLE_" + matcher.group(1).toUpperCase() );
				}
				else {
					logger.debug("Skipped group: {}", ldapGroup);
				}
			}
		}
		if( authorities.isEmpty() ) {
			logger.debug("No permissions found on token for app regex [{}].", this.rolesRegex);
			return AuthorityUtils.NO_AUTHORITIES;
		}
		else {
			logger.debug("Returning authorities: {}",  authorities);
			return AuthorityUtils.createAuthorityList(authorities.toArray(new String[0]));
		}
	}
}
