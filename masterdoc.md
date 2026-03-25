# Masterdoc de ROS2 e Linux

## Atalhos Especiais

- ```.``` (ponto) = diretório atual
- ```..``` (dois pontos) = diretório pai (um nível acima)
- ```~``` (til) = seu diretório home (```/home/seuusuario```)

**Exemplos práticos:**
```bash
cd /home/usuario/pasta    # caminho absoluto
cd pasta                  # caminho relativo (se você já está em /home/usuario)
cd ..                     # sobe um nível
cd ../..                  # sobe dois níveis
cd ~/.config              # vai para o diretório .config dentro do seu home
```

**ls**

    Lista o conteúdo do diretório atual ou de um caminho especificado.

    ls    # Lista conteúdos do diretório

    ls -a # Mostra arquivos e diretórios ocultos

    ls -l # Fornece lista detalhada, com permissões, tamanho, etc.

**mv**

    Move ou renomeia arquivos e diretórios.

    mv nome_antigo.txt nome_novo.txt        # renomeia um arquivo

    mv meu_arquivo.txt /caminho/para/destino # move o arquivo para outro diretório

**cp**

    Copia arquivos e diretórios.

    cp origem.txt destino.txt               # copia arquivo para um novo arquivo

    cp -r minha_pasta /caminho/para/destino # copia uma pasta inteira de forma recursiva


**rm**

    Remove (deleta) arquivos e diretórios.

    rm arquivo.txt       # deleta um arquivo

    rm -r minha_pasta    # deleta uma pasta e todo o seu conteúdo recursivamente

    rm -i arquivo.txt    # pede confirmação antes de cada remoção (mais seguro!)

    
## Atalhos Úteis do Terminal

- **Tab**: Autocompleta nomes de arquivos, diretórios e comandos
  - Digite as primeiras letras e pressione Tab
  - Se houver múltiplas opções, pressione Tab duas vezes para ver todas

- **↑ (seta para cima) / ↓ (seta para baixo)**: Navega pelo histórico de comandos
  - Útil para repetir ou modificar comandos anteriores

- **Ctrl + C**: Interrompe o comando que está executando
  - Use quando um comando travar ou você quiser cancelá-lo

- **Ctrl + L**: Limpa a tela do terminal
  - Equivalente ao comando ```clear```

- **Ctrl + R**: Busca no histórico de comandos
  - Digite parte do comando que você quer encontrar

- **Ctrl + D**: Fecha o terminal ou sai de uma sessão
  - Equivalente ao comando ```exit```

**Dica:** O Tab é seu melhor amigo! Use-o constantemente para economizar digitação e evitar erros de digitação.

---
## Comandos básicos de ROS2
```ros2 run <pacote> <executável>```

    Executa um nó (node) de um pacote específico. Cada pacote pode ter um ou mais executáveis.
```ros2 node list```

    Lista todos os nós ativos, isto é, processos ROS2 em execução no momento.
```ros2 node info <nome_do_nó>``` 

    Exibe detalhes sobre um nó específico, incluindo tópicos publicados/assinados, serviços oferecidos, parâmetros, etc.
```ros2 topic list```

    Lista todos os tópicos conhecidos pelo sistema ROS2.
```ros2 topic echo <tópico>```

    Mostra em tempo real as mensagens publicadas em um tópico.
```ros2 topic pub <tópico> <tipo_da_msg> <conteúdo>```

    Publica manualmente uma mensagem em um tópico. Útil para testes rápidos.
```ros2 service list```

    Lista todos os serviços disponíveis no sistema ROS2.
```ros2 service call <serviço> <tipo> <conteúdo>```

    Chama (request) um serviço específico, enviando um payload de requisição e aguardando a resposta.
    ros2 service call /clear std_srvs/srv/Empty {}
```ros2 interface list```

    Lista todos os tipos de interfaces conhecidos pelo ROS2, incluindo mensagens (msg), serviços (srv) e ações (action).
```ros2 interface show <tipo>```

    Mostra a estrutura (definição) de uma interface, que pode ser msg, srv ou action.
```ros2 topic info <tópico>```

    Mostra informações detalhadas sobre um tópico, incluindo tipo de mensagem, número de publishers e subscribers.
```rqt``` ou ```rqt_graph```

    Abre uma interface gráfica que reúne plugins para monitoramento e depuração (nós, tópicos, gráficos de dados, etc.).
```rviz2```

    Abre a ferramenta de visualização 3D do ROS2, permitindo enxergar mapas, modelos de robôs, sensores, TF (transform frames) etc.
```ros2 pkg create <nome_do_pacote> --build-type <tipo> --dependencies <dep1> <dep2>```

    Cria a estrutura inicial de um novo pacote ROS2, seja em C++ (ament_cmake) ou Python (ament_python).

| Argumento | Descrição | Exemplo |
|-----------|-----------|---------|
| `<nome_do_pacote>` | Nome do pacote (em snake_case) | `rm_description` |
| `--build-type` | Tipo de build (`ament_cmake` ou `ament_python`). Se omitido, usa `ament_cmake` | `--build-type ament_cmake` |
| `--dependencies` | Lista de pacotes dos quais este depende | `--dependencies urdf xacro` |
```colcon build```

    Compila os pacotes localizados no workspace atual. Um workspace ROS2 típico tem a estrutura:
    - `src/` - código fonte dos pacotes
    - `build/` - arquivos temporários de compilação
    - `install/` - pacotes compilados prontos para uso
    - `log/` - logs de compilação

    Após compilar, você DEVE fazer source para reconhecer os pacotes: source install/setup.bash
    
## Comandos do Gazebo
```gz sim```: Roda o Gazebo

### Compilando e Executando
Após criar a launch file e verificar o `setup.py`, compile o pacote e execute:

```bash
cd ~/robotica_ws
colcon build --packages-select rm_description
source install/setup.bash
ros2 launch rm_description gazebo_casa.launch.py
```
| Comando | Descrição |
|---------|-----------|
| `colcon build` | Compila todos os pacotes do workspace |
| `colcon build --packages-select <nome>` | Compila apenas o pacote especificado |
| `colcon build --symlink-install` | Cria links simbólicos em vez de copiar (útil para desenvolvimento) |

### Interagindo com o robô
**Terminal 2 — Enviar um comando de velocidade:**

```bash
gz topic -t /cmd_vel -m gz.msgs.Twist -p "linear: {x: 0.5}, angular: {z: 0.0}"
```

Observe o robô se mover para frente no Gazebo! Agora tente uma rotação:

```bash
gz topic -t /cmd_vel -m gz.msgs.Twist -p "linear: {x: 0.0}, angular: {z: 0.5}"
```

**Terminal 2 — Verificar dados de odometria:**

```bash
gz topic -e -t /odom
```

#### Visualizando a Câmera no Gazebo
**Terminal 1 — Lançar o Gazebo com o robô:**

```bash
cd ~/robotica_ws && source install/setup.bash
ros2 launch rm_description gazebo_casa.launch.py
```

Aguarde o robô aparecer na cena.

**Terminal 2 — Listar tópicos e verificar a câmera:**

```bash
gz topic -l
```

Procure pelos tópicos `/camera/image_raw` e `/camera/camera_info`. Para mais detalhes sobre o tópico de imagem:

```bash
gz topic -i -t /camera/image_raw
```

Isso mostra o tipo da mensagem Gazebo: `gz.msgs.Image`.

Para visualizar a imagem da câmera diretamente na interface do Gazebo:

1. Clique no ícone de **plugins** (três pontos no canto superior direito).
2. Selecione **Image Display**.
3. No campo de tópico, escolha `/camera/image_raw`.
4. Você verá a imagem capturada pela câmera do robô em tempo real.

#### Fazendo o robô andar no Gazebo
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

## Montagem do robô (URDF e XACRO)
Antes de começar a modelagem, é crucial entender a diferença entre esses base_footprint e base_link:

| Característica | `base_footprint` | `base_link` |
|----------------|------------------|-------------|
| **Definição** | Projeção do robô no plano do chão | Primeiro link físico do robô |
| **Posição Z** | Sempre em Z = 0 (no chão) | Altura real da base do robô |
| **Uso principal** | Navegação, localização, planejamento de caminho | Referência para montagem de sensores e atuadores |
| **Geometria** | Geralmente vazio (sem visual) | Contém visual, colisão e inércia |

**Por que usar ambos?**

- O `base_footprint` facilita algoritmos de navegação que trabalham em 2D (no plano do chão).
- O `base_link` representa a estrutura física real do robô.
- A separação permite que o robô "flutue" sobre o `base_footprint` em simulações de terreno irregular.

```
     Z
     │
     │    ┌─────────┐
     │    │base_link│  ← Altura real da base
     │    └─────────┘
     │         │
     │    ═════╪═════  ← base_footprint (Z=0)
─────┴─────────────────── Chão (plano XY)
```

### Links

Um **link** representa uma parte rígida (corpo) do robô. Cada link pode conter até três seções:

| Seção | Descrição | Obrigatória? |
|-------|-----------|--------------|
| `<visual>` | Define a aparência gráfica (forma, cor, textura) — o que você **vê** no RViz | Não |
| `<collision>` | Define a geometria usada para **detecção de colisões** na simulação | Não |
| `<inertial>` | Define as propriedades de **massa e inércia** para a simulação dinâmica | Não |

```xml
<link name="nome_do_link">
  <visual>
    <origin xyz="0 0 0" rpy="0 0 0"/>
    <geometry> ... </geometry>
    <material name="cor"/>
  </visual>
  <collision>
    <origin xyz="0 0 0" rpy="0 0 0"/>
    <geometry> ... </geometry>
  </collision>
  <inertial>
    <origin xyz="0 0 0" rpy="0 0 0"/>
    <mass value="1.0"/>
    <inertia ixx="0" ixy="0" ixz="0" iyy="0" iyz="0" izz="0"/>
  </inertial>
</link>
```

As geometrias disponíveis são:

| Geometria | Tag XML | Parâmetros |
|-----------|---------|------------|
| Caixa | `<box size="x y z"/>` | Dimensões em cada eixo |
| Cilindro | `<cylinder radius="r" length="l"/>` | Raio e comprimento (eixo Z) |
| Esfera | `<sphere radius="r"/>` | Raio |
| Mesh | `<mesh filename="package://..."/>` | Caminho para arquivo 3D (.stl, .dae) |

#### Resumo: Visual vs Collision vs Inertial

```
┌─────────────────────────────────────────────────────────────────┐
│                         LINK                                    │
├─────────────────┬─────────────────┬─────────────────────────────┤
│    <visual>     │   <collision>   │        <inertial>           │
├─────────────────┼─────────────────┼─────────────────────────────┤
│ O que você VÊ   │ O que COLIDE    │ Como o link se MOVE         │
│                 │                 │                             │
│ • Geometria     │ • Geometria     │ • Massa                     │
│ • Material/Cor  │   (simplificada)│ • Centro de massa           │
│ • Texturas      │ • Superfície    │ • Tensor de inércia         │
│                 │   de contato    │                             │
├─────────────────┼─────────────────┼─────────────────────────────┤
│ Renderização    │ Física de       │ Dinâmica do                 │
│ gráfica         │ colisão         │ corpo rígido                │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

### Joints

Um **joint** (junta) define a conexão e o movimento relativo entre dois links — um **pai** (parent) e um **filho** (child). A posição do link filho é sempre definida **em relação ao link pai** através do campo `<origin>`.

| Tipo de Joint | Descrição | Exemplo de Uso |
|---------------|-----------|----------------|
| `fixed` | Sem movimento — conexão rígida | Sensores fixos no chassis |
| `revolute` | Rotação com limites (ângulo mínimo e máximo) | Juntas de braço robótico |
| `continuous` | Rotação infinita (sem limites) | Rodas |
| `prismatic` | Translação linear com limites | Atuadores lineares |

```xml
<joint name="nome_da_junta" type="revolute">
  <parent link="link_pai"/>
  <child link="link_filho"/>
  <origin xyz="x y z" rpy="roll pitch yaw"/>
  <axis xyz="0 0 1"/>
  <limit lower="-3.14" upper="3.14" effort="10" velocity="1.0"/>
</joint>
```

| Campo | Descrição |
|-------|-----------|
| `<parent>` | Link pai — ponto de referência |
| `<child>` | Link filho — posicionado em relação ao pai |
| `<origin>` | Posição e orientação do filho em relação ao pai (translação `xyz` e rotação `rpy` em radianos) |
| `<axis>` | Eixo de rotação ou translação (apenas para joints móveis) |
| `<limit>` | Limites de posição, esforço e velocidade (obrigatório para `revolute` e `prismatic`) |

### Verificando a Árvore de Transformadas

Execute em um novo terminal:

```bash
ros2 run tf2_tools view_frames
```

Isso gera um arquivo `frames.pdf` mostrando a árvore de transformadas. 

Você deve ver:

```
base_footprint
    └── base_link
            └── link1
                    └── link2
                            └── end_effector
```

---