from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, TypeVar


class SubGenotype(ABC):
    @abstractmethod
    def serialize_to_dict() -> Dict[Any, Any]:
        pass

    @abstractmethod
    def deserialize_from_dict(self, serialized: Dict[Any, Any]):
        pass
