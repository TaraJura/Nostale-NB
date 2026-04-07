from .client_socket import ClientSocket, Request, Response
from .base_client import Client
from typing import TypedDict


class PlayerObjManagerClient(Client):
    def __init__(self, socket: ClientSocket):
        super().__init__("PlayerObjManagerService", socket)

    def get_player_obj_manager(self) -> dict:
        request: Request = {
            "service": self._service_name,
            "method": "getPlayerObjManager",
            "params": {}
        }
        response = self._socket.request(request)
        return response["result"]

    def walk(self, x: int, y: int) -> Response:
        request: Request = {
            "service": self._service_name,
            "method": "walk",
            "params": {"x": x, "y": y}
        }
        return self._socket.request(request)

    def attack(self, entity_type: int, entity_id: int, skill_id: int) -> Response:
        request: Request = {
            "service": self._service_name,
            "method": "attack",
            "params": {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "skill_id": skill_id
            }
        }
        return self._socket.request(request)

    def pickup(self, item_id: int) -> Response:
        request: Request = {
            "service": self._service_name,
            "method": "pickup",
            "params": {"item_id": item_id}
        }
        return self._socket.request(request)

    def target(self, entity_type: int, entity_id: int) -> Response:
        request: Request = {
            "service": self._service_name,
            "method": "target",
            "params": {
                "entity_type": entity_type,
                "entity_id": entity_id
            }
        }
        return self._socket.request(request)
