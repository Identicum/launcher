package com.identicum.controllers;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.oauth2.provider.OAuth2Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.identicum.models.Link;
import com.identicum.services.LinkRepository;

@Controller
public class IndexController {

	private final static Logger logger = LoggerFactory.getLogger(IndexController.class);

	@Autowired
    LinkRepository linkRepository;

	@GetMapping("/welcome")
	public String welcome() {
		return "welcome";
	}

	@SuppressWarnings("unchecked")
	@GetMapping({"", "/", "/menu"})
	public String launchpad(Model model, OAuth2Authentication auth ) {

    	try {
    		logger.debug("Spring auth: " + new ObjectMapper().writeValueAsString(auth));
    	} catch(JsonProcessingException jpe) {

    	}
		Map<String, Object> details = (HashMap<String, Object>)auth.getUserAuthentication().getDetails();
    	logger.debug("User details --> {}", details);

    	Set<Link> links = null;
    	if( details.containsKey("member_of")) {

        	if(details.get("member_of") instanceof List) {
        		logger.debug("Getting links for roles {}", details.get("member_of"));
        		links = linkRepository.getLinksByRoles( (ArrayList<String>)details.get("member_of") );
        	}
        	else {
        		logger.debug("Getting links for role {}", details.get("member_of").toString());
        		links = linkRepository.getLinksByRoles( Arrays.asList( details.get("member_of").toString() ));
        	}
        }
			String userName = details.get("given_name") + " " + details.get("family_name");
    	logger.debug("Total links found for {}: {}", userName, links);
			model.addAttribute("links", links);
			logger.debug("User attrs: given_name({}) - family_name({}) - userName({})", details.get("given_name"), details.get("family_name"), userName);
    	model.addAttribute("name", userName);
			return "launcher";
	}
}
