# O nó publica mensagens do tipo Aula8 periodicamente no tópico aula8_topic, 
# incrementando um contador a cada segundo.
import rclpy # biblioteca principal do ROS2 para Python.
from rclpy.node import Node # classe base para criar nós ROS2.
from custom_interfaces.msg import Aula8 # importa a mensagem customizada criada anteriormente.

# Definição do nó
class Publisher(Node):
    def __init__(self):
        super().__init__('aula8_publisher') #inicializa o nó com o nome aula8_publisher.
        self.publisher = self.create_publisher(Aula8, 'aula8_topic', 10) # cria um publisher para o tópico aula8_topic, com fila de até 10 mensagens não entregues.
        self.timer = self.create_timer(1.0, self.timer_callback) # chama timer_callback a cada 1 segundo.
        self.contador = 0

# Callback do timer
#Incrementa o contador e instancia um objeto do tipo Aula8.
#Preenche os campos count e message.
#Publica a mensagem no tópico e registra no log.
    def timer_callback(self):
        self.contador += 1
        msg = Aula8()
        msg.count = self.contador
        msg.message = 'A contagem é: '
        self.publisher.publish(msg)
        self.get_logger().info('Publicando: "%s%i"' % (msg.message, msg.count))

def main(args=None):
    rclpy.init(args=args)
    publisher = Publisher()
    rclpy.spin(publisher)
    publisher.destroy_node()
    rclpy.shutdown()