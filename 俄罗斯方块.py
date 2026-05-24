#!/usr/bin/env python3
"""
Hermes 升级版俄罗斯方块 - 终端版
经典7种方块造型，彩色方块视觉效果
支持方块移动、旋转、加速下落、满行消除
附带下一方块预览、等级难度递增、计分统计
具备开始、暂停、游戏结束、重新开局机制

操作说明:
  空格键: 开始游戏 / 暂停游戏 / 重新开局
  ↑ 方向键: 旋转方块
  ← 方向键: 方块左移
  → 方向键: 方块右移
  ↓ 方向键: 加速下落
  W 键:    一键落底
"""

import curses
import random
import time
import copy

# ==================== 基础配置 ====================
ROW = 20
COL = 10

# 七种经典俄罗斯方块样式
SHAPES = [
    [[1, 1, 1, 1]],                          # I
    [[1, 1], [1, 1]],                        # O
    [[0, 1, 0], [1, 1, 1]],                  # T
    [[1, 0, 0], [1, 1, 1]],                  # L
    [[0, 0, 1], [1, 1, 1]],                  # J
    [[0, 1, 1], [1, 1, 0]],                  # S
    [[1, 1, 0], [0, 1, 1]],                  # Z
]

# ==================== 游戏类 ====================
class TetrisGame:
    def __init__(self):
        self.board = [[0] * COL for _ in range(ROW)]
        self.current_shape = None
        self.current_color = 0
        self.current_x = 0
        self.current_y = 0
        self.next_shape = None
        self.next_color = 0
        self.score = 0
        self.level = 1
        self.drop_speed = 0.8  # 秒
        self.game_over = False
        self.is_pause = False
        self.is_start = False
        self.last_drop = 0

    def create_piece(self):
        """生成随机方块"""
        idx = random.randint(0, len(SHAPES) - 1)
        return copy.deepcopy(SHAPES[idx]), idx + 1

    def reset_piece(self):
        """初始化新方块"""
        if self.next_shape is not None:
            self.current_shape = copy.deepcopy(self.next_shape)
            self.current_color = self.next_color
        else:
            self.current_shape, self.current_color = self.create_piece()

        self.next_shape, self.next_color = self.create_piece()

        # 居中放置
        self.current_x = COL // 2 - len(self.current_shape[0]) // 2
        self.current_y = 0

        # 检查是否碰撞（游戏结束）
        if self.collision(self.current_x, self.current_y):
            self.game_over = True

    def collision(self, x, y):
        """方块碰撞边界检测（修复：添加顶部边界检查）"""
        for r in range(len(self.current_shape)):
            for c in range(len(self.current_shape[r])):
                if self.current_shape[r][c]:
                    nx = x + c
                    ny = y + r
                    if nx < 0 or nx >= COL or ny < 0 or ny >= ROW:
                        return True
                    if ny >= 0 and self.board[ny][nx]:
                        return True
        return False

    def merge(self):
        """方块固化到棋盘"""
        for r in range(len(self.current_shape)):
            for c in range(len(self.current_shape[r])):
                if self.current_shape[r][c]:
                    self.board[self.current_y + r][self.current_x + c] = self.current_color

    def clear_lines(self):
        """整行消除得分 + 升级难度"""
        lines_cleared = 0
        r = ROW - 1
        while r >= 0:
            if all(self.board[r]):
                del self.board[r]
                self.board.insert(0, [0] * COL)
                lines_cleared += 1
                # 不减少 r，因为上面的行下移后需要再次检查同一位置
            else:
                r -= 1

        if lines_cleared > 0:
            # 得分计算
            self.score += lines_cleared * 100 * self.level

            # 升级：每 500 分升一级
            new_level = self.score // 500 + 1
            if new_level > self.level:
                self.level = new_level
                # 难度自动提速
                self.drop_speed = max(0.2, 0.8 - (self.level - 1) * 0.08)

    def rotate(self):
        """旋转方块"""
        # 顺时针旋转矩阵
        old_shape = self.current_shape
        rows = len(self.current_shape)
        cols = len(self.current_shape[0])
        self.current_shape = [
            [self.current_shape[rows - 1 - r][c] for r in range(rows)]
            for c in range(cols)
        ]

        # 旋转后碰撞则恢复
        if self.collision(self.current_x, self.current_y):
            self.current_shape = old_shape

    def move_left(self):
        """方块左移"""
        if not self.collision(self.current_x - 1, self.current_y):
            self.current_x -= 1

    def move_right(self):
        """方块右移"""
        if not self.collision(self.current_x + 1, self.current_y):
            self.current_x += 1

    def drop(self):
        """自动下落"""
        if not self.collision(self.current_x, self.current_y + 1):
            self.current_y += 1
        else:
            self.merge()
            self.clear_lines()
            self.reset_piece()

    def hard_drop(self):
        """直接落底（按 W 键触发）"""
        while not self.collision(self.current_x, self.current_y + 1):
            self.current_y += 1
        self.merge()
        self.clear_lines()
        self.reset_piece()

    def reset(self):
        """重置游戏"""
        self.board = [[0] * COL for _ in range(ROW)]
        self.score = 0
        self.level = 1
        self.drop_speed = 0.8
        self.game_over = False
        self.is_pause = False
        self.is_start = False
        self.next_shape = None
        self.reset_piece()

# ==================== 绘制函数 ====================
def draw_board(win, game):
    """绘制游戏棋盘（修复左边框被方块覆盖问题）"""
    # 绘制棋盘背景（偏移一列，避免覆盖左边框）
    for r in range(ROW):
        for c in range(COL):
            color = game.board[r][c]
            if color:
                win.addch(r, c * 2 + 1, '█', curses.color_pair(color))
            else:
                win.addch(r, c * 2 + 1, ' ', curses.color_pair(0))

    # 绘制当前方块
    if game.current_shape and not game.game_over:
        for r in range(len(game.current_shape)):
            for c in range(len(game.current_shape[r])):
                if game.current_shape[r][c]:
                    y = game.current_y + r
                    x = (game.current_x + c) * 2 + 1
                    if 0 <= y < ROW:
                        win.addch(y, x, '█', curses.color_pair(game.current_color))

def draw_preview(win, game, start_y, start_x):
    """右侧下一方块预览"""
    win.addstr(start_y, start_x, "  下一个方块", curses.color_pair(7) | curses.A_BOLD)
    start_y += 2

    if game.next_shape:
        for r in range(len(game.next_shape)):
            for c in range(len(game.next_shape[r])):
                if game.next_shape[r][c]:
                    win.addch(start_y + r, start_x + c * 2, '█', curses.color_pair(game.next_color))

def draw_info(win, game, start_x):
    """实时显示分数与当前等级"""
    win.addstr(0, start_x, f"  得分: {game.score}", curses.color_pair(7) | curses.A_BOLD)
    win.addstr(2, start_x, f"  等级: {game.level}", curses.color_pair(7) | curses.A_BOLD)
    win.addstr(4, start_x, f"  速度: {game.drop_speed:.2f}s", curses.color_pair(7))

def draw_status(win, game, height, width):
    """绘制游戏状态提示"""
    # 居中计算
    mid_y = height // 2 - 2

    if not game.is_start and not game.game_over:
        # 开始提示
        msg = "按空格开始游戏"
        win.addstr(mid_y, (width - len(msg) * 2) // 2, msg, curses.color_pair(7) | curses.A_BOLD)
        win.addstr(mid_y + 2, (width - 28) // 2, "↑ 旋转  ←→ 移动  ↓ 加速  W 落底", curses.color_pair(6))
        win.addstr(mid_y + 4, (width - 20) // 2, "空格 暂停/继续", curses.color_pair(6))
    elif game.is_pause:
        # 暂停提示
        msg = "游戏暂停"
        win.addstr(mid_y, (width - len(msg) * 2) // 2, msg, curses.color_pair(3) | curses.A_BOLD)
        win.addstr(mid_y + 2, (width - 24) // 2, "按空格继续游戏", curses.color_pair(3))
    elif game.game_over:
        # 游戏结束
        msg1 = "游戏结束!"
        msg2 = f"最终得分: {game.score}"
        msg3 = "按空格重新开始"
        win.addstr(mid_y - 1, (width - len(msg1) * 2) // 2, msg1, curses.color_pair(1) | curses.A_BOLD)
        win.addstr(mid_y + 1, (width - len(msg2) * 2) // 2, msg2, curses.color_pair(7))
        win.addstr(mid_y + 3, (width - len(msg3) * 2) // 2, msg3, curses.color_pair(3) | curses.A_BOLD)

def draw_border(win, game):
    """绘制棋盘边框（适配偏移后的棋盘）"""
    right = COL * 2 + 1
    # 左侧边框
    for r in range(ROW + 1):
        win.addch(r, 0, '│', curses.color_pair(7))
        win.addch(r, right, '│', curses.color_pair(7))
    # 上下边框
    for c in range(right + 1):
        win.addch(0, c, '─', curses.color_pair(7))
        win.addch(ROW, c, '─', curses.color_pair(7))
    # 四角
    win.addch(0, 0, '┌', curses.color_pair(7))
    win.addch(0, right, '┐', curses.color_pair(7))
    win.addch(ROW, 0, '└', curses.color_pair(7))
    win.addch(ROW, right, '┘', curses.color_pair(7))

# ==================== 主游戏循环 ====================
def main(stdscr):
    # 初始化 curses
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(100)  # 100ms 非阻塞输入

    # 初始化颜色
    curses.start_color()
    curses.use_default_colors()
    # 1=青, 2=黄, 3=紫, 4=橙, 5=蓝, 6=绿, 7=红(白色用于文字)
    color_map = [
        curses.COLOR_CYAN,    # I - 青色
        curses.COLOR_YELLOW,  # O - 黄色
        curses.COLOR_MAGENTA, # T - 紫色
        curses.COLOR_RED,     # L - 橙色(用红色代替)
        curses.COLOR_BLUE,    # J - 蓝色
        curses.COLOR_GREEN,   # S - 绿色
        curses.COLOR_RED,     # Z - 红色
    ]
    for i, color in enumerate(color_map):
        curses.init_pair(i + 1, color, -1)
    curses.init_pair(7, curses.COLOR_WHITE, -1)

    # 创建游戏
    game = TetrisGame()
    game.reset_piece()

    # 获取终端尺寸
    height, width = stdscr.getmaxyx()

    # 面板偏移位置（棋盘右侧）
    panel_offset = COL * 2 + 3

    while True:
        # 清屏
        stdscr.clear()

        # 绘制游戏内容
        draw_border(stdscr, game)
        draw_board(stdscr, game)
        draw_info(stdscr, game, panel_offset)
        draw_preview(stdscr, game, 6, panel_offset)
        draw_status(stdscr, game, height, width)

        # 刷新显示
        stdscr.refresh()

        # 获取按键输入（非阻塞）
        key = stdscr.getch()

        # 处理空格键
        if key == ord(' ') or key == curses.KEY_SPACE:
            if game.game_over:
                # 重新开局
                game.reset()
            elif not game.is_start:
                # 开始游戏
                game.is_start = True
                game.last_drop = time.time()
            else:
                # 暂停/继续
                game.is_pause = not game.is_pause
                if not game.is_pause:
                    game.last_drop = time.time()
            continue

        # 游戏未开始或暂停/结束时不处理其他按键
        if not game.is_start or game.is_pause or game.game_over:
            time.sleep(0.1)
            continue

        # 处理方向键
        if key == curses.KEY_LEFT:
            game.move_left()
        elif key == curses.KEY_RIGHT:
            game.move_right()
        elif key == curses.KEY_UP:
            game.rotate()
        elif key == curses.KEY_DOWN:
            game.drop()
        # 修复：绑定 W 键到 hard_drop
        elif key == ord('w') or key == ord('W'):
            game.hard_drop()

        # 自动下落
        current_time = time.time()
        if current_time - game.last_drop >= game.drop_speed:
            game.drop()
            game.last_drop = current_time

# ==================== 入口 ====================
if __name__ == "__main__":
    print("俄罗斯方块 - 终端版")
    print("=" * 30)
    print("操作说明:")
    print("  空格键: 开始游戏 / 暂停游戏 / 重新开局")
    print("  ↑ 方向键: 旋转方块")
    print("  ← 方向键: 方块左移")
    print("  → 方向键: 方块右移")
    print("  ↓ 方向键: 加速下落")
    print("  W 键:     一键落底")
    print("=" * 30)
    print("按 Enter 开始游戏...")
    input()
    curses.wrapper(main)
    print("\n游戏结束! 感谢游玩!")
