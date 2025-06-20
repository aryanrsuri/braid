from src.sample import Sample
from src.actor import Actor
from src.event import *
from util.log import Log

if __name__ == "__main__":
    base_log = Log("base_log")
    
    with base_log.trace("create_actor"):
        actor = Actor(name="test_actor", description="for purposes of testing", tags=["test", "xrd"])

    with base_log.trace("create_materials"):
        material_1 = Material(
            name="dopant_Cu",
            description="Copper dopant for Cathode",
            tags=["cathode", "Cu", "dopant"],
            log=base_log,
        )
        material_2 = Material(
            name="dopant_Zr",
            description="Zirconium dopant for Cathode",
            tags=["cathode", "Zr", "dopant"],
            log=base_log,
        )
        base_log.info("materials created",
                      materials={
                          "material_1": material_1.name,
                          "material_1_id": material_1.id,
                          "material_2": material_2.name,
                          "material_2_id": material_2.id,
                      })

    with base_log.trace("mix_dopants"):
        ingr1 = UnspecifiedAmountIngredient(material=material_1)
        ingr2 = UnspecifiedAmountIngredient(material=material_2)
        action = Action(
            name="dopant_mix",
            description="Mixing dopants for cathode",
            tags=["cathode", "mix", "dopant"],
            actor=actor,
            ingredients=[ingr1, ingr2],
            log=base_log,
        )
        action.add_upstream(material_1)
        action.add_upstream(material_2)
        base_log.info("action created", action_name=action.name, action_id=action.id)

    with base_log.trace("generate_material"):
        gen_material = action.generate_generic_material()
        base_log.info("generic material generated",
                      generated_material=gen_material.name,
                      generated_material_id=gen_material.id)

    with base_log.trace("measure_conductivity"):
        measurement = Measurement(name="Conductivity Test", material=gen_material, actor=actor, log=base_log)
        base_log.info("Created measurement", measurement_name=measurement.name, material=gen_material.name)

    with base_log.trace("analyze_conductivity"):
        analysis = Analysis(name="Conductivity Analysis", actor=actor, measurements=[measurement], log=base_log)
        base_log.info("Created analysis", analysis_name=analysis.name)

    material_1.log.info("Material mat1 is ready")
    action.log.info("Action started")
    measurement.log.info("Measurement taken")
    analysis.log.info("Analysis complete")

    base_log.info("Action validity check", action=action.name, is_invalid=action.invalid())
    with base_log.trace("create_material", material="dopant_Cu") as span:
        mat = Material(name="dopant_Cu", log=base_log)
        base_log.info("material created", material_id=mat.id)

    with base_log.trace("run_synthesis", actor=actor.name, actor_id=actor.id) as span:
        from time import sleep
        sleep(1)  
        base_log.info("synthesis completed", actor=actor.name, actor_id=actor.id)


    base_log.info("Sample creation started")
    with base_log.trace("create_sample") as span:
        timec = time_ns() // 1_000
        sample = Sample(name=f"sample_{timec}", description="Sample for testing purposes", tags=["test", "sample"], log=base_log)
        sample.add_event(action)
        sample.add_event(measurement)
        sample.add_event(analysis)
        sample.save()
        base_log.info("Valid graph?", is_valid=sample.valid_graph())
        base_log.info("Sample created", sample_name=sample.name, sample_id=sample.id)
        print("sample is valid?", sample.valid_graph()) 
        sample.plot_graph()
        for event in sample.events:
            # print with formatting
            print(f"Event in sample: {event.id}, {event.name}, {event.type}")
            

            base_log.info("Event in sample", event_id=event.id, event_name=event.name, event_type=event.type)

