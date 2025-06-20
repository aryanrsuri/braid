from src.sample import Sample
from src.actor import Actor
from src.event import *
from util.log import Log

log = Log("base_log")
with log.trace("create_sample"):
    operator = Actor(
        name="Operator",
        description="Operator for the lab",
        tags=["operator", "lab"],
        log=log,
    )

    m0 = Material(
        name="Titanium Dioxide",
        formula="TiO2",
        log=log,
    )

    p0 = Action(
        name="procurement",
        gen_materials=[m0],
        actor=operator,
        log=log,
    )
        

    p1 = Action(
        "grind",
        ingredients=[
            Ingredient(
                material=m0,
                amount=1,
                unit="g",
            )
        ],
        log=log,
        actor=operator,
    )

    aeris = Actor(
        name="Aeris X-ray Diffraction",
        description="X-ray diffraction instrument for material characterization",
        tags=["XRD", "Aeris"],
        log=log,
    )
    tubefurnace1 = Actor(
        name="Tube Furnace 1",
        description="High-temperature tube furnace for sintering",
        tags=["furnace", "sintering"],
        log=log,
    )

    cnn_phaseID = Actor(
        name="CNN Phase Identification",
        description="Convolutional Neural Network for phase identification from XRD patterns",
        tags=["CNN", "PhaseID"],
        procedure={
            "step_1": "Load XRD data",
            "step_2": "Preprocess data",
            "step_3": "Run CNN model",
            },
        log=log,
    )

    m1 = p1.generate_generic_material()

    p2 = Action("sinter", ingredients=[WholeIngredient(m1)], actor=tubefurnace1)
    m2 = p2.generate_generic_material()

    p3 = Action("grind", ingredients=[WholeIngredient(m2)], actor=operator, final_step=True)
    m3 = p3.generate_generic_material()

    me0 = Measurement(
        name="XRD",
        material=m3,
        actor=aeris,
        log=log,
    )

    a0 = Analysis(
        name="Phase Identification", measurements=[me0], actor=cnn_phaseID
        ,log=log,
    )

    

    all_nodes = [p0, m0, p1, m1, p2, m2, p3, m3, me0, a0]

    s = Sample(name="first_sample", events=all_nodes, log=log)
    s.log.info("Sample created", sample_name=s.name, sample_id=s.id)
    for event in s.events:
        print(event)
        print("--" * 10)
        s.log.info("Event added", event_name=event.name, event_id=event.id)
    s.plot_graph()





