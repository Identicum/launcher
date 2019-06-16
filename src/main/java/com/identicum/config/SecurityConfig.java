package com.identicum.config;

import org.springframework.boot.autoconfigure.security.oauth2.client.EnableOAuth2Sso;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableGlobalMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter;
import org.springframework.security.oauth2.config.annotation.web.configuration.EnableOAuth2Client;
import org.springframework.security.web.util.matcher.AntPathRequestMatcher;

@Configuration
@EnableWebSecurity
@EnableOAuth2Sso
@EnableOAuth2Client
@EnableGlobalMethodSecurity(prePostEnabled = true)
public class SecurityConfig extends WebSecurityConfigurerAdapter {

    @Override
    public void configure(HttpSecurity http) throws Exception {

    	http.headers().frameOptions().disable();
        http.csrf().disable()
            .authorizeRequests()
        		.antMatchers("/welcome", "/webjars/**", "/css/**").permitAll()
                .anyRequest().authenticated()
                .and().logout()
                	.logoutRequestMatcher(new AntPathRequestMatcher("/logout"))
                	.logoutSuccessUrl("/welcome").permitAll();
    }

}
