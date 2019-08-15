package com.identicum.controllers;

import javax.validation.Valid;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;

import com.identicum.models.Link;
import com.identicum.services.LinkRepository;

@Controller
@RequestMapping("/admin/links")
@PreAuthorize("hasRole('ROLE_ADMIN')")
public class LinksController {

	private final static Logger logger = LoggerFactory.getLogger(LinksController.class);

	@Autowired
    LinkRepository linkRepository;

	private final static String VIEWS_BASE = "/admin/links";

	@GetMapping({"","/"})
    public String index(Model model) {
		logger.debug("Entered LinksController.index");
        model.addAttribute("links", linkRepository.findAllByOrderByDisplayAsc());
        return VIEWS_BASE + "/index";
    }


	@GetMapping("/new")
    public String addForm(Link link) {
        return "admin/links/form";
    }

	@PostMapping({"","/"})
    public String create(@Valid Link link, BindingResult result, Model model) {
        if (result.hasErrors()) {
            return VIEWS_BASE + "/form";
        }
        link.setType("html");
        linkRepository.save(link);
        model.addAttribute("links", linkRepository.findAllByOrderByDisplayAsc());
        return VIEWS_BASE + "/index";
    }

	@GetMapping("/{id}")
	public String editForm(@PathVariable("id") long id, Model model) {
	    Link link = linkRepository.findById(id).orElseThrow(() -> new IllegalArgumentException("Invalid link Id:" + id));
	    model.addAttribute("link", link);
	    return VIEWS_BASE + "/form";
	}

	@PostMapping("/{id}")
	public String update(@PathVariable("id") long id, @Valid Link link, BindingResult result, Model model) {
	    if (result.hasErrors()) {
	        link.setId(id);
	        return VIEWS_BASE + "/form";
	    }
	    // FIX THIS.  Overwrites role or else they get deleted. Received link has empty roles.
	    Link oldLink = linkRepository.findById(id).orElseThrow(() -> new IllegalArgumentException("Invalid link Id:" + id));
	    link.getRoles().addAll( oldLink.getRoles() );
	    linkRepository.save(link);
	    model.addAttribute("links", linkRepository.findAllByOrderByDisplayAsc());
	    return VIEWS_BASE + "/index";
	}

	@GetMapping("/{id}/delete")
	public String delete(@PathVariable("id") long id, Model model) {
	    Link link = linkRepository.findById(id).orElseThrow(() -> new IllegalArgumentException("Invalid link Id:" + id));
	    linkRepository.delete(link);
	    model.addAttribute("links", linkRepository.findAllByOrderByDisplayAsc());
	    return VIEWS_BASE + "/index";
	}

}
