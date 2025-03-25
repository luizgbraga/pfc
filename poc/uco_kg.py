import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List

import networkx as nx
from rdflib import OWL, RDF, RDFS, URIRef

from kg import BaseKnowledgeGraph


class UCOKnowledgeGraph(BaseKnowledgeGraph):
    """
    Class for loading and managing the UCO Knowledge Graph.
    Provides a specialized interface for working with the Unified Cyber Ontology.
    """

    def __init__(self):
        super().__init__()

        # UCO namespace definitions
        self.uco_namespaces = {}

    def load_graph(self, uco_repo_path: str) -> None:
        """
        Load a knowledge graph from the UCO repository.

        Args:
            uco_repo_path: Path to the UCO repository root
        """
        self.load_uco_ontology(uco_repo_path)

    def load_uco_ontology(self, uco_repo_path: str) -> None:
        """
        Load the UCO ontology from the repository directory structure.

        Args:
            uco_repo_path: Path to the UCO repository root
        """
        uco_path = Path(uco_repo_path)
        if not uco_path.exists():
            raise FileNotFoundError(f"UCO directory not found: {uco_repo_path}")

        # Main ontology directory
        ontology_dir = uco_path / "ontology"
        if not ontology_dir.exists():
            raise FileNotFoundError(f"Ontology directory not found: {ontology_dir}")

        # Main UCO directory
        uco_ontology_dir = ontology_dir / "uco"
        if not uco_ontology_dir.exists():
            raise FileNotFoundError(
                f"UCO ontology directory not found: {uco_ontology_dir}"
            )

        self.logger.info(f"Loading UCO ontology from {uco_ontology_dir}")

        # Find all the module directories
        module_dirs = [d for d in uco_ontology_dir.iterdir() if d.is_dir()]
        self.logger.info(f"Found {len(module_dirs)} UCO modules")

        # Count the loaded files
        file_count = 0

        # Load the main UCO TTL file first if it exists
        main_uco_file = uco_ontology_dir / "uco.ttl"
        if main_uco_file.exists():
            self.logger.info(f"Loading main UCO file: {main_uco_file}")
            self.rdf_graph.parse(str(main_uco_file), format="turtle")
            file_count += 1

        # Load all TTL files from each module directory
        for module_dir in module_dirs:
            module_name = module_dir.name
            self.logger.info(f"Loading module: {module_name}")

            # Find TTL files in this module
            ttl_files = list(module_dir.glob("*.ttl"))
            self.logger.info(f"Found {len(ttl_files)} TTL files in {module_name}")

            # Load each TTL file
            for ttl_file in ttl_files:
                # Skip checking files (CI artifacts)
                if ttl_file.name.startswith(".check-"):
                    continue

                self.logger.info(f"Loading {ttl_file}")
                try:
                    self.rdf_graph.parse(str(ttl_file), format="turtle")
                    file_count += 1
                except Exception as e:
                    self.logger.error(f"Error loading {ttl_file}: {e}")

            # Check for catalog file for additional import information
            catalog_file = module_dir / "catalog-v001.xml"
            if catalog_file.exists():
                self._process_catalog_file(catalog_file, module_dir)

        # Check for additional ontology files in co/ directory
        co_dir = ontology_dir / "co"
        if co_dir.exists():
            self.logger.info("Loading ontology files from co/ directory")
            for ttl_file in co_dir.glob("**/*.ttl"):
                if not ttl_file.name.startswith(".check-"):
                    self.logger.info(f"Loading {ttl_file}")
                    try:
                        self.rdf_graph.parse(str(ttl_file), format="turtle")
                        file_count += 1
                    except Exception as e:
                        self.logger.error(f"Error loading {ttl_file}: {e}")

        # Extract and register namespaces
        self._extract_namespaces()

        # Build indexes for faster access
        self._build_indexes()

        # Create NetworkX graph
        self._create_networkx_graph()

        self.logger.info(
            f"Loaded {len(self.rdf_graph)} triples from {file_count} files"
        )
        self.logger.info(
            f"Found {len(self.classes)} classes, {len(self.properties)} properties"
        )

    def _extract_namespaces(self) -> None:
        """Extract namespace information from the loaded graph with UCO-specific handling"""
        super()._extract_namespaces()

        # Identify UCO-specific namespaces
        for prefix, namespace in self.namespaces.items():
            ns_str = str(namespace)
            if "unifiedcyberontology" in ns_str or "uco/" in ns_str:
                self.uco_namespaces[prefix] = namespace
                self.logger.debug(f"Found UCO namespace: {prefix}: {namespace}")

    def _process_catalog_file(self, catalog_file: Path, base_dir: Path) -> None:
        """Process a catalog-v001.xml file to find additional imports"""
        try:
            tree = ET.parse(catalog_file)
            root = tree.getroot()

            # Find URI mappings in the catalog
            for child in root:
                if "uri" in child.attrib and "name" in child.attrib:
                    # If URI is a relative file path
                    uri_value = child.attrib["uri"]
                    if not uri_value.startswith(("http://", "https://", "urn:")):
                        # This is a local file reference
                        referenced_file = base_dir / uri_value
                        if referenced_file.exists():
                            self.logger.info(
                                f"Loading catalog reference: {referenced_file}"
                            )
                            try:
                                format_guess = (
                                    "turtle"
                                    if str(referenced_file).endswith(".ttl")
                                    else None
                                )
                                self.rdf_graph.parse(
                                    str(referenced_file), format=format_guess
                                )
                            except Exception as e:
                                self.logger.error(
                                    f"Error loading catalog reference {referenced_file}: {e}"
                                )
        except Exception as e:
            self.logger.error(f"Error processing catalog file {catalog_file}: {e}")

    def _build_indexes(self) -> None:
        """Build indexes of classes, properties, and instances for UCO ontology"""
        # Find all classes
        for cls in self.rdf_graph.subjects(RDF.type, OWL.Class):
            cls_str = str(cls)
            if cls_str not in self.classes:
                self.classes[cls_str] = {
                    "uri": cls,
                    "label": self._get_label(cls),
                    "comment": self._get_comment(cls),
                    "parent_classes": list(
                        self.rdf_graph.objects(cls, RDFS.subClassOf)
                    ),
                }

        # Find all properties
        for prop_type in [
            OWL.ObjectProperty,
            OWL.DatatypeProperty,
            OWL.AnnotationProperty,
        ]:
            for prop in self.rdf_graph.subjects(RDF.type, prop_type):
                prop_str = str(prop)
                if prop_str not in self.properties:
                    self.properties[prop_str] = {
                        "uri": prop,
                        "label": self._get_label(prop),
                        "comment": self._get_comment(prop),
                        "type": prop_type,
                        "domains": list(self.rdf_graph.objects(prop, RDFS.domain)),
                        "ranges": list(self.rdf_graph.objects(prop, RDFS.range)),
                    }

        # Find individuals (instances of classes)
        for cls_uri in self.classes:
            cls = URIRef(cls_uri)
            for indiv in self.rdf_graph.subjects(RDF.type, cls):
                indiv_str = str(indiv)
                if indiv_str in self.classes or indiv_str in self.properties:
                    continue

                if indiv_str not in self.individuals:
                    self.individuals[indiv_str] = {
                        "uri": indiv,
                        "label": self._get_label(indiv),
                        "comment": self._get_comment(indiv),
                        "types": [cls],
                    }
                else:
                    if cls not in self.individuals[indiv_str]["types"]:
                        self.individuals[indiv_str]["types"].append(cls)

    def _create_networkx_graph(self) -> None:
        """Create a NetworkX graph from the RDF data specific to UCO structure"""
        self.nx_graph = nx.DiGraph()

        # Add nodes for classes
        for uri, data in self.classes.items():
            self.nx_graph.add_node(
                uri, label=data["label"], comment=data["comment"], node_type="Class"
            )

        # Add nodes for properties
        for uri, data in self.properties.items():
            self.nx_graph.add_node(
                uri,
                label=data["label"],
                comment=data["comment"],
                node_type="Property",
                property_type=str(data["type"]),
            )

        # Add nodes for individuals
        for uri, data in self.individuals.items():
            self.nx_graph.add_node(
                uri,
                label=data["label"],
                comment=data["comment"],
                node_type="Individual",
            )

        # Add edges for class hierarchies
        for cls_uri, cls_data in self.classes.items():
            for parent in cls_data["parent_classes"]:
                if isinstance(parent, URIRef) and str(parent) in self.nx_graph:
                    self.nx_graph.add_edge(cls_uri, str(parent), relation="subClassOf")

        # Add edges for property domains and ranges
        for prop_uri, prop_data in self.properties.items():
            for domain in prop_data["domains"]:
                if isinstance(domain, URIRef) and str(domain) in self.nx_graph:
                    self.nx_graph.add_edge(prop_uri, str(domain), relation="domain")

            for range_uri in prop_data["ranges"]:
                if isinstance(range_uri, URIRef) and str(range_uri) in self.nx_graph:
                    self.nx_graph.add_edge(prop_uri, str(range_uri), relation="range")

        # Add edges for actual relationships in the data
        for s, p, o in self.rdf_graph:
            # Skip RDF, RDFS and OWL built-in relationships to keep the graph manageable
            if (
                str(p).startswith(str(RDF))
                or str(p).startswith(str(RDFS))
                or str(p).startswith(str(OWL))
            ):
                continue

            # Only add edges between entities that are nodes in our graph
            if isinstance(s, URIRef) and isinstance(o, URIRef):
                s_str, o_str = str(s), str(o)
                if s_str in self.nx_graph and o_str in self.nx_graph:
                    # Get property label
                    prop_label = self._get_label(p)
                    self.nx_graph.add_edge(
                        s_str, o_str, relation=prop_label, uri=str(p)
                    )

    def get_cybersecurity_concepts(self) -> List[Dict]:
        """
        Get concepts specifically related to cybersecurity from the UCO ontology

        Returns:
            List of cybersecurity-related concepts with metadata
        """
        cyber_concepts = []

        # Look for concepts with specific cybersecurity-related terms in their labels or comments
        cyber_terms = [
            "attack",
            "malware",
            "vulnerability",
            "threat",
            "exploit",
            "cyber",
            "security",
            "intrusion",
            "breach",
            "ransomware",
            "phishing",
            "botnet",
            "firewall",
            "encryption",
            "authentication",
            "authorization",
            "backdoor",
            "incident",
            "defense",
            "protection",
            "hack",
            "compromise",
        ]

        for node, attrs in self.nx_graph.nodes(data=True):
            label = attrs.get("label", "").lower()
            comment = attrs.get("comment", "").lower()

            # Check if any cyber term appears in the label or comment
            if any(term in label or term in comment for term in cyber_terms):
                cyber_concepts.append(
                    {
                        "uri": node,
                        "label": attrs.get("label", ""),
                        "type": attrs.get("node_type", ""),
                        "comment": attrs.get("comment", ""),
                    }
                )

        return cyber_concepts
