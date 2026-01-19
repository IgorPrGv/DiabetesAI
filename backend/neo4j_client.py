import os
from typing import Any, Dict, Optional, List
from neo4j import GraphDatabase


class Neo4jClient:
    def __init__(self, uri: str, user: str, password: str):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    @classmethod
    def from_env(cls) -> Optional["Neo4jClient"]:
        uri = os.getenv("NEO4J_URI")
        user = os.getenv("NEO4J_USER")
        password = os.getenv("NEO4J_PASSWORD")
        if not uri or not user or not password:
            return None
        return cls(uri, user, password)

    def close(self) -> None:
        self._driver.close()

    def upsert_food(self, name: str, group: str, nutrients: Dict[str, Any], source: str) -> None:
        with self._driver.session() as session:
            session.run(
                """
                MERGE (f:Food {name: $name})
                SET f.group = $group, f.source = $source
                WITH f
                FOREACH (k IN keys($nutrients) |
                  MERGE (n:Nutrient {name: k})
                  MERGE (f)-[:HAS_NUTRIENT {value: $nutrients[k]}]->(n)
                )
                """,
                name=name,
                group=group,
                source=source,
                nutrients=nutrients,
            )

    def search_foods_by_name(self, term: str, limit: int = 10) -> List[Dict[str, Any]]:
        with self._driver.session() as session:
            result = session.run(
                """
                MATCH (f:Food)
                WHERE toLower(f.name) CONTAINS toLower($term)
                RETURN f.name AS name, f.group AS group, f.source AS source
                LIMIT $limit
                """,
                term=term,
                limit=limit,
            )
            return [dict(record) for record in result]


