package com.identicum.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.autoconfigure.security.oauth2.client.EnableOAuth2Sso;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.oauth2.config.annotation.web.configuration.EnableOAuth2Client;

@Configuration
@EnableWebSecurity
@EnableOAuth2Sso
@EnableOAuth2Client
@EnableGlobalMethodSecurity(prePostEnabled = true)

public class SecurityConfig extends WebSecurityConfigurerAdapter {

	@Value("${idp.end_session_uri}")
	private String end_session_uri;

	@Value("${app.post_logout_uri}")
	private String post_logout_uri;
	@Value("${security.oauth2.client.client-id}")
	private String client_id;

	@Override
    public void configure(HttpSecurity http) throws Exception {
    	http.headers().frameOptions().disable();
        http.csrf().disable()
            .authorizeRequests()
        		.antMatchers("/webjars/**", "/css/**", "/fonts/**", "/imgs/**", "/js/**").permitAll()
                .anyRequest().authenticated()
                .and().logout()
                	.logoutUrl("/logout")
                	.invalidateHttpSession(true)
					.logoutSuccessUrl(end_session_uri+"?post_logout_redirect_uri="+post_logout_uri+"&client_id="+client_id);
	}
}
