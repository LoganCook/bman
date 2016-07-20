#Design

* Person is mainly defined by names.
* Organisation can be any entity which has multiple Persons, e.g. schools, groups.
* An Organisation has Persons and Organisations.
* Organisation receive services through some Persons carry certain roles.
* A Role is defined to a Person in an Organisation. Organisation is required.
* A Person can have multiple roles, therefore belong to multiple Organisation.
* Entities can be linked by Foreign keys in database sense but can also be linked
  though Relationship through predefined RelationshipTypes.
* The main purpose of Relationship is to define flexible links and has very limited
  narrative by RelationshipType: directional labels.
* Services are provided to a Role.
* An Account is used in services to identify a Role and linked to an Organisation which
  can be charged against.
* An Account has `billing organisation` instead of Organisation which means it can be
  paid by another Organisation (this covers visiting Persons, or cooperation).
* Without an Account, received services should be charged to Role's Organisation.
* *Should a Role has multiple Accounts for different services? Should them be bound
  to some scopes: server, domain?*

##Relationship

Relationships can be described as directed graphs. The most common way to
describe a replationship is used to define which entity is the head, which is the tail.
Maybe both directions are equally favoured or only the common one is
preferred. Starts from tail and ends at head. The interpretation depends on the
direction when applied: e.g. forward or backward. The meaning of it can be
displayed by labels. As there are two directions, there are two labels. When
direction is not important, the labels can be identical. Same types of relationships
e.g. root-leaf, should always follow the same pattern. The relationship between a
university and its employees should always have university (Oranisation) as tail,
employees (Persons) as tails. In such way, the queies can be optimised.

0. `name`: parent-child
0. `tail`: entity (object type) of tail node
0. `head`: entiy (object type) of head node
0. `forward`: label read from tail to head
0. `backward`: label read from head to tail

###Examples

* UofA is the parent of all its schools and facuties.
* School A is child of UofA.
* School A is child of facuty A.
* School A hosts org B.
* John Smith works for UofA.
* John Smith is a lecture at School A.
* John Smith supervises Joe Block.

##Roles - a special RelationshipType between Person and Organisation

Role binds a Person to an Organisation during a time period.

###Role manangement
John Smith studied at School of A, UofA as a student between Year A and B. Since
Year C, he has been a staff member of Hospital H. Roles have been changed once:
Student -> Staff member which had email address, role type (RelationshipType) and
organisation changed.

A natural Person cannot apply an account with eRSA. `username` (account name) is only
assigned to a Role and never deleted. The status maybe changed, such as disabled for
a period of time. Even `username` is an attrbute of a Role, it is construed for a
Person based on Person's information. It is one of unique identifiers of a Person
and kept when `Role` changes.

###Role change events

When a Person's role changes, either `start_date` or `end_date` will change. Change
of email address, username are not a Role change event. Events are:

0. A Person joins an Organisation
0. A Person changes `relationshiptype` within the Organisation
0. Role is terminated: Person left the Organisation

###Queries could be:

0. A social event is going to happen at Organisation A, who should be contacted?
0. What is the status of an account? Only active roles are important.
0. What were the activities of a Person/Role during a period?
0. Between Year A.1 and Year C.2, what did John Smith do?
   0. Changed role - one event
   0. Activities have to be split for two roles he held when reported back.

##Services

Simple services provides only access to systems. The instances only need to link
to Roles. A Role should have an account for the service. A role by current design
can have multiple accounts even now one role has only one account.

Currently the simple access services are:

* HPC
* Storage

Services which need more properties to define an instances have dedicated models.
Currently:

* RDS
* Nectar: cloud computing

Nectar projects (`https://keystone.rc.nectar.org.au:5000/v3/projects/openstack_id`)
can have multiple managers. For billing purpose, only one manager is treated as the
contractor in this system. The rest of information in regarding to Nectar projects
can be retrieved through its `openstack_id` on Nectar.

###Queries could be:

0. What are the services a Person can access?
0. What are the properties of a service to a Person?
0. What are the services an Organisation have?

##Urls

For api access, define urls after /api/ with proper methods and object types:

  * read one object with id or objects: get /api/object_types/(id)
  * update one object: put /api/object_types/id some json data
  * delete one object: delete /api/object_types/id some json data
  * create one or more objects: post /api/object_types/  some json data {}

For interactive access in browser, define urls after:

  * for accessing objects: /objects/types/(id)
  * for accessing form to create: /form/types/

##Notes

0. Ignore migrations until models are stable and deployed.
0. Should consider a way of saving random information of an object. For example:
   contractor person of Nectar service has `openstack_id`. Currently, it has not
   be saved any where.
0. Event handlers have not been conceptually developed. Singals will be used and
   currently they arecommented out.
0. To be considered:
    * Biller - a role object for billing purpose - send to
    * Invoices and their management: export to csv, pdf, pulling in other information from system like Xero
    * Prices and their history
0. Provide a better price if some one bundle multiple services together. Bundled catalog
   which include not only one catalog item. In such case, containing catalog's price
   will invalid the included catalog items. Most likely, the unit will be meaningless:
   4 VMs with 1TB storage.

