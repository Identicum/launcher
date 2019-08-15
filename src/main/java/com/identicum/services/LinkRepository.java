package com.identicum.services;

import java.util.List;
import java.util.Set;

import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.CrudRepository;

import com.identicum.models.Link;

public interface LinkRepository extends CrudRepository<Link, Long>{

	// Get links for the user's roles plus PUBLIC links.
	@Query(value="SELECT l FROM Link l  join  Role r on l.id = r.link WHERE r.name = 'PUBLIC' or r.name in (?1) order by l.display")
	Set<Link> getLinksByRoles(Iterable<String> roles);
	
	List<Link> findAllByOrderByDisplayAsc();
}
