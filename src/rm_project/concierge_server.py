import os
import math
import yaml
import threading

import rclpy
from rclpy.action import ActionServer, GoalResponse, CancelResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from ament_index_python.packages import get_package_share_directory

from custom_interfaces.action import GoToRoom


def _make_pose(nav: BasicNavigator, x: float, y: float, yaw: float = 0.0) -> PoseStamped:
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = nav.get_clock().now().to_msg()
    pose.pose.position.x = float(x)
    pose.pose.position.y = float(y)
    pose.pose.orientation.z = math.sin(yaw / 2.0)
    pose.pose.orientation.w = math.cos(yaw / 2.0)
    return pose


class ConciergeServer(Node):
    
    # Função construtora do servidor de concierge: recebe o BasicNavigator e a lista de cômodos, inicializa o ActionServer e loga os cômodos disponíveis.
    def __init__(self, nav: BasicNavigator, rooms: dict):
        super().__init__('concierge_server')
        self._nav = nav
        self._rooms = rooms  
        self._busy = False
        self._lock = threading.Lock()

        cb_group = ReentrantCallbackGroup()
        self._action_server = ActionServer(
            self,
            GoToRoom,
            '/concierge/go_to_room',
            execute_callback=self._execute_cb,
            goal_callback=self._goal_cb,
            cancel_callback=self._cancel_cb,
            callback_group=cb_group,
        )
        self.get_logger().info(
            f'Concierge pronto. Cômodos disponíveis: {list(self._rooms.keys())}')

    # Função de recebimento de goal: verifica se o cômodo pedido existe e se o servidor não está ocupado, e aceita ou rejeita o goal de acordo.
    def _goal_cb(self, goal_request):
        room_name = goal_request.room_name
        with self._lock:
            # Se o cômodo pedido não estiver na lista de cômodos conhecidos, rejeita o goal e loga um aviso.
            if room_name not in self._rooms:
                self.get_logger().warn(f'Cômodo desconhecido: "{room_name}". Cômodos disponíveis: {list(self._rooms.keys())}')
                return GoalResponse.REJECT
            # Se self._busy for True, significa que já tem uma entrega em andamento, então rejeita o goal e loga um aviso. Caso contrário, marca self._busy como True para indicar que o servidor agora está ocupado com uma entrega.
            if self._busy:
                self.get_logger().warn('Já existe uma entrega em andamento.')
                return GoalResponse.REJECT
            # Caso o cômodo seja conhecido e o servidor não esteja ocupado, aceita o goal e marca self._busy como True.
            self._busy = True
        return GoalResponse.ACCEPT

    # Função de cancelamento: se o cliente pedir cancelamento, manda o Nav2 cancelar a navegação atual e aceita o cancelamento.
    def _cancel_cb(self, goal_handle):
        self.get_logger().info('Cancelamento solicitado pelo cliente.')
        self._nav.cancelTask()
        return CancelResponse.ACCEPT

    # Função que executa a ação: navega até o cômodo solicitado e preenche o resultado da ação com sucesso ou falha dependendo do resultado da navegação.
    def _execute_cb(self, goal_handle):
        room_name = goal_handle.request.room_name
        room = self._rooms[room_name]
        self.get_logger().info(f'Navegando para "{room_name}" → {room}')

        # Pega a pose alvo do cômodo e manda o Nav2 ir pra lá.
        target = _make_pose(
            self._nav, room['x'], room['y'], room.get('yaw', 0.0))
        self._nav.goToPose(target)  


        feedback_msg = GoToRoom.Feedback()
        feedback_msg.phase = 'going_to_room'

        # Loop que fica rodando enquanto o Nav2 não chegar no destino, for cancelado ou falhar. A cada iteração, pega o feedback do Nav2 e publica no feedback da ação.
        while not self._nav.isTaskComplete():
            nav_fb = self._nav.getFeedback()
            if nav_fb is not None:
                feedback_msg.distance_remaining = float(nav_fb.distance_remaining)
                goal_handle.publish_feedback(feedback_msg)

        # Verifica se o robô chegou, foi cancelado ou falhou, e preenche o resultado da ação de acordo.
        result = GoToRoom.Result()
        nav_result = self._nav.getResult()

        # Se o resultado for SUCCEEDED, preenche o resultado da ação com sucesso=True e uma mensagem de sucesso.
        if nav_result == TaskResult.SUCCEEDED:
            self.get_logger().info(f'Chegou em "{room_name}".')
            result.success = True
            result.message = f'Chegou em {room_name} com sucesso.'
            goal_handle.succeed()
        
        # Se o resultado for CANCELED, preenche o resultado da ação com sucesso=False e uma mensagem de cancelamento.
        elif nav_result == TaskResult.CANCELED:
            self.get_logger().warn('Navegação cancelada.')
            result.success = False
            result.message = 'Navegação cancelada.'
            goal_handle.canceled()
        
        # Se não for SUCCEEDED nem CANCELED, considera que falhou, preenche o resultado da ação com sucesso=False e uma mensagem de falha.
        else:
            self.get_logger().error('Navegação falhou.')
            result.success = False
            result.message = 'Navegação falhou.'
            goal_handle.abort()

        # Antes de retornar, marca o servidor como não ocupado para aceitar novos goals.
        with self._lock:
            self._busy = False
        return result


def main(args=None):
    rclpy.init(args=args)

    nav = BasicNavigator()

    server = ConciergeServer(nav, rooms)
    #Espera Nav2 ficar ativo antes de mandar o goal
    nav.get_logger().info('Aguardando Nav2 ficar ativo...')
    nav.waitUntilNav2Active()
    # Agora que Nav2 tá pronto, o servidor de concierge pode aceitar goals.
    server.get_logger().info(f'Nav2 ativo. Concierge pronto para receber goals. Cômodos disponíveis: {list(server._rooms.keys())}')

    # O MultiThreadedExecutor permite que o servidor de concierge e o BasicNavigator rodem ao mesmo tempo, sem bloquear um ao outro.
    executor = MultiThreadedExecutor()
    executor.add_node(nav) 
    executor.add_node(server)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        server.destroy_node()
        nav.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
