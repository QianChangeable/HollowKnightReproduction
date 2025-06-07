import pygame
import UnityFrame.UnityFrameBase as ufb

class Transform(ufb.Component):
    def __init__(self,gameObject:ufb.GameObject,position:()=(0,0),rotation:int=0,scale:()=(1,1),parent=None): # type: ignore
        super().__init__(gameObject)
        self.position=position
        self.rotation=rotation
        self.scale=scale
        self.parent=parent
        self.children=[]
        if parent!=None:
            parent.children.append(self)
    #设置父物体
    def setParent(self,parent):
        if parent==None:
            print("设置的父物体为空！")
            return
        newPositionX=self.position[0]-parent.position[0]
        newPositionY=self.position[1]-parent.position[1]
        self.position=(newPositionX,newPositionY)
        self.parent=parent
        parent.children.append(self)
    #设置位置
    def setPosition(self, newPosition):
        tempPositionX = newPosition[0] - self.position[0]
        tempPositionY = newPosition[1] - self.position[1]
        for child in self.children:
            # 创建新的坐标元组而不是修改现有元组
            child.position = (child.position[0] + tempPositionX, 
                            child.position[1] + tempPositionY)
        self.position = newPosition

    #设置旋转角度
    def setRtoation(self, newRoation):
        tempRotation = newRoation - self.rotation
        for child in self.children:
            child.rotation = child.rotation + tempRotation
        self.rotation = newRoation
        
    #设置缩放大小
    def setScale(self, newScale):
        tempScaleX = newScale[0] / self.scale[0]
        tempScaleY = newScale[1] / self.scale[1]
        for child in self.children:
            # 同样创建新元组
            child.scale = (child.scale[0] * tempScaleX, 
                        child.scale[1] * tempScaleY)
        self.scale = newScale

#动画类
class SpriteAnimation:
    def __init__(self, name,frames, frame_duration, loop=True):
        self.name=name
        self.frames = frames
        self.frame_duration = frame_duration
        self.loop = loop
        self.currentFrame = 0
        self.finished = False
        self.currentFrameElapsedTime = 0

    def update_frame(self, dt):
        if self.finished and self.loop == False:
            return
        self.currentFrameElapsedTime += dt
        if self.currentFrameElapsedTime > self.frame_duration:
            self.currentFrame += 1
            self.currentFrameElapsedTime=0
        if self.currentFrame >= len(self.frames):
            if self.loop:
                self.currentFrame = 0
            else:
                self.finished = True
                self.currentFrame = len(self.frames) - 1

    def get_current_frame(self):
        return self.frames[self.currentFrame]

    def resetAnimation(self):
        self.currentFrame = 0

#动画机组件
class Animator(ufb.Component):
    def __init__(self,gameObject):
        super().__init__(gameObject)
        self.animations={}
        self.currentAnimation=None
        self.sprite=None
        self.flipX=False #判断是否翻转精灵图片

    def addAnimation(self,animation):
        if animation.name in self.animations.keys():
            print("添加动画失败！已存在相同的动画名")
            return
        elif animation.__class__.__name__!="SpriteAnimation":
            print("添加的动画Type不正确！当前参数类型为："+animation.__class__.__name__)
        else:
            self.animations[animation.name]=animation

    def changeAnimation(self,name):
        if name in self.animations.keys():
            if self.currentAnimation != None:
                self.currentAnimation.resetAnimation()
            print("切换动画为"+name)
            self.currentAnimation=self.animations[name]
        else:
            print("当前动画集中没有命为"+name+"的动画！")

    def update(self,deltaTime):
        if self.currentAnimation==None:
            print("当前没有播放的动画")
            return
        self.currentAnimation.update_frame(deltaTime)
        self.sprite=self.currentAnimation.get_current_frame()

        # 计算精灵的宽度和高度
        sprite_width = self.sprite.get_width()
        sprite_height = self.sprite.get_height()     
        # 计算绘制位置（让物体位置对应图像中心）
        draw_x = self.gameObject.transform.position[0] - sprite_width // 2
        draw_y = self.gameObject.transform.position[1] - sprite_height // 2

        # # 根据flipX属性决定是否翻转精灵
        # if self.flipX:
        #     flipped_sprite = pygame.transform.flip(self.sprite, True, False)
        #     ufb.GameObjectManager.instance.canvas.blit(flipped_sprite, (self.gameObject.transform.position[0],self.gameObject.transform.position[1]))
        # else:
        #     ufb.GameObjectManager.instance.canvas.blit(self.sprite, (self.gameObject.transform.position[0],self.gameObject.transform.position[1]))
           # 根据flipX属性决定是否翻转精灵
        if self.flipX:
            flipped_sprite = pygame.transform.flip(self.sprite, True, False)
            ufb.GameObjectManager.instance.canvas.blit(flipped_sprite, (draw_x, draw_y))
        else:
            ufb.GameObjectManager.instance.canvas.blit(self.sprite, (draw_x, draw_y))

# 碰撞体基类
class Collider(ufb.Component):
    def __init__(self, gameObject, isTrigger=False, tag=""):
        super().__init__(gameObject)
        self.isTrigger = isTrigger  # 是否为触发器
        self.tag = tag  # 碰撞体标签，用于过滤碰撞
        self.offset = (0, 0)  # 相对于游戏对象位置的偏移
        self.enabled = True  # 是否启用碰撞
        
        # 自动注册到碰撞管理器
        ufb.GameObjectManager.instance.collision_manager.add_collider(self)
        
    def awake(self):
        super().awake()
        
    def get_position(self):
        """获取碰撞体在世界坐标中的位置"""
        transform_pos = self.gameObject.transform.position
        return (transform_pos[0] + self.offset[0], transform_pos[1] + self.offset[1])
    
    def check_collision(self, other):
        """检查与其他碰撞体的碰撞，子类需要重写此方法"""
        return False
    
    def on_collision_enter(self, other):
        """当碰撞开始时调用"""
        pass
        
    def on_collision_stay(self, other):
        """当碰撞持续时调用"""
        pass
        
    def on_collision_exit(self, other):
        """当碰撞结束时调用"""
        pass
    
    def on_trigger_enter(self, other):
        """当触发器碰撞开始时调用"""
        pass
        
    def on_trigger_stay(self, other):
        """当触发器碰撞持续时调用"""
        pass
        
    def on_trigger_exit(self, other):
        """当触发器碰撞结束时调用"""
        pass
    
    def onDestroy(self):
        """组件销毁时从碰撞管理器中移除"""
        ufb.GameObjectManager.instance.collision_manager.remove_collider(self)
        super().onDestroy()

# 矩形碰撞体
class BoxCollider(Collider):
    def __init__(self, gameObject, width=50, height=50, offset=(0, 0), isTrigger=False, tag=""):
        super().__init__(gameObject, isTrigger, tag)
        self.width = width
        self.height = height
        self.offset = offset
    
    def get_rect(self):
        """获取碰撞体的rect对象"""
        pos = self.get_position()
        return pygame.Rect(
            pos[0] - self.width // 2,
            pos[1] - self.height // 2,
            self.width,
            self.height
        )
    
    def check_collision(self, other):
        """检查与其他碰撞体的碰撞"""
        if isinstance(other, BoxCollider):
            return self.get_rect().colliderect(other.get_rect())
        elif isinstance(other, CircleCollider):
            # 矩形和圆的碰撞检测
            rect = self.get_rect()
            circle_pos = other.get_position()
            
            # 找到矩形上最近的点
            closest_x = max(rect.left, min(circle_pos[0], rect.right))
            closest_y = max(rect.top, min(circle_pos[1], rect.bottom))
            
            # 计算圆心到最近点的距离
            distance_x = circle_pos[0] - closest_x
            distance_y = circle_pos[1] - closest_y
            distance_squared = distance_x * distance_x + distance_y * distance_y
            
            return distance_squared < (other.radius * other.radius)
        
        return False
    
    def draw_debug(self, color=(255, 0, 0)):
        """绘制碰撞体的调试视图"""
        if not self.enabled or not self.gameObject.active:
            return
            
        rect = self.get_rect()
        pygame.draw.rect(
            ufb.GameObjectManager.instance.canvas,
            color,
            rect,
            1  # 线宽
        )

# 圆形碰撞体
class CircleCollider(Collider):
    def __init__(self, gameObject, radius=25, offset=(0, 0), isTrigger=False, tag=""):
        super().__init__(gameObject, isTrigger, tag)
        self.radius = radius
        self.offset = offset
    
    def check_collision(self, other):
        """检查与其他碰撞体的碰撞"""
        if isinstance(other, CircleCollider):
            pos1 = self.get_position()
            pos2 = other.get_position()
            
            # 计算两圆心之间的距离
            dx = pos1[0] - pos2[0]
            dy = pos1[1] - pos2[1]
            distance_squared = dx * dx + dy * dy
            
            # 如果距离小于两圆半径之和，则发生碰撞
            return distance_squared < ((self.radius + other.radius) * (self.radius + other.radius))
            
        elif isinstance(other, BoxCollider):
            return other.check_collision(self)
            
        return False
    
    def draw_debug(self, color=(255, 0, 0)):
        """绘制碰撞体的调试视图"""
        if not self.enabled or not self.gameObject.active:
            return
            
        pos = self.get_position()
        pygame.draw.circle(
            ufb.GameObjectManager.instance.canvas,
            color,
            (int(pos[0]), int(pos[1])),
            self.radius,
            1  # 线宽
        )




# 地面渲染器
class SpriteRenderer(ufb.Component):
    def __init__(self, gameObject, image_path=None, size=None):
        super().__init__(gameObject)
        self.image = None
        if image_path:
            self.load_image(image_path, size)
    
    def awake(self):
        super().awake()
            
    def load_image(self, image_path, size=None):
        """加载指定路径的图片"""
        try:
            self.image = pygame.image.load(image_path).convert_alpha()
            if size:
                self.image = pygame.transform.scale(self.image, size)
        except pygame.error as e:
            print(f"无法加载图片 {image_path}: {e}")
            
    def update(self, deltaTime):
        """渲染精灵"""
        if self.image and self.gameObject.active:
            # 获取变换组件
            transform = self.gameObject.transform
            # 计算绘制位置（让物体位置对应图像中心）
            draw_x = transform.position[0] - self.image.get_width() // 2
            draw_y = transform.position[1] - self.image.get_height() // 2
            
            # 绘制到画布上
            ufb.GameObjectManager.instance.canvas.blit(self.image, (draw_x, draw_y))


# 调试组件
class DebugRenderer(ufb.Component):
    """用于调试目的的渲染组件，可以绘制碰撞体等调试信息"""
    
    def __init__(self, gameObject, show_colliders=True):
        super().__init__(gameObject)
        self.show_colliders = show_colliders
        
    def update(self, deltaTime):
        """每帧更新时绘制调试信息"""
        if self.show_colliders:
            self.draw_colliders()
    
    def draw_colliders(self):
        """绘制当前对象碰撞体"""
        if not self.gameObject.active:
            return
                
        collider = self.gameObject.getComponent(BoxCollider)
        if collider and collider.enabled:
            rect = collider.get_rect()
            color = (0, 0, 255) if collider.isTrigger else (0, 255, 0)
            pygame.draw.rect(ufb.GameObjectManager.instance.canvas, color, rect, 2)
    
    def set_show_colliders(self, value):
        """设置是否显示碰撞体"""
        self.show_colliders = value
