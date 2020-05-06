package com.identicum.config;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.identicum.Application;
import com.identicum.models.Link;
import com.identicum.models.Role;
import com.identicum.services.LinkRepository;
import com.identicum.services.RoleRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;

import java.io.File;
import java.io.InputStream;
import java.net.URL;
import java.util.List;

@Component
public class DataLoader  implements ApplicationRunner {

    private static final Logger logger = LoggerFactory.getLogger(DataLoader.class);

    private static final String DATA_FILENAME = "data.json";

    private LinkRepository linkRepository;
    private RoleRepository roleRepository;

    @Value("${app.homedir}")
    private String appHomedir;

    @Autowired
    public DataLoader(LinkRepository linkRepository, RoleRepository roleRepository) {
        this.linkRepository = linkRepository;
        this.roleRepository = roleRepository;
    }

    public void run(ApplicationArguments args) {

        if(linkRepository.count() == 0) {
            File initialData = new File(this.appHomedir + File.separator + DATA_FILENAME);
            logger.debug("Repository is empty. Trying to find initial data in file {}", initialData);
            if(initialData.exists() && initialData.canRead()) {
                logger.debug("An initial datafile has benn found and it's readable");
                try {
                    ObjectMapper objectMapper = new ObjectMapper();
                    List<Link> links = objectMapper.readValue(initialData, new TypeReference<List<Link>>() {});
                    links.forEach(link -> {
                        logger.debug("Loading link: {}", link.getDisplay());
                        linkRepository.save(link);
                        link.getRoleNames().forEach(roleName -> {
                            logger.debug("Loading role {} for link: {}", roleName, link.getDisplay());
                            Role role = new Role();
                            role.setName(roleName);
                            role.setLink(link);
                            roleRepository.save(role);
                        });
                    });
                } catch (Exception e) {
                    logger.error("Error serializing link", e);
                }
            }
            else {
                logger.debug("File not found or it can't be read");
            }
        }
        else{
            logger.debug("Database already filled. Skipping initial data loading.");
        }
    }
}
