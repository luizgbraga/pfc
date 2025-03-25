import logging
from abc import ABC, abstractmethod
from typing import Dict, List

import networkx as nx
from rdflib import RDFS, Graph, URIRef


class BaseKnowledgeGraph(ABC):
    """
    Base class for knowledge graph access and manipulation.
    Provides common functionality for different types of knowledge graphs.
    """

    def __init__(self):
        self.rdf_graph = Graph()
        self.nx_graph = None
        self.namespaces = {}

        # Common structures for entities
        self.classes = {}
        self.properties = {}
        self.individuals = {}

        # Logging setup
        self.logger = logging.getLogger(self.__class__.__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    @abstractmethod
    def load_graph(self, source_path: str) -> None:
        """
        Load a knowledge graph from a source.
        Must be implemented by subclasses.

        Args:
            source_path: Path to the knowledge graph source
        """
        pass

    def _extract_namespaces(self) -> None:
        """Extract namespace information from the loaded graph"""
        self.namespaces = dict(self.rdf_graph.namespaces())

    def _get_label(self, uri: URIRef) -> str:
        """Extract the label for a URI, with fallbacks"""
        # Try rdfs:label first
        for label in self.rdf_graph.objects(uri, RDFS.label):
            return str(label)

        # Fall back to the local name
        if "#" in str(uri):
            return str(uri).split("#")[-1]
        else:
            return str(uri).split("/")[-1]

    def _get_comment(self, uri: URIRef) -> str:
        """Extract the comment/description for a URI"""
        for comment in self.rdf_graph.objects(uri, RDFS.comment):
            return str(comment)
        return ""

    @abstractmethod
    def _build_indexes(self) -> None:
        """
        Build indexes of classes, properties, and instances for fast lookup.
        May be customized by subclasses based on ontology structure.
        """
        pass

    @abstractmethod
    def _create_networkx_graph(self) -> None:
        """
        Create a NetworkX representation of the knowledge graph.
        May be customized by subclasses based on ontology structure.
        """
        pass

    def find_entities_by_label(
        self, label: str, partial_match: bool = True, case_sensitive: bool = False
    ) -> List[Dict]:
        """
        Find entities (classes, properties, or individuals) by label

        Args:
            label: The label to search for
            partial_match: Whether to include partial matches
            case_sensitive: Whether to perform case sensitive matching

        Returns:
            List of entities with their metadata
        """
        results = []
        search_label = label if case_sensitive else label.lower()

        for node, attrs in self.nx_graph.nodes(data=True):
            node_label = attrs.get("label", "")
            if not case_sensitive:
                node_label = node_label.lower()

            if (partial_match and search_label in node_label) or (
                search_label == node_label
            ):
                results.append(
                    {
                        "uri": node,
                        "label": attrs.get("label", ""),
                        "type": attrs.get("node_type", ""),
                        "comment": attrs.get("comment", ""),
                    }
                )

        return results

    def get_entity_neighbors(
        self, entity_uri: str, edge_types: List[str] = None
    ) -> Dict:
        """
        Get all connected entities for a given entity

        Args:
            entity_uri: URI of the entity to explore
            edge_types: Optional list of relation types to filter by

        Returns:
            Dictionary with incoming and outgoing connections
        """
        if entity_uri not in self.nx_graph:
            return {"incoming": [], "outgoing": []}

        result = {"incoming": [], "outgoing": []}

        # Get outgoing connections
        for _, target, data in self.nx_graph.out_edges(entity_uri, data=True):
            relation = data.get("relation", "")

            # Apply filter if edge_types is provided
            if edge_types and relation not in edge_types:
                continue

            target_attrs = self.nx_graph.nodes[target]
            result["outgoing"].append(
                {
                    "uri": target,
                    "label": target_attrs.get("label", ""),
                    "type": target_attrs.get("node_type", ""),
                    "relation": relation,
                }
            )

        # Get incoming connections
        for source, _, data in self.nx_graph.in_edges(entity_uri, data=True):
            relation = data.get("relation", "")

            # Apply filter if edge_types is provided
            if edge_types and relation not in edge_types:
                continue

            source_attrs = self.nx_graph.nodes[source]
            result["incoming"].append(
                {
                    "uri": source,
                    "label": source_attrs.get("label", ""),
                    "type": source_attrs.get("node_type", ""),
                    "relation": relation,
                }
            )

        return result

    def get_subgraph(
        self,
        seed_entities: List[str],
        max_depth: int = 2,
        relation_types: List[str] = None,
    ) -> nx.DiGraph:
        """
        Extract a subgraph from the knowledge graph starting from seed entities

        Args:
            seed_entities: List of entity URIs to start exploration from
            max_depth: Maximum distance from seed entities to include
            relation_types: Optional list of relationship types to follow

        Returns:
            NetworkX DiGraph representing the subgraph
        """
        # Validate that seed entities exist in the graph
        valid_seeds = [entity for entity in seed_entities if entity in self.nx_graph]

        if not valid_seeds:
            self.logger.warning("None of the provided seed entities exist in the graph")
            return nx.DiGraph()

        # Create new subgraph
        subgraph = nx.DiGraph()

        # Initialize BFS queue with seed entities and their depth
        queue = [(entity, 0) for entity in valid_seeds]
        visited = set()

        while queue:
            current_entity, depth = queue.pop(0)

            if current_entity in visited:
                continue

            visited.add(current_entity)

            # Add current entity to subgraph
            if current_entity in self.nx_graph:
                attrs = self.nx_graph.nodes[current_entity]
                subgraph.add_node(current_entity, **attrs)

            # Stop if we've reached maximum depth
            if depth >= max_depth:
                continue

            # Process outgoing edges
            for _, target, data in self.nx_graph.out_edges(current_entity, data=True):
                relation = data.get("relation", "")

                # Skip if we're filtering by relation type and this type isn't included
                if relation_types and relation not in relation_types:
                    continue

                # Add this edge to the subgraph
                subgraph.add_edge(current_entity, target, **data)

                # Add target node with its attributes
                target_attrs = self.nx_graph.nodes[target]
                subgraph.add_node(target, **target_attrs)

                # Enqueue target for further exploration if not visited
                if target not in visited:
                    queue.append((target, depth + 1))

            # Process incoming edges
            for source, _, data in self.nx_graph.in_edges(current_entity, data=True):
                relation = data.get("relation", "")

                # Skip if we're filtering by relation type and this type isn't included
                if relation_types and relation not in relation_types:
                    continue

                # Add this edge to the subgraph
                subgraph.add_edge(source, current_entity, **data)

                # Add source node with its attributes
                source_attrs = self.nx_graph.nodes[source]
                subgraph.add_node(source, **source_attrs)

                # Enqueue source for further exploration if not visited
                if source not in visited:
                    queue.append((source, depth + 1))

        return subgraph

    def find_paths(
        self, source_uri: str, target_uri: str, max_length: int = 3
    ) -> List[List[Dict]]:
        """
        Find all paths between two entities up to a maximum length

        Args:
            source_uri: URI of the source entity
            target_uri: URI of the target entity
            max_length: Maximum path length

        Returns:
            List of paths, each path is a list of edge dictionaries
        """
        if source_uri not in self.nx_graph or target_uri not in self.nx_graph:
            return []

        # Find all simple paths within the maximum length
        simple_paths = list(
            nx.all_simple_paths(
                self.nx_graph, source_uri, target_uri, cutoff=max_length
            )
        )

        detailed_paths = []
        for path in simple_paths:
            detailed_path = []

            for i in range(len(path) - 1):
                source = path[i]
                target = path[i + 1]

                # Get edge data
                edge_data = self.nx_graph.get_edge_data(source, target)

                # May have multiple edges between the same nodes
                if isinstance(edge_data, list):
                    for edge in edge_data:
                        detailed_path.append(
                            {
                                "source": source,
                                "source_label": self.nx_graph.nodes[source].get(
                                    "label", ""
                                ),
                                "relation": edge.get("relation", ""),
                                "target": target,
                                "target_label": self.nx_graph.nodes[target].get(
                                    "label", ""
                                ),
                            }
                        )
                else:
                    detailed_path.append(
                        {
                            "source": source,
                            "source_label": self.nx_graph.nodes[source].get(
                                "label", ""
                            ),
                            "relation": edge_data.get("relation", ""),
                            "target": target,
                            "target_label": self.nx_graph.nodes[target].get(
                                "label", ""
                            ),
                        }
                    )

            detailed_paths.append(detailed_path)

        return detailed_paths

    def export_subgraph_for_visualization(self, subgraph: nx.DiGraph = None) -> Dict:
        """
        Export a subgraph (or the full graph) for visualization

        Args:
            subgraph: Optional subgraph to export (defaults to full graph)

        Returns:
            Dictionary with nodes and edges in a format ready for visualization
        """
        graph_to_export = subgraph if subgraph is not None else self.nx_graph

        # Create a visualization-friendly representation
        vis_data = {"nodes": [], "edges": []}

        # Add nodes with their properties
        for node_id, attrs in graph_to_export.nodes(data=True):
            node_type = attrs.get("node_type", "Unknown")

            node_data = {
                "id": node_id,
                "label": attrs.get("label", node_id),
                "title": attrs.get("comment", ""),
                "group": node_type,
            }

            vis_data["nodes"].append(node_data)

        # Add edges
        edge_id = 0
        for source, target, attrs in graph_to_export.edges(data=True):
            relation = attrs.get("relation", "")

            edge_data = {
                "id": f"e{edge_id}",
                "from": source,
                "to": target,
                "label": relation,
                "arrows": "to",
            }

            vis_data["edges"].append(edge_data)
            edge_id += 1

        return vis_data
