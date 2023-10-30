package com.identicum.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.identicum.services.LinkRepository;
import com.identicum.services.RoleRepository;
import com.identicum.models.Link;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;
import java.util.List;

import java.io.*;

@Component
public class DataLoader implements ApplicationRunner {

    private static final Logger logger = LoggerFactory.getLogger(DataLoader.class);

    private static final String DATA_FILENAME = "data.json";

    private LinkRepository linkRepository;
    private RoleRepository roleRepository;

    @Value("${app.homedir:/var/opt/identicum/launcher}")
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
                logger.debug("An initial datafile has been found and it's readable");
                try {
                    this.importData(new FileInputStream(initialData));
                }
                catch(FileNotFoundException fne) {
                    logger.error("It should not happen because file presence is checked before", fne);
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

    public void importData(InputStream data) {
        logger.debug("Entered DataLoader.importData");
        try {
            ObjectMapper objectMapper = new ObjectMapper();
            ModelsDto models = objectMapper.readValue(data, ModelsDto.class);
            List<Link> links = models.getLinks();
            logger.trace("Full list of links: {}", links);
            links.forEach(link -> {
                if (linkRepository.findByTarget(link.getTarget()).size() > 0) {
                    logger.warn("Link with target '{}' already exists. Skipping.", link.getTarget());
                } else {
                    logger.debug("Trying to save link from json: {}", link);
                    linkRepository.save(link);
                    Link linkInDB = linkRepository.findByTarget(link.getTarget()).get(0);
                    logger.debug("Complete link saved in database: {}", linkInDB);
                    logger.trace("List of links in database: {}", linkRepository.findAll());
                }
            });
        } catch (Exception e) {
            logger.error("Error reading links from json", e);
        }
        finally {
            try { data.close(); } catch (IOException e) {
                logger.error("Error closing stream of import file", e);
            }
        }
    }
}
