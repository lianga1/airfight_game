import tkinter as tk
import socket
import threading
from enum import Enum

# 定义飞机方向
class Direction(Enum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3

# 定义一个点
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return f"Point(x={self.x}, y={self.y})"

# 定义飞机
class Plane:
    def __init__(self, head: Point, direction: Direction):
        self.head = head
        self.direction = direction
        self.body_points = self.calculate_body_points()

    def calculate_body_points(self):
        """
        根据飞机的头部位置和方向，计算其他位置的点。
        """
        body_points = []
        x, y = self.head.x, self.head.y

        if self.direction == Direction.UP:
            body_points = [
                Point(x, y),
                Point(x, y + 1), Point(x - 2, y + 1), Point(x - 1, y + 1), Point(x + 1, y + 1), Point(x + 2, y + 1),
                Point(x, y + 2),
                Point(x - 1, y + 3), Point(x, y + 3), Point(x + 1, y + 3),
            ]
        elif self.direction == Direction.DOWN:
            body_points = [
                Point(x, y),
                Point(x, y - 1), Point(x - 2, y - 1), Point(x - 1, y - 1), Point(x + 1, y - 1), Point(x + 2, y - 1),
                Point(x, y - 2),
                Point(x - 1, y - 3), Point(x, y - 3), Point(x + 1, y - 3),
            ]
        elif self.direction == Direction.LEFT:
            body_points = [
                Point(x, y),
                Point(x - 1, y), Point(x - 1, y - 2), Point(x - 1, y - 1), Point(x - 1, y + 1), Point(x - 1, y + 2),
                Point(x - 2, y),
                Point(x - 3, y - 1), Point(x - 3, y), Point(x - 3, y + 1),
            ]
        elif self.direction == Direction.RIGHT:
            body_points = [
                Point(x, y),
                Point(x + 1, y), Point(x + 1, y - 2), Point(x + 1, y - 1), Point(x + 1, y + 1), Point(x + 1, y + 2),
                Point(x + 2, y),
                Point(x + 3, y - 1), Point(x + 3, y), Point(x + 3, y + 1),
            ]

        return body_points

# 定义局域网游戏类
class LANGame:
    def __init__(self, is_host, port=12345):
        self.is_host = is_host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.conn = None
        self.address = None
        self.opponent_confirmed = False
        self.able_atk = False 
        if is_host:
            self.host_game()
        else:
            self.join_game()

        # 启动接收消息线程
        threading.Thread(target=self.receive_messages, daemon=True).start()

    def host_game(self):
        self.able_atk = True
        self.sock.bind(("", self.port))
        self.sock.listen(1)
        print("等待对手加入...")
        self.conn, self.address = self.sock.accept()
        print(f"对手已连接：{self.address}")

    def join_game(self, host_ip="localhost"):
        self.able_atk = False
        self.sock.connect((host_ip, self.port))
        self.conn = self.sock
        print(f"已连接到主机 {host_ip}:{self.port}")

    def send_message(self, message):
        if self.conn:
            self.conn.sendall(message.encode())
        else:
            print("尚未建立连接，无法发送消息。")

    def receive_messages(self):
        while True:
            try:
                if self.is_host and not self.conn:
                    self.conn, self.address = self.sock.accept()
                message = self.conn.recv(1024).decode()
                if message:
                    self.handle_message(message)
            except WindowsError as e:
                print(e)
                break
            except Exception as e:
                print(f"接收消息时出错: {e}")
                continue
            

    def handle_message(self, message):
        if message.startswith("ATTACK:"):
            _, coords = message.split(":")
            x, y = map(int, coords.split(","))
            result = self.handle_attack(x, y)
            self.send_message(f"RESULT:{x},{y}:{result}")
            app.handle_atk(x,y,result)
        elif message.startswith("RESULT:"):
            _, coords, result = message.split(":")
            x, y = map(int, coords.split(",")[:2])
            app.handle_attack_result(x, y, result)
        elif message == "CONFIRM_PLANES":
            self.opponent_confirmed = True
            print("对手已确认飞机！")
            if app.planes_confirmed:
                print("双方已确认，游戏开始！")

    def handle_attack(self, x, y):
        """
        检查攻击是否击中飞机，返回结果。
        """
        self.able_atk = True
        for plane in app.planes:
            for i, point in enumerate(plane.body_points):
                if point.x == x and point.y == y:
                    if i == 0:
                        print("击中机头！")
                        #delete the plane
                        app.planes.remove(plane)
                        if len(app.planes) == 0:
                            print("游戏结束！")
                            self.send_message("GAME_OVER")
                        return "HIT_HEAD"  # 击中机头
                    
                    else:
                        print("击中机身！")
                        return "HIT_BODY"  # 击中机身
        print("没有击中！")
        return "MISS"  # 没有击中

# 定义GUI应用程序
class PlaneGameGUI:
    def __init__(self, root, lan_game):
        self.root = root
        self.lan_game = lan_game
        self.root.title("飞机大战")
        self.grid_size = 15
        self.cell_size = 30

        # 创建自己的棋盘
        self.canvas_own = tk.Canvas(self.root, width=self.grid_size * self.cell_size, height=self.grid_size * self.cell_size)
        self.canvas_own.pack(side=tk.LEFT)

        # 创建对手的棋盘
        self.canvas_opponent = tk.Canvas(self.root, width=self.grid_size * self.cell_size, height=self.grid_size * self.cell_size)
        self.canvas_opponent.pack(side=tk.RIGHT)

        self.planes = []
        self.current_direction = Direction.UP
        self.planes_confirmed = False
        self.create_buttons()
        self.draw_grid(self.canvas_own)
        self.draw_grid(self.canvas_opponent)
    
        self.canvas_own.bind("<Button-1>", self.place_plane)
        self.canvas_opponent.bind("<Button-1>", self.attack_position)

    def create_buttons(self):
        button_frame = tk.Frame(self.root)
        button_frame.pack()

        delete_button = tk.Button(button_frame, text="删除上一架飞机", command=self.delete_last_plane)
        delete_button.pack(side=tk.LEFT)

        rotate_cw_button = tk.Button(button_frame, text="顺时针旋转", command=self.rotate_clockwise)
        rotate_cw_button.pack(side=tk.LEFT)

        rotate_ccw_button = tk.Button(button_frame, text="逆时针旋转", command=self.rotate_counter_clockwise)
        rotate_ccw_button.pack(side=tk.LEFT)

        confirm_button = tk.Button(button_frame, text="确认飞机", command=self.confirm_planes)
        confirm_button.pack(side=tk.LEFT)

    def draw_grid(self, canvas):
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                x1 = i * self.cell_size
                y1 = j * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                canvas.create_rectangle(x1, y1, x2, y2, outline="black")

    def place_plane(self, event):
        if self.planes_confirmed:
            print("飞机已确认，无法再放置或更改位置。")
            return
        x = event.x // self.cell_size
        y = event.y // self.cell_size
        head = Point(x, y)
        plane = Plane(head, self.current_direction)
        self.planes.append(plane)
        self.draw_plane(self.canvas_own, plane)

    def draw_plane(self, canvas, plane):
        for i, point in enumerate(plane.body_points):
            x1 = point.x * self.cell_size
            y1 = point.y * self.cell_size
            x2 = x1 + self.cell_size
            y2 = y1 + self.cell_size
            fill_color = "red" if i == 0 else "blue"
            canvas.create_rectangle(x1, y1, x2, y2, fill=fill_color)

    def delete_last_plane(self):
        if self.planes_confirmed:
            print("飞机已确认，无法删除。")
            return
        if self.planes:
            self.planes.pop()
            self.canvas_own.delete("all")
            self.draw_grid(self.canvas_own)
            for plane in self.planes:
                self.draw_plane(self.canvas_own, plane)

    def rotate_clockwise(self):
        if self.planes_confirmed:
            print("飞机已确认，无法旋转。")
            return
        if self.planes:
            last_plane = self.planes[-1]
            new_direction = Direction((last_plane.direction.value + 1) % 4)
            last_plane.direction = new_direction
            last_plane.body_points = last_plane.calculate_body_points()
            self.canvas_own.delete("all")
            self.draw_grid(self.canvas_own)
            for plane in self.planes:
                self.draw_plane(self.canvas_own, plane)

    def rotate_counter_clockwise(self):
        if self.planes_confirmed:
            print("飞机已确认，无法旋转。")
            return
        if self.planes:
            last_plane = self.planes[-1]
            new_direction = Direction((last_plane.direction.value - 1) % 4)
            last_plane.direction = new_direction
            last_plane.body_points = last_plane.calculate_body_points()
            self.canvas_own.delete("all")
            self.draw_grid(self.canvas_own)
            for plane in self.planes:
                self.draw_plane(self.canvas_own, plane)

    def confirm_planes(self):
        if len(self.planes) != 3:
            print("必须有三架飞机才能确认！")
            return

        all_points = set()
        for plane in self.planes:
            for point in plane.body_points:
                if (point.x, point.y) in all_points:
                    print("飞机之间不能重叠！")
                    return
                if not (0 <= point.x < self.grid_size and 0 <= point.y < self.grid_size):
                    print("飞机超出边界，无法确认！")
                    return
                all_points.add((point.x, point.y))

        print("飞机确认成功！")
        self.planes_confirmed = True
        self.lan_game.send_message("CONFIRM_PLANES")
        if self.lan_game.opponent_confirmed:
            print("双方已确认，游戏开始！")

    def attack_position(self, event):
        if not self.lan_game.able_atk:
            print("请等待对手攻击完毕。")
            return
        if not self.planes_confirmed:
            print("请先确认飞机后再开始攻击。")
            return
        
        x = event.x // self.cell_size
        y = event.y // self.cell_size
        print(f"攻击位置: ({x}, {y})")
        self.lan_game.able_atk = False
        self.lan_game.send_message(f"ATTACK:{x},{y}")

    def handle_atk(self,x,y,result):
        """
        在自己的棋盘上更新被攻击的位置。
        """
        color = "black" if result == "MISS" else "green"
        self.color_cell(self.canvas_own, x, y, color)
        if result == "HIT_HEAD":
            print(f"你的飞机在位置 ({x}, {y}) 被击沉！")
            
    def handle_attack_result(self, x, y, result):
        """
        根据攻击结果在对手棋盘上染色。
        """


        if result == "MISS":
            color = "black"
        elif result == "HIT_BODY":
            color = "blue"
        elif result == "HIT_HEAD":
            color = "red"
        else:
            return
        self.color_cell(self.canvas_opponent, x, y, color)

    def color_cell(self, canvas, x, y, color):
        x1 = x * self.cell_size
        y1 = y * self.cell_size
        x2 = x1 + self.cell_size
        y2 = y1 + self.cell_size
        canvas.create_rectangle(x1, y1, x2, y2, fill=color)

if __name__ == "__main__":
    # get host ip from argv
    import sys
    if len(sys.argv) > 1:
        host_ip = sys.argv[1]
    is_host = input("是否作为主机？(y/n): ").lower() == 'y'
    lan_game = LANGame(is_host)
    root = tk.Tk()
    app = PlaneGameGUI(root, lan_game)
    root.mainloop()
