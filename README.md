# Autonomic Manager (AM)

![Autonomic Manager](docs/imgs/AM.png)


Autonomic Manager (AM) is an innovative toolkit comprising custom, reliable self-X AI technologies and applications. The Autonomic Manager with MAPE-K (Monitor, Analyze, Plan, Execute, Knowledge) methodology is a concept in the field of autonomic computing, which aims to create self-managing systems that can adapt to changing conditions, optimize performance, and maintain system health.

It's based on open-source FIWARE/Apache components, built on top of the [DIDA](https://github.com/Engineering-Research-and-Development/dida) (Digital Industries Data Analytics) platform. The Autonomic Manager has the role of autonomous AI Data pipeline coordinator and decision maker adopting MAPE-K framework and implementing the actual innovation lying on the Self-X capabilities.

It can interact with the applications layer to improve its functionalities and support the AI pipeline processing. The idea is to listen to events coming from context information to identify patterns described by rules, in order to immediately react upon them by autonomously triggering actions.

The selected components to allow that kind of behaviors are:

* [FIWARE Draco](https://github.com/ging/fiware-draco): based on Apache NiFi. NiFi is a data-flow system based on the flow-based concept programming designed to automate the flow of data in systems and support direct and scalable graphics.
* [FIWARE ORION-LD Context Broker (OCB)](https://github.com/FIWARE/context.Orion-LD): an implementation of the Publish/Subscribe Broker Generic Enabler (GE), able to manage the entire lifecycle of context information including updates, queries, registrations, and subscriptions. It's based on NGSI-LD server implementation to manage context information and its availability.
* [PostgreSQL](https://www.postgresql.org/): a multiplatform relational database management system (RDBMS). It's an open-source able to manage distributed application cloud native and compatible with NGSI-LD and FIWARE Draco to archive context information.
* [Apache Airflow](https://airflow.apache.org/): an open-source workflow management platform. Creating Airflow allow to programmatically author and schedule workflows and monitor them via the built-in Airflow user interface. It's written in Python, and workflows are created via Python scripts.
* [FIWARE KeyRock](https://github.com/FIWARE-GEs/keyrock): a FIWARE component for Identity Management. Using KeyRock (in conjunction with other security components such as PEP Proxy and Authzforce) it adds OAuth2-based authentication and authorization security to services and applications.
* [FIWARE Wilma Pep Proxy](https://github.com/ging/fiware-pep-proxy): combined with Keyrock, it enforces access control to OCB. This means that only permitted users will be able to access OCB entities based on specific permissions and policies.

![AM architecture](docs/imgs/Autonomic_Manager.png)

## Documentation Contents

* [Main functionalities](docs/mainFunctionalities.md)
* [Useful tools](docs/usefulTools.md)
* [Requirements](docs/requirements.md)
* [How to run](docs/howToRun.md)
* [How to Setup Idm](docs/howToSetupIdm.md)
* [Extend the AM](docs/extendAM.md)

Autonomic Manager has received funding from the European Union's HORIZON-CL4-20-21-TWIN-TRANSITION-01 programme under grant agreements No 10.1058715 <https://s-x-ai-project.eu/>.