package com.identicum.services;


import org.springframework.data.repository.CrudRepository;
import com.identicum.models.Role;

public interface RoleRepository extends CrudRepository<Role, Long>{

}