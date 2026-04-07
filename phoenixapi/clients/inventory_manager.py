from .client_socket import ClientSocket, Request, Response
from .base_client import Client


class InventoryManagerClient(Client):
    def __init__(self, socket: ClientSocket):
        super().__init__("InventoryManagerService", socket)

    def get_equip_tab(self) -> list[dict]:
        request: Request = {
            "service": self._service_name,
            "method": "getEquipTab",
            "params": {}
        }
        response = self._socket.request(request)
        return response["result"]["inv_slots"]

    def get_main_tab(self) -> list[dict]:
        request: Request = {
            "service": self._service_name,
            "method": "getMainTab",
            "params": {}
        }
        response = self._socket.request(request)
        return response["result"]["inv_slots"]

    def get_etc_tab(self) -> list[dict]:
        request: Request = {
            "service": self._service_name,
            "method": "getEtcTab",
            "params": {}
        }
        response = self._socket.request(request)
        return response["result"]["inv_slots"]

    def get_inventory_slot(self, inv_tab: int, slot_index: int) -> dict:
        request: Request = {
            "service": self._service_name,
            "method": "getInventorySlot",
            "params": {
                "inv_tab": inv_tab,
                "slot_index": slot_index
            }
        }
        response = self._socket.request(request)
        return response["result"]

    def get_gold(self) -> int:
        request: Request = {
            "service": self._service_name,
            "method": "getGold",
            "params": {}
        }
        response = self._socket.request(request)
        return response["result"]["gold"]
