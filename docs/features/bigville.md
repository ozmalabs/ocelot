# Bigville integration

Bigville is a separate project and repository:

<https://github.com/ozmalabs/bigville>

Its standalone checkout is `/home/matt/ozmadev/bigville` in the development
workspace. It owns the village world, domain data, seeds, agent backends,
game client, assets, reports, and Bigville-specific tests.

Ocelot is the substrate project. It no longer owns a second Bigville world or
viewer. Any future Ocelot integration belongs at an explicit backend or graph
adapter boundary; it must not import Bigville's implementation back into the
substrate repository.

The historical design and experiment notes remain under
`docs/research/bigville/` for provenance. They are documentation, not a second
runtime implementation.
