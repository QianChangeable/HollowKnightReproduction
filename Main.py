import pygame
import UnityFrame.UnityFrameBase as ufb
import UnityFrame.Components.Components as cp
import Entity
pygame.init()

pygame.display.set_caption("Hollow Knight")

gameObjectManager=ufb.GameObjectManager() # 注册游戏物体管理器

# 创建背景
background = ufb.GameObject("Background", True)
# 将背景对象放在渲染序列的最前面，确保它在所有对象之下
gameObjectManager.gameObjects.remove(background)
gameObjectManager.gameObjects.insert(0, background)

# 为背景添加Transform组件（位置设置为屏幕中心）
backgroundTransform = background.addComponent(cp.Transform, (500, 300))  # 假设屏幕大小为1000x600
# 添加背景图像渲染器
backgroundRenderer = background.addComponent(cp.SpriteRenderer, 
                                           "Assets/background.png",
                                           (1000, 600))  # 设置背景图像大小为全屏

# 修改椅子的初始化部分
chair = ufb.GameObject("Chair", True)
chairTransform = chair.addComponent(cp.Transform, (200, 490))  # 调整位置到地面上
chairRender = chair.addComponent(cp.SpriteRenderer, "Assets/Sprites/Objects/Bench/Bench.png", (183, 90))
chairCollider = chair.addComponent(cp.BoxCollider, 150, 60, (0, -10), False, "Bench")  # 为椅子添加碰撞体
chairInteraction = chair.addComponent(Entity.BenchInteraction)  # 添加椅子交互组件

# 创建玩家
player=ufb.GameObject("Player",True) # 注册游戏物体
playerDebug = player.addComponent(cp.DebugRenderer, False)  # 传递参数控制是否显示碰撞体

# 为游戏物体添加组件
playerAnimator=player.addComponent(cp.Animator) # 动画控制
playerTransform=player.addComponent(cp.Transform,(200,100)) # 位置控制
playerController=player.addComponent(Entity.PlayerController) # 玩家控制器
playerCollider = player.addComponent(cp.BoxCollider, 60, 120)  # 添加长方形碰撞体

# 创建地面
ground = ufb.GameObject("Ground", True)
groundDebug = ground.addComponent(cp.DebugRenderer, False)


groundTransform = ground.addComponent(cp.Transform, (500, 600))  # 水平居中，垂直在下方
groundCollider = ground.addComponent(cp.BoxCollider, 1000, 150, (0, 0), False, "Ground") # 为地面添加碰撞体，宽度较大，高度较小
groundRenderer = ground.addComponent(cp.SpriteRenderer, "Assets/Sprites/Objects/Floor/Floor.png",(1000,500))  # 假设您有地面图像


gameObjectManager.startGame() # 游戏物体管理器启动

# 创建音频管理器单例
audio_manager = ufb.AudioManager.get_instance()

# 播放背景音乐
audio_manager.play_background_music("Assets/Audios/cityoftears.wav", volume=0.5)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 填充背景色
    gameObjectManager.instance.canvas.fill((0, 0, 255))
    gameObjectManager.gameLoopLogic() # 游戏物体管理器的循环逻辑

    # 绘制碰撞箱
    # draw_colliders()

    # 更新显示
    pygame.display.flip()

pygame.quit()
