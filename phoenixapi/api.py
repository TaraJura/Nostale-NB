from .clients.client_socket import ClientSocket
from .clients.player_manager import PlayerObjManagerClient
from .clients.packet_manager import PacketManagerClient
from .clients.inventory_manager import InventoryManagerClient


class PhoenixApi:
    def __init__(self, port: int):
        socket = ClientSocket(port)
        self.player_obj_manager = PlayerObjManagerClient(socket)
        self.packet_manager = PacketManagerClient(socket)
        self.inventory_manager = InventoryManagerClient(socket)
