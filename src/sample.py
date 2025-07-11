from util.versionstamp import versionid, versionstamp
from time import time_ns
from util.log import Log
from src.event import BaseEvent, Material, Action, Measurement, Analysis, WholeIngredient
from typing import List, Optional, Dict, Any
from src.experiment import Experiment
from util.status import Status
import networkx as nx


vm = versionstamp()
allowed_events = Material | Action | Measurement | Analysis

class Sample:
    def __init__(
        self,
        experiment: Experiment,
        name: Optional[str] = None,
        description: str = "",
        events: List[allowed_events] = [],
        status: Status = Status.PENDING,
        tags: List[str] = [],
        log: Optional[Log] = None,
        **contents: Any
    ):
        self.description = description
        self.tags = tags
        self._contents = contents
        self.created_at = time_ns() // 1_000
        self.updated_at = None
        self.id = vm()
        self.experiment = experiment
        self.events = []
        self.status = status

        if events is not None:
            for event in events:
                self.add_event(event)

        self.name = self.generate_sample_name(name)
        self.log = (log or Log(self.name)).with_context(
            sample_name = self.name,
            sample_id = self.id,
            events = [event.id for event in self.events] if self.events else []
        )

    def generate_sample_name(self, name: Optional[str]) -> str:
        if name:
            return name
        # Format: 3 digits Lab code 3 digits experiment code . 3 digit project code : 6 digits timestamp + 2 random
        # FIXME: Perf improvements here
        lab_code = self.experiment.lab.code[:3].upper()
        exp_code = self.experiment.id[:3].upper()
        project_code = self.experiment.project.id[:3].upper()
        timestamp = str(time_ns() // 1_000_000)[-6:]  # Last 6 digits of the timestamp
        random_suffix = str(vm())[-2:]
        name = f"{lab_code}{exp_code}.{project_code}:{timestamp}{random_suffix}"
        return name




    def add_event(self, event: allowed_events):
        if not isinstance(event, allowed_events):
            self.log.error(f"Event must be of type {allowed_events.__name__}, got {type(event).__name__}")
            raise TypeError(f"Event must be of type {allowed_events.__name__}")
        if event in self.events:
            return
        self.events.append(event)
        self.updated_at = time_ns() // 1_000

    def to_dict(self, include_events: bool = True) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "contents": self._contents
        }
        if include_events:
            data["events"] = [event.to_dict() for event in self.events]
        return data
    # TODO: from_dict method

    def __repr__(self):
        return f"Sample(name={self.name}, id={self.id}, created_at={self.created_at})"

    def save(self):
        # TODO: Implement save logic to persist sample data
        self.updated_at = time_ns() // 1_000
        return None

    def graph(self):
        graph = nx.DiGraph()
        for event in self.events:
            event: BaseEvent # This type hint is correct, event is a BaseEvent
            graph.add_node(event.id, type=event.type, name=event.name)
            for upstream_event in event.upstream: # Renamed `upstream` to `upstream_event` for clarity
                # Access attributes directly, not as dictionary keys
                if upstream_event.id not in graph.nodes:
                    graph.add_node(upstream_event.id, type=upstream_event.type, name=f"outside_event")
                graph.add_edge(upstream_event.id, event.id, type=upstream_event.type)

            for downstream_event in event.downstream: # Renamed `downstream` to `downstream_event` for clarity
                # Access attributes directly, not as dictionary keys
                if downstream_event.id not in graph.nodes:
                    graph.add_node(downstream_event.id, type=downstream_event.type, name=f"outside_event")
                graph.add_edge(event.id, downstream_event.id, type=downstream_event.type)
        return graph

    def valid_graph(self) -> bool:
        is_acyclic = nx.is_directed_acyclic_graph(self.graph())
        connected = len(list(nx.connected_components(self.graph().to_undirected()))) == 1
        return is_acyclic and connected


    def add_linear_sample_process(self, actions: List[Action]):
        for action in actions[:-1]:
            if len(action.gen_materials) > 1:
                self.log.error("Action must generate a single or no material for linear sample process")
                raise ValueError("Action must generate a single or no material for linear sample process")
        for a_0, a_1 in zip(actions, actions[1:]):
            if len(a_1.ingredients) == 0:
                continue
            if not any([
                ingredient.material in a_0.gen_materials
                for ingredient in a_1.ingredients
                ]):
                self.log.error(f"Action {a_1.name} must use a material generated by the previous action {a_0.name}")
                raise ValueError(f"Action {a_1.name} must use a material generated by the previous action {a_0.name}")
        for ingredient in actions[0].ingredients:
            self.add_event(ingredient.material)
        self.add_event(actions[0])

        for a_0,a_1 in zip(actions, actions[1:]):
            if len(a_0.gen_materials) == 0:
                inter = a_0.generate_generic_material()
            elif len(a_0.gen_materials) == 1:
                inter = a_0.gen_materials[0]
            self.add_event(inter)
            if len(a_1.ingredients) == 0:
                a_1.add_ingredient(WholeIngredient(inter))
            self.add_event(a_1)

        if len(actions[-1].gen_materials) == 0:
            actions[-1].generate_generic_material()
        for final_material in actions[-1].gen_materials:
            self.add_event(final_material)

    def plot_graph(self):
        import matplotlib.pyplot as plt
        pos = nx.spring_layout(self.graph())
        # different color for each type of node

        node_colors = {
            'material': 'lightgreen',
            'action': 'lightcoral',
            'measurement': 'lightblue',
            'analysis': 'lightyellow'
        }
        node_color_map = [node_colors[data['type']] for node, data in self.graph().nodes(data=True)]
        labels = {node: f"{data['name']}\n({data['type']})" for node, data in self.graph().nodes(data=True)}
        nx.draw(self.graph(), pos, with_labels=True, labels=labels, node_size=1000, node_color=node_color_map, font_size=8, font_color='black', arrows=True)
        edge_labels = nx.get_edge_attributes(self.graph(), 'type')
        nx.draw_networkx_edge_labels(self.graph(), pos, edge_labels=edge_labels)
        plt.show()
