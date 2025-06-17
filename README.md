# Braid is a framework for intergration human and robotic operators for self driving labs

## Manifest

Braid is a framework for integrating human and robotic operators for self-driving labs. It provides a structured way to represent and manage scientific processes, focusing on the lifecycle of samples and their associated events. Braid is designed to be flexible, extensible, and capable of handling complex workflows in laboratory environments.


## Architecture

Braid (graph), represents a `sample` as a [directed acyclic graph](https://en.wikipedia.org/wiki/Directed_acyclic_graph) which consists of various node types to fully describe a unique process and serial. This architecture is heavily inspired by [LabGraph](https://labgraph.readthedocs.io/en/latest/schema.html)

## Constructs

The Glossary of constructs is:

Application Layer

- User
- Group (Set of Users)
- Location
- Project
- Experiment
- Status
- Task
- Tag(s)
- Data Lake
- Logging
- Inventory:
  - All Material
  - All Ingredients
  - Vendor
- Ingredient
- Up/Down stream
- Handoff
- Queueing

Data Layer

- Sample
  - Event:
    - Type:
      - Material
      - Action
      - Measurement
      - Analysis
    - Parameters
    - Edges:
      - Action    -> Material -< Action/Measurement
      - Material  -> Action -< Material
      - Material  -> Measurement -< Analysis
      - Measurement/Analysis -> Analysis -< Analysis
- Actor
- AnalysisMethod
- View:
  - Sample
  - Event
  - Actor

### Actor

A versioned and defined representation of a phsyical device or container where events occur. This should contain the *driver* (e.g. PLC) of the device if so required. An Action or Measurement must be associated with an actor. Actors _start_ the associated action/measurement and thus become `OCCUPIED` with the sample, or `LOCKED` in preperation for the sample. If no samples occupy or lock the actor, it is deemed `IDLE` or `ERRORED`.

Actors are physical entities, so four furnaces in a lab represents four distinct actors. Actors can be _versioned_ (service, modification, PLC update, driver code update, etc) and that history can be tracked

### Sample

A sample is a set of events that form a directed acyclic graph, i.e. a process to form and measure material(s). The nodes of the sample are deemed `events` of four types: Material, Action, Measurement, and Analysis. Each event has a grammar that details what it is and the edges these events can produce.

### Event

#### Material

A _material_ is an event created by an _action_ that represents a physical material in a phsyical state, materials can feed a new action, and/or feed a measuremnt to yield raw data.

Examples of a material are: Zirconia dopant, Thermo Fischer HCL 0.05%, Intermediate Mixture (of two materials from an action), Anode, Cathode, Coin Cell, etc... 

#### Action

An _action_ is an event performed by an _actor_ that bridges or "generating" material(s). Each _action_ produces a material, even if that material does not get measured. 

Examples of a material are: Procurement, Mix, Heat, Electrode Casting, Elecrolyte Fill, Fabrication, etc...

#### Measurement

A measurement is an event that yields raw data for some _material_. Thus, only _analysis_ events can follow a measurement. A measurement's set of parameters detail the _procedure_ 

Examples of a measurement are: X-ray diffraction, C/10 Coin Cell Cycling, etc...

#### Analysis

An analysis event performed through an _AnalysisMethod_ analyses a _measurement_ or other _analysis_ event. 

### Parameters

Every abstraction in the schema requires a set of parameters that dictacts the logic of the abstraction. The two types of parameter are schematic, i.e represent fields needed to construct the data layer (timestamp or name parameter for example), and some are event scoped, and represent fields a user details to distinguish one event from another (e.g. hcl_mix_temp: 230)

#### Shared, Schematic Parameters
- (mandatory) name
- global id 
- global position 
- versionstamp 
- timestamp
- description
- tags
- status

## Artifacts

### Example of hierarchy 

```ini

[Charter]
Material_Type=Solid_State_Battery
Location=Palo_Alto_CA
Project=Pheonix_First
Experiment=High_Temp_Dopant_Sweep

[Example]
Human_Readable_Sample_Name=SSB.PF.HTDS:fC001

```



