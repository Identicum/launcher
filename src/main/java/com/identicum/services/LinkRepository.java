package com.identicum.services;

import java.util.List;
import java.util.Set;

import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.CrudRepository;

import com.identicum.models.Link;

public interface LinkRepository extends CrudRepository<Link, Long>{

	@Query(value="SELECT l FROM Link l  join  Role r on l.id = r.link WHERE r.name = '*' or r.name in (?1) order by l.display")
	Set<Link> getLinksByRoles(Iterable<String> roles);
	
	List<Link> findAllByOrderByDisplayAsc();
}