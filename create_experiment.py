from src.task import Task
from src.experiment import Experiment
from util.log import Log
from src.lab import Lab

palo_alto_lab = Lab(
        name="Palo Alot Lab",
        code="PAL",
        location="Palo Alto, CA",
    )

dopants_project = palo_alto_lab.create_project(
        project_name="Dopants in TiO2",
        description="Investigating the effects of various dopants on the properties of TiO2",
        tags=["TiO2", "dopants", "materials science"],
    )



log = Log("base_log")

run_xrd = Task(
        name = "run xrd",
        description = "Run X-ray diffraction on the sample",
        tags = ["XRD", "characterization"],
        event_type="measurement",
        log=log,
        parameter={
            "scan_range": "5-90 degrees",
            "step_size": "0.02 degrees",
            "exposure_time": "10 seconds",
        },
        )

dopant_study = Experiment(
        name="Zr dopant sweep",
        lab=palo_alto_lab,
        log=log,
        project=dopants_project,
        description="Study the effect of Zr doping on TiO2",
        tags=["Zr", "dopant", "TiO2"],
        tasks=[run_xrd],
        )


sam = dopant_study.create_sample(
        description="Sample for Zr dopant study",
        tags=["Zr", "TiO2", "sample"],
    )


print(f"Experiment created: {dopant_study.name} with ID: {dopant_study.id}")
print(f"Sample created: {sam.name} with ID: {sam.id}")
print(f"Lab created: {palo_alto_lab.name} with ID: {palo_alto_lab.id}")
print(f"Project created: {dopants_project.name} with ID: {dopants_project.id}")
print(f"Task created: {run_xrd.name} with ID: {run_xrd.id}")
print("Experiment, Sample, Lab, Project, and Task created successfully.")
