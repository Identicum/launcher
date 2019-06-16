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
import com.identicum.models.Role;
import com.identicum.services.LinkRepository;
import com.identicum.services.RoleRepository;

@Controller
@RequestMapping("/admin/links/{linkId}/roles")
@PreAuthorize("hasRole('ROLE_ADMIN')")
public class RolesController {
	
	private final static Logger logger = LoggerFactory.getLogger(RolesController.class);
	
	@Autowired
    LinkRepository linkRepository;
	
	@Autowired
    RoleRepository roleRepository;
	
	private final static String VIEWS_BASE = "/admin/roles";
	
	@GetMapping({"", "/"})
	public String index(@PathVariable("linkId") long linkId, Model model) {
		logger.debug("Enetered RoleController.index");
		Link link = linkRepository.findById(linkId).orElseThrow(() -> new IllegalArgumentException("Invalid link Id:" + linkId));
        model.addAttribute("link", link);
        model.addAttribute("roles", link.getRoles());
        return VIEWS_BASE + "/index";
    }
	
	@GetMapping("/new")
	public String addForm(@PathVariable("linkId") long linkId, Model model, Role role) {
		logger.debug("Enetered RoleController.addForm");
		Link link = linkRepository.findById(linkId).orElseThrow(() -> new IllegalArgumentException("Invalid link Id:" + linkId));
        model.addAttribute("link", link);
        model.addAttribute("action", "/admin/links/" + linkId + "/roles");
        return VIEWS_BASE + "/form";
    }
	
	@PostMapping({"", "/"})
    public String create(@PathVariable("linkId") long linkId, @Valid Role role, BindingResult result, Model model) {
        if (result.hasErrors()) {
            return VIEWS_BASE + "/form";
        }
        Link link = linkRepository.findById(linkId).orElseThrow(() -> new IllegalArgumentException("Invalid link Id:" + linkId));
        role.setLink(link);
        roleRepository.save(role);
        link.getRoles().add(role);
        model.addAttribute("link", link);
        model.addAttribute("roles", link.getRoles());
        return VIEWS_BASE + "/index";
    }
	
	@GetMapping("/{id}")
	public String editForm(@PathVariable("linkId") long linkId, @PathVariable("id") long id, Model model) {
		logger.debug("Enetered RolesController.editForm");
		Role role = roleRepository.findById(id).orElseThrow(() -> new IllegalArgumentException("Invalid role Id:" + id));
        model.addAttribute("link", role.getLink());
        model.addAttribute("role", role);
        model.addAttribute("action", "/admin/links/" + linkId + "/roles/" + id);
        return VIEWS_BASE + "/form";
    }
	
	@PostMapping({"/{id}"})
    public String update(@PathVariable("linkId") long linkId, @PathVariable("id") long id, @Valid Role role, BindingResult result, Model model) {
		Link link = linkRepository.findById(linkId).orElseThrow(() -> new IllegalArgumentException("Invalid link Id:" + linkId));
		role.setLink(link);
		if (result.hasErrors()) {
            return VIEWS_BASE + "/form";
        }
        roleRepository.save(role);
        model.addAttribute("link", link);
        model.addAttribute("roles", link.getRoles());
        return VIEWS_BASE + "/index";
    }
	
	@GetMapping("/{id}/delete")
	public String delete(@PathVariable("linkId") long linkId, @PathVariable("id") long id, Model model) {
		logger.debug("Enetered RolesController.delete");
		Role role = roleRepository.findById(id).orElseThrow(() -> new IllegalArgumentException("Invalid role Id:" + id));
	    roleRepository.delete(role);
	    Link link = linkRepository.findById(linkId).orElseThrow(() -> new IllegalArgumentException("Invalid link Id:" + linkId));
	    model.addAttribute("link", link);
	    model.addAttribute("roles", link.getRoles());
	    return VIEWS_BASE + "/index";
	}

}
