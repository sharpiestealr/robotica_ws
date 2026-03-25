# Resumão da parte teórica

## Nós (Nodes)

Um **nó** é o processo executável fundamental no ROS2. Cada nó tem uma responsabilidade bem definida dentro do sistema robótico — por exemplo: controlar um motor, processar imagens de uma câmera, ou planejar trajetórias. Os nós se comunicam entre si através de **tópicos**, **serviços** ou **actions**.

## Tópicos

Um **tópico** é um canal de comunicação nomeado pelo qual os nós trocam mensagens de forma **assíncrona**. O modelo é **publish/subscribe**: quem envia não precisa saber quem está ouvindo, e vice-versa. Um tópico tem um **nome** (ex: `/cmd_vel`) e um **tipo de mensagem** fixo — todos os participantes precisam usar o mesmo tipo.

## Mensagens

Uma **mensagem** é a estrutura de dados trocada em um tópico. O ROS2 possui muitas mensagens padrão (ex: `geometry_msgs/Twist`, `sensor_msgs/LaserScan`), mas também é possível criar **mensagens customizadas**, definidas por arquivos `.msg`.

## Publishers e Subscribers

- **Publisher**: um nó que **envia** mensagens para um tópico.
- **Subscriber**: um nó que **recebe** mensagens de um tópico.

```
  [Publisher]
      |
      |  publica em
      v
  /aula8_topic   (tipo: custom_interfaces/msg/Aula8)
      |
      |  recebido por
      v
  [Subscriber]
```

### Estrutura genérica de um Publisher
```python
    import rclpy
    from rclpy.node import Node
    from custom_interfaces.msg import Aula8

    class Publisher(Node):
        def __init__(self):
            super().__init__('aula8_publisher')
            self.publisher = self.create_publisher(Aula8, 'aula8_topic', 10)
            self.timer = self.create_timer(1.0, self.timer_callback)
            self.contador = 0

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
```
### Estrutura genérica de um Subscriber
```python
    import rclpy
    from rclpy.node import Node
    from custom_interfaces.msg import Aula8

    class Subscriber(Node):
        def __init__(self):
            super().__init__('aula8_subscriber')
            self.subscription = self.create_subscription(
                Aula8, 'aula8_topic', self.subscription_callback, 10)

        def subscription_callback(self, msg):
            mensagem = msg.message
            contagem = msg.count
            self.get_logger().info('Recebendo: "%s%i"' % (mensagem, contagem))

    def main(args=None):
        rclpy.init(args=args)
        subscriber = Subscriber()
        rclpy.spin(subscriber)
        subscriber.destroy_node()
        rclpy.shutdown()
```

## Launch Files

Um **launch file** é um script Python que permite iniciar **múltiplos nós** com um único comando, em vez de abrir um terminal separado para cada um. Isso é essencial em projetos reais, onde o sistema robótico pode ter dezenas de nós rodando simultaneamente.

Os launch files ficam no diretório `launch/` do pacote e usam a extensão `.launch.py`. Além de iniciar nós, eles permitem passar parâmetros, incluir outros launch files e configurar o ambiente de execução.

### Estrutura genérica de um Launch File
```python
    from launch import LaunchDescription
    from launch_ros.actions import Node


    def generate_launch_description():

        publisher_node = Node(
            package='aula8',
            executable='publisher',
            name='aula8_publisher',
            output='screen',
        )

        subscriber_node = Node(
            package='aula8',
            executable='subscriber',
            name='aula8_subscriber',
            output='screen',
        )

        return LaunchDescription([
            publisher_node,
            subscriber_node,
        ])
```
---

## Serviços (Services)

Um **serviço** é um modelo de comunicação **síncrono** no ROS2, baseado em **requisição/resposta (request/response)**. Diferente dos tópicos — que utilizam o modelo **publish/subscribe** e são assíncronos — nos serviços, um nó envia uma requisição e **aguarda** até receber uma resposta.

Serviços são ideais para operações pontuais e sob demanda, como solicitar um cálculo, requisitar dados de sensores, ou disparar uma ação específica no robô (por exemplo, salvar um mapa ou mudar de modo de operação).

## Service Server e Service Client

- **Service Server**: nó que **disponibiliza** um serviço. Ele fica "escutando" requisições e, ao receber uma, executa uma função de callback para processá-la e retornar uma resposta.
- **Service Client**: nó que **envia** uma requisição ao serviço e aguarda a resposta.

```
  [Service Client]
      |
      |  REQUEST (requisição)
      |  ┌─────────────────┐
      |  │ a: 2            │
      |  │ b: 3            │
      |  └─────────────────┘
      v
  /aula9_srv   (tipo: custom_interfaces/srv/Aula9)
      |
      v
  [Service Server]
      |  (processa: sum = a + b)
      |
      |  RESPONSE (resposta)
      |  ┌─────────────────┐
      |  │ sum: 5          │
      |  └─────────────────┘
      v
  [Service Client]
```

## Interfaces de serviço (`.srv`)

Assim como tópicos usam mensagens (`.msg`), serviços usam **interfaces de serviço** definidas em arquivos `.srv`. A diferença é que uma interface de serviço possui **duas partes**, separadas por `---`:

- **Requisição (request)**: os campos enviados pelo client ao server.
- **Separador**: três hífens (`---`), que dividem a requisição da resposta.
- **Resposta (response)**: os campos retornados pelo server ao client.

## Estrutura genérica de um Service Server
```python
    import rclpy
    from rclpy.node import Node
    from custom_interfaces.srv import Aula9

    class SrvServer(Node):
        def __init__(self):
            super().__init__('aula9_srv_server')
            self.srv_server = self.create_service(Aula9, 'aula9_srv', self.srv_callback)

        def srv_callback(self, request, response):
            response.sum = request.a + request.b
            return response

    def main(args=None):
        rclpy.init(args=args)
        srv_server = SrvServer()
        rclpy.spin(srv_server)
        node.destroy_node()
        rclpy.shutdown()
```

### Estrutura genérica de um Service Client
```python
    import rclpy
    from rclpy.node import Node
    from custom_interfaces.srv import Aula9
    import sys

    class SrvClient(Node):
        def __init__(self):
            super().__init__('aula9_srv_client')
            self.srv_client = self.create_client(Aula9, 'aula9_srv')
            while not self.srv_client.wait_for_service(timeout_sec=1.0):
                self.get_logger().info('Service not available, waiting...')

        def send_request(self, a, b):
            request = Aula9.Request()
            request.a = a
            request.b = b
            future = self.srv_client.call_async(request)
            rclpy.spin_until_future_complete(self, future)
            return future.result()

    def main(args=None):
        rclpy.init(args=args)
        srv_client = SrvClient()
        result = srv_client.send_request(int(sys.argv[1]), int(sys.argv[2]))
        srv_client.get_logger().info(
            'Result of add_two_ints: for %d + %d = %d' %
            (int(sys.argv[1]), int(sys.argv[2]), result.sum))
        srv_client.destroy_node()
        rclpy.shutdown()
```

## Tópicos vs. Serviços

| Característica | Tópicos | Serviços |
|---|---|---|
| Modelo | Publish/Subscribe | Request/Response |
| Comunicação | Assíncrona | Síncrona |
| Fluxo | Contínuo (streaming) | Pontual (sob demanda) |
| Exemplo de uso | Dados de sensores, velocidade | Cálculos, consultas, comandos |

---

## Ações (Actions)

Uma **ação** é um modelo de comunicação **assíncrono e de longa duração** no ROS2, baseado em **objetivo/resultado/feedback (goal/result/feedback)**. Diferente dos serviços — que são síncronos e pontuais — as ações permitem enviar um objetivo, acompanhar o progresso por meio de **feedback contínuo** e receber um resultado ao final da execução.

Ações são ideais para tarefas que levam tempo para serem concluídas, como navegar até um ponto, mover um braço robótico, ou qualquer operação onde seja útil monitorar o progresso e, opcionalmente, cancelar a execução.

### Action Server e Action Client

- **Action Server**: nó que **disponibiliza** uma ação. Ele recebe objetivos (goals), executa a tarefa, envia feedback periódico durante a execução e retorna um resultado ao final.
- **Action Client**: nó que **envia** um objetivo ao action server, recebe feedback durante a execução e obtém o resultado final.

```
  [Action Client]
      |
      |  GOAL (objetivo)
      |  ┌─────────────────────┐
      |  │ count_up_to: 5      │
      |  └─────────────────────┘
      v
  /aula10_action   (tipo: custom_interfaces/action/Aula10)
      |
      v
  [Action Server]
      |  (executa a tarefa)
      |
      |  FEEDBACK (progresso)          ← enviado periodicamente
      |  ┌─────────────────────┐
      |  │ current_number: 0   │
      |  │ current_number: 1   │
      |  │ current_number: 2   │
      |  │ ...                 │
      |  └─────────────────────┘
      v
  [Action Client]
      |
      |  (ao final da execução)
      |
      |  RESULT (resultado)
      |  ┌─────────────────────┐
      |  │ final_count: 5      │
      |  └─────────────────────┘
      v
  [Action Client]
```

### Interfaces de ação (`.action`)

Assim como tópicos usam mensagens (`.msg`) e serviços usam interfaces de serviço (`.srv`), ações usam **interfaces de ação** definidas em arquivos `.action`. Uma interface de ação possui **três partes**, separadas por `---`:

- **Objetivo (goal)**: os campos enviados pelo client ao server ao iniciar a ação.
- **Primeiro separador** (`---`): divide o objetivo do resultado.
- **Resultado (result)**: os campos retornados pelo server ao client quando a ação termina.
- **Segundo separador** (`---`): divide o resultado do feedback.
- **Feedback**: os campos enviados periodicamente pelo server ao client durante a execução da ação.

## Tópicos vs. Serviços vs. Ações

| Característica | Tópicos | Serviços | Ações |
|---|---|---|---|
| Modelo | Publish/Subscribe | Request/Response | Goal/Result/Feedback |
| Comunicação | Assíncrona | Síncrona | Assíncrona |
| Fluxo | Contínuo (streaming) | Pontual (sob demanda) | Longa duração com progresso |
| Feedback | N/A | N/A | Sim, periódico |
| Cancelamento | N/A | N/A | Sim, durante execução |
| Exemplo de uso | Dados de sensores, velocidade | Cálculos, consultas, comandos | Navegação, movimentação, tarefas longas |