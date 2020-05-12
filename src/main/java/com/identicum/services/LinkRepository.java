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

	// Get links for the user's roles plus PUBLIC links that matches given criteria.
	@Query(value="SELECT l FROM Link l  join  Role r on l.id = r.link " +
			      "WHERE (r.name = 'PUBLIC' or r.name in (?1)) " +
					"and lower(l.display) like ?2 " +
			      "order by l.display")
	Set<Link> getLinksByQueryAndRoles(Iterable<String> roles, String query);
	
	List<Link> findAllByOrderByDisplayAsc();
}
