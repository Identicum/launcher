package com.identicum.config;

import com.identicum.models.Link;
import com.identicum.models.Role;

import java.util.ArrayList;
import java.util.List;

public class ModelsDto {

    private List<Link> links = new ArrayList<>();

    public List<Link> getLinks() {
        return links;
    }

    public void setLinks(List<Link> links) {
        this.links = links;
    }
}
