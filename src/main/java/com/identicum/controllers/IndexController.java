package com.identicum.controllers;

import java.util.*;

import com.fasterxml.jackson.databind.Module;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.module.SimpleModule;
import com.identicum.config.LinkSimpleSerializer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.oauth2.provider.OAuth2Authentication;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import com.identicum.models.Link;
import com.identicum.services.LinkRepository;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseBody;

@Controller
public class IndexController {

	private final static Logger logger = LoggerFactory.getLogger(IndexController.class);

	@Autowired
    LinkRepository linkRepository;

	@SuppressWarnings("unchecked")
	@GetMapping({"", "/", "/menu"})
	public String launchpad(Model model, OAuth2Authentication auth ) {
		logger.debug("Entered IndexController.launchpad");
		Map<String, Object> details = (HashMap<String, Object>)auth.getUserAuthentication().getDetails();
    	logger.info("User details --> {}", details);
		logger.info("User roles --> {}", this.getUserRoles(auth));

    	Set<Link> links =  linkRepository.getLinksByRoles(this.getUserRoles(auth) );
    	String userName = details.get("given_name") + " " + details.get("family_name");
    	logger.debug("Total links found for {}: {}", userName, links);
		model.addAttribute("links", links);
		logger.debug("User attrs: given_name({}) - family_name({}) - userName({})", details.get("given_name"), details.get("family_name"), userName);
    	model.addAttribute("name", userName);
		return "launcher";
	}

	@GetMapping("/links/search")
	@ResponseBody
	public ResponseEntity<Object> search(@RequestParam("query") Optional<String> query, OAuth2Authentication auth) {
		logger.debug("Entered IndexController.search with query: {}", query.orElse(""));
		List<String> userRoles = this.getUserRoles(auth);
		String sqlQuery = "%" + query.orElse("") + "%";
		Set<Link> links = linkRepository.getLinksByQueryAndRoles(userRoles, sqlQuery.toLowerCase());

		ObjectMapper mapper = new ObjectMapper();
		SimpleModule module = new SimpleModule();
		module.addSerializer(Link.class, new LinkSimpleSerializer());
		mapper.registerModule(module);
		return ResponseEntity.ok( mapper.valueToTree( links ));
	}

	private List<String> getUserRoles(OAuth2Authentication auth) {
		logger.debug("Entered IndexController.getUserRoles");
		Map<String, Object> details = (HashMap<String, Object>)auth.getUserAuthentication().getDetails();
		logger.debug("User details --> {}", details);
		if( details.containsKey("member_of")) {

			if(details.get("member_of") instanceof List) {
				logger.debug("Getting links for roles {}", details.get("member_of"));
				return (ArrayList<String>)details.get("member_of");
			}
			else {
				logger.debug("Getting links for role {}", details.get("member_of").toString());
				return Arrays.asList( details.get("member_of").toString());
			}
		}
		return new ArrayList<String>();
	}
}
