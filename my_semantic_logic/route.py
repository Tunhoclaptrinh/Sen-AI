# semantic_router/route.py
from typing import Any, Dict, List, Optional


class Route:
    def __init__(
        self,
        name: str,
        samples: List[str],
        filter_dict: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.samples = samples
        # filter_dict dùng để filter MongoDB Atlas Vector Search
        self.filter_dict = filter_dict or {}

    def __repr__(self) -> str:
        return f"Route(name={self.name}, samples={len(self.samples)}, filter={self.filter_dict})"



# from typing import List
# class Route():
#     def __init__(
#         self,
#         name: str = None,
#         samples:List = []
#     ):

#         self.name = name
#         self.samples = samples
 