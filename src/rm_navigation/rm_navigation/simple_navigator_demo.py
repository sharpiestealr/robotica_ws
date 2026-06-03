import rclpy
from rclpy.duration import Duration
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult


def make_pose(nav: BasicNavigator, x: float, y: float, yaw_quat_w: float = 1.0) -> PoseStamped:
    """Helper rápido pra montar um PoseStamped no frame 'map'."""
    pose = PoseStamped()
    pose.header.frame_id = 'map'
    pose.header.stamp = nav.get_clock().now().to_msg()
    pose.pose.position.x = x
    pose.pose.position.y = y
    pose.pose.orientation.w = yaw_quat_w   # yaw 0 quando w=1
    return pose


def main():
    rclpy.init()
    nav = BasicNavigator()

    # 1) Espera o Nav2 ficar pronto (lifecycle_manager ativou tudo).
    nav.get_logger().info('Aguardando o Nav2 ficar ativo...')
    nav.waitUntilNav2Active()
    nav.get_logger().info('Nav2 pronto. Enviando goal.')

    # 2) Monta a pose alvo (ajuste x, y para algum ponto livre do seu mapa).
    goal_pose = make_pose(nav, x=1.5, y=5.0)

    # 3) Manda o goal — chamada NÃO bloqueante.
    nav.goToPose(goal_pose)

    # 4) Loop de feedback: imprime o que está acontecendo enquanto o robô anda.
    i = 0
    while not nav.isTaskComplete():
        feedback = nav.getFeedback()
        if feedback and i % 10 == 0:
            remaining = feedback.distance_remaining
            eta_s = Duration.from_msg(feedback.estimated_time_remaining).nanoseconds / 1e9
            nav.get_logger().info(
                f'Distância restante: {remaining:.2f} m | ETA: {eta_s:.1f} s')
        i += 1

    # 5) Trata o resultado final.
    result = nav.getResult()
    if result == TaskResult.SUCCEEDED:
        nav.get_logger().info('Goal alcançado.')
    elif result == TaskResult.CANCELED:
        nav.get_logger().warn('Goal cancelado.')
    elif result == TaskResult.FAILED:
        nav.get_logger().error('Goal falhou.')

    nav.lifecycleShutdown()
    rclpy.shutdown()


if __name__ == '__main__':
    main()