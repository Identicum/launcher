package com.identicum.controllers;

import com.identicum.config.DataLoader;
import com.identicum.config.ModelsDto;
import com.identicum.services.LinkRepository;
import com.identicum.services.RoleRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import java.io.IOException;

@Controller
@RequestMapping("/admin/data")
@PreAuthorize("hasRole('ROLE_ADMIN')")
public class DataController {

    private final static Logger logger = LoggerFactory.getLogger(DataController.class);

    @Autowired
    LinkRepository linkRepository;

    @Autowired
    RoleRepository roleRepository;

    @GetMapping("/export")
    public ResponseEntity<ModelsDto> export() {
        ModelsDto models = new ModelsDto();
        linkRepository.findAll().forEach(link -> models.getLinks().add(link));
        return ResponseEntity.ok().body(models);
    }

    @PostMapping("/import")
    public ResponseEntity<String> importJson(@RequestParam("importFile") MultipartFile file, RedirectAttributes redirectAttributes) throws IOException {
        logger.debug("Trying to read json data");
        DataLoader loader = new DataLoader(this.linkRepository, this.roleRepository);
        loader.importData(file.getInputStream());
        logger.debug("Imported json data with no errors !");
        return ResponseEntity.ok().body("{\"status\": \"ok\"}");
    }
}
