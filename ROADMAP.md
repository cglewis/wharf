# Wharf Next Steps:

This is a high level overview of the direction I would like to take Wharf next.


## Persistence

For Wharf to be usable outside just an experiment or prototype, it needs to be able to let services persist, and with that the data associated with the services via Docker Volumes.  Along with persisting the idea of a user being able to manage the services that were spun up also needs to be better addressed that Wharf currently handles.


## Sharing

Ideally Wharf should enable services to be publicly accessible, restricted to certain users or groups, or complately private.  Currently Wharf makes all service completely wide open for all.


## Custom Configurations

Unfortunately due to the nature of building images on Docker, having custom configurations for each service for each user is not as straight forward as it might seem.  This enhancement should leverage the Docker ADD command and make the files that are being added to the service accessible to the user for changes prior to building.


## Scale Out

Wharf currently does not support being able to scale out to a cluster of Wharf machines, this would need to be addressed to allow large deployments.


## Trusted Services

Some means for doing trusted builds, that are official, and guaranteed to work.


## Keep Services Updated

Services need to be kept up to date, whether via Github commits/tags/releases, or through some other means periodic updates.  Also sync up for when Dockerfiles change, the build should also be updated accordingly.


## Version of Services

Retaining versions of services so that a user can spin up a service in a specific state regardless of updates or version changes.


## Private Services

Along the lines of having services be private, this would enable an image to remain private as well.  This would likely have the same rules set forth as Sharing, for public, specific groups, individuals, or completely private.


## Known Issues

* Currently the Wharf codebase is quite messy (originally written for a Docker hackday).

* There needs to be a way to edit metadata after a service has been added.

* Services should be have the option to edit after they have been created, whether simple metadata changes, build changes, or completely deleting.

* Currently there is no guarantee that a Dockerfile will build a working serivce that exposes a port, the user should be notified one way or the other.
