package com.identicum.models;

import com.fasterxml.jackson.annotation.*;

import java.io.Serializable;

import javax.persistence.*;
import javax.validation.constraints.NotNull;

@Entity
@JsonIdentityInfo(generator = ObjectIdGenerators.PropertyGenerator.class, property = "id")
public class Role implements Serializable {
	
	private static final long serialVersionUID = 3566048646415017879L;

	@Id
	@GeneratedValue(strategy = GenerationType.IDENTITY)
	private Long id;

	@NotNull
	private String name;
	
	@ManyToOne
	@JoinColumn
	@JsonBackReference
	private Link link;
	
	public Long getId() {
		return id;
	}

	public void setId(Long id) {
		this.id = id;
	}

	public Link getLink() {
		return link;
	}

	public void setLink(Link link) {
		this.link = link;
	}

	public String getName() {
		return name;
	}

	public void setName(String name) {
		this.name = name;
	}

	@Override
	public String toString() {
		return "Role{" +
				"id=" + id +
				", name='" + name + '\'' +
				'}';
	}
}
