import os

import UnityFrame.Components.Components as cp
import UnityFrame.UnityFrameBase as ufb
import pygame

class PlayerController(ufb.Component):
    def __init__(self,gameObjcet):
        super().__init__(gameObjcet)
        self.animator=None
        self.stateMachine=StateMachine()
        self.idleState=None
        self.walkStartState=None

        # 添加一个重力禁用标记
        self.gravity_disabled = False

    def awake(self):
        super().awake()
        self.animator=self.gameObject.getComponent(cp.Animator)
        self.idleState=IdleState("Idle",self,self.animator)
        self.walkStartState=WalkStartState("WalkStart",self,self.animator)
        self.walkLoopState=WalkLoopState("WalkLoop",self,self.animator)

        self.dashState=DashState("Dash",self,self.animator)
        self.jumpdashState=JumpDashState("JumpDash",self,self.animator)

        self.jumpStartState=JumpStartState("Jump",self,self.animator)
        self.jumpLoopState=JumpLoopState("JumpLoop",self,self.animator)
        self.jumpLandState=JumpLandState("JumpLand",self,self.animator)
        self.doublejumpState=DoubleJumpState("DoubleJump",self,self.animator)
        
        self.attackState=AttackState("Attack",self,self.animator)
        self.attackTwiceState=AttackTwiceState("AttackTwice",self,self.animator)
        self.attackTopState=AttackTopState("AttackTop",self,self.animator)
        self.attackBottomState=AttackBottomState("AttackBottom",self,self.animator)

        self.jumpattackState=JumpAttackState("JumpAttack",self,self.animator)
        self.jumpattackTwiceState=JumpAttackTwiceState("JumpAttackTwice",self,self.animator)  
        self.jumpattackTopState=JumpAttackTopState("JumpAttackTop",self,self.animator)
        self.jumpattackBottomState=JumpAttackBottomState("JumpAttackBottom",self,self.animator)

        self.sitState=SitState("Sit",self,self.animator)

        # 获取碰撞体组件
        self.collider = self.gameObject.getComponent(cp.BoxCollider)
    
        # 增加跳跃相关参数
        self.isGrounded = False
        self.jumpForce = 12            # 初始跳跃力
        self.jumpExtraForce = 0.5      # 每帧额外施加的向上力
        self.jumpHoldMaxTime = 0.25    # 最大按住时间(秒)
        self.jumpCurrentHoldTime = 0   # 当前已按住时间
        self.isJumpButtonHeld = False  # 是否正在按住跳跃键
        self.gravity = 0.7
        self.velocity = 0
        self.prev_position = (0, 0)
        self.canDoubleJump = False
        self.spaceKeyReleased = True   # 空格键是否已释放
        self.jumpKeyUsed = False       # 标记跳跃键是否已经在当前跳跃周期中被使用

        # 冲刺和移动平滑过渡相关变量
        self.dash_momentum = 0
        self.dash_momentum_timer = 0
        self.dash_momentum_duration = 0.5
        self.last_dash_speed = 0  # 记录冲刺最后一帧的速度

    def start(self):
        super().start()
        self.stateMachine.initState(self.idleState)
        self.prev_position = self.gameObject.transform.position

    def update(self,deltaTime):
        super().update(deltaTime)

        # 保存当前位置，用于碰撞恢复
        self.prev_position = self.gameObject.transform.position



        # 处理冲刺余势
        if self.dash_momentum != 0:
            # 增加计时器
            self.dash_momentum_timer += deltaTime
            
            # 计算余势减少系数 (0.0到1.0之间线性减少)
            momentum_factor = max(0, 1 - (self.dash_momentum_timer / self.dash_momentum_duration))
            
            # 应用递减的余势
            current_momentum = self.dash_momentum * momentum_factor
            self.gameObject.transform.setPosition(
                (self.gameObject.transform.position[0] + current_momentum, 
                self.gameObject.transform.position[1])
            )
            
            # 当时间到达或接近结束时，清除余势
            if self.dash_momentum_timer >= self.dash_momentum_duration:
                self.dash_momentum = 0
                self.dash_momentum_timer = 0



        # 应用重力 - 添加对重力禁用标记的检查
        if not self.isGrounded and not self.gravity_disabled:
            self.velocity += self.gravity
            self.gameObject.transform.setPosition(
                (self.gameObject.transform.position[0], 
                self.gameObject.transform.position[1] + self.velocity)
            )

        # 主动检查与地面的碰撞
        self.check_ground_collision()

        self.stateMachine.currentState.update()

    def check_ground_collision(self):
        """主动检查与地面的碰撞"""
        # 找到所有地面物体
        for game_object in ufb.GameObjectManager.instance.gameObjects:
            if not game_object.active:
                continue
                
            # 跳过自己
            if game_object == self.gameObject:
                continue
                
            ground_collider = game_object.getComponent(cp.BoxCollider)
            if ground_collider and ground_collider.tag == "Ground" and ground_collider.enabled:
                # 检查碰撞
                if self.collider.check_collision(ground_collider):
                    self.handle_ground_collision(ground_collider)
                    return

        # 如果没有检测到地面碰撞，标记为未接地
        self.isGrounded = False

    def handle_ground_collision(self, ground_collider):
        """处理与地面的碰撞"""
        if self.velocity >= 0:  # 只有在下落时才处理地面碰撞
            # 设置接地状态
            self.isGrounded = True
            self.velocity = 0
            
            # 调整位置，确保角色站在地面上
            ground_top = ground_collider.get_rect().top
            self.gameObject.transform.setPosition(
                (self.gameObject.transform.position[0], 
                ground_top - self.collider.height/2)
            )
            
            # 如果当前是跳跃状态，切换到落地状态
            if (isinstance(self.stateMachine.currentState, JumpLoopState) or 
                isinstance(self.stateMachine.currentState, JumpStartState)):
                self.stateMachine.changeState(self.jumpLandState)

    def on_collision_enter(self, other):
        """碰撞开始时调用"""
        if other.tag == "Ground" and self.velocity >= 0:  # 仅在下落时检测
            # 标记为已经处理，避免重复处理
            self.handle_ground_collision(other)
            
    def on_collision_stay(self, other):
        """碰撞持续时调用"""
        if other.tag == "Ground" and self.velocity >= 0:
            # 确保角色不会穿过地面
            self.handle_ground_collision(other)

    def on_collision_exit(self, other):
        """碰撞结束时调用"""
        if other.tag == "Ground":
            self.isGrounded = False

class StateMachine:
    def __init__(self):
        self.currentState = None
        self.previousState = None  # 添加记录前一个状态的属性
        
    def initState(self, newState):
        self.currentState = newState
        self.previousState = None  # 初始状态没有前一个状态
        self.currentState.enter()
        
    def changeState(self, newState):
        self.currentState.exit()
        self.previousState = self.currentState  # 记录前一个状态
        self.currentState = newState
        self.currentState.enter()

class StateBase:
    def __init__(self,animName,player,animator):
        self.animName=animName
        self.player=player
        self.animator=animator
        self.keys=None

        self.from_dash = False
        self.initial_walk_speed = 10
        self.speed_decay_timer = 0
        self.speed_decay_duration = 0.3

        self.audio = ufb.AudioManager.get_instance()

    def enter(self):
        self.animator.changeAnimation(self.animName)

    def update(self):
        self.keys=pygame.key.get_pressed()
        pass

    def exit(self):
        pass

    def play_sound(self, sound_name):
        """播放指定音效"""
        self.audio.play_sound(sound_name)

class IdleState(StateBase):
    def __init__(self, animName, player, animator):
        super().__init__(animName, player, animator)

        # 设置图片路径
        base_path = "Assets/Sprites/Knight"
        Action = "Idle"  # 可以改为其他动作如"Attack", "Dash"等

        # 获取该动作目录下所有图片文件
        ActionFrames = sorted([f for f in os.listdir(os.path.join(base_path, Action))
                             if f.startswith(Action) and f.endswith('.PNG')])

        # 加载所有图片到列表
        ActionFrameList = []
        for img_file in ActionFrames:
            img_path = os.path.join(base_path, Action, img_file)
            image = pygame.image.load(img_path).convert_alpha()  # convert_alpha保留透明度
            ActionFrameList.append(image)

        ActionAnim=cp.SpriteAnimation("Idle",ActionFrameList,0.05)
        self.animator.addAnimation(ActionAnim)

    def enter(self):
        super().enter()

        # 停止之前的所有声音效果（包括下落音效）
        pygame.mixer.stop()  
        pass
    def update(self):
        super().update()

        # 重置跳跃相关标志，为新的跳跃周期准备
        if self.player.isGrounded:
            self.player.jumpKeyUsed = False
        
        # 左右移动
        if self.keys[pygame.K_a] or self.keys[pygame.K_d]:
            self.player.stateMachine.changeState(self.player.walkStartState)

        # 跳跃
        elif self.keys[pygame.K_SPACE]:
            self.player.stateMachine.changeState(self.player.jumpStartState)
        
        # 冲刺
        elif self.keys[pygame.K_k]:
            self.player.stateMachine.changeState(self.player.dashState)

        # 上劈
        if self.keys[pygame.K_w]:
            if self.keys[pygame.K_j]:
                self.player.stateMachine.changeState(self.player.attackTopState)

        # 下劈
        elif self.keys[pygame.K_s]:
            if self.keys[pygame.K_j]:
                self.player.stateMachine.changeState(self.player.attackBottomState)  

        # 横批
        elif self.keys[pygame.K_j]:
            self.player.stateMachine.changeState(self.player.attackState)
        

    def exit(self):
        super().exit()
        pass

class WalkStartState(StateBase):
    def __init__(self, animName, player, animator):
        super().__init__(animName, player, animator)
        # 设置图片路径
        base_path = "Assets/Sprites/Knight/Walk"
        Action = "WalkStart"  # 可以改为其他动作如"Attack", "Dash"等
        # 获取该动作目录下所有图片文件
        ActionFrames = sorted([f for f in os.listdir(os.path.join(base_path, Action))
                             if f.startswith(Action) and f.endswith('.PNG')])
        # 加载所有图片到列表
        ActionFrameList = []
        for img_file in ActionFrames:
            img_path = os.path.join(base_path, Action, img_file)
            image = pygame.image.load(img_path).convert_alpha()  # convert_alpha保留透明度
            ActionFrameList.append(image)

        ActionAnim = cp.SpriteAnimation("WalkStart", ActionFrameList, 0.08, loop=False) # 起步动画不循环
        self.animator.addAnimation(ActionAnim)
        

    def enter(self):
        super().enter()
        self.animator.currentAnimation.finished = False

        # 播放
        self.play_sound("run")
        
        # 检查是否从冲刺状态转换过来
        prev_state = self.player.stateMachine.previousState
        self.from_dash = isinstance(prev_state, DashState) or isinstance(prev_state, JumpDashState)
        
        # 设置初始步行速度 - 如果是从冲刺来的，保持较高速度
        if self.from_dash:
            # 使用冲刺的末速作为初速度
            self.initial_walk_speed = abs(self.player.last_dash_speed) * 0.5
            self.speed_decay_timer = 0
            self.speed_decay_duration = 0.3  # 在0.3秒内逐渐降低到正常步行速度
        else:
            self.initial_walk_speed = 10  # 正常步行速度

        pass
    def update(self):
        super().update()

        # self.player.dash_momentum = 0
        # self.player.dash_momentum_timer = 0

        if self.keys[pygame.K_SPACE]:
            self.player.stateMachine.changeState(self.player.jumpStartState)

        # 检查动画是否播放完毕，如果完毕则切换到walkLoop状态
        if self.animator.currentAnimation.finished: # 动画在动画机里
            self.player.stateMachine.changeState(self.player.walkLoopState) # 状态在状态机中

        # 上劈
        if self.keys[pygame.K_w]:
            if self.keys[pygame.K_j]:
                self.player.stateMachine.changeState(self.player.attackTopState) 

        # 下劈
        elif self.keys[pygame.K_s]:
            if self.keys[pygame.K_j]:
                self.player.stateMachine.changeState(self.player.attackBottomState) 

        # 横批
        elif self.keys[pygame.K_j]:
            self.player.stateMachine.changeState(self.player.attackState) 

        # 跳跃
        if self.keys[pygame.K_SPACE]:
            self.player.stateMachine.changeState(self.player.jumpStartState) 

        # 冲刺
        if self.keys[pygame.K_k]:
            self.player.stateMachine.changeState(self.player.dashState)

        # 计算当前应用的速度
        if self.from_dash:
            self.speed_decay_timer += 0.016
            decay_factor = max(0, 1 - (self.speed_decay_timer / self.speed_decay_duration))
            current_speed = 10 + (self.initial_walk_speed - 10) * decay_factor
        else:
            current_speed = 10
        
        # 移动时应用当前速度
        if self.keys[pygame.K_a]:
            self.player.gameObject.transform.setPosition(
                (self.player.gameObject.transform.position[0] - current_speed, 
                 self.player.gameObject.transform.position[1]))
            self.animator.flipX = False
        elif self.keys[pygame.K_d]:
            self.player.gameObject.transform.setPosition(
                (self.player.gameObject.transform.position[0] + current_speed, 
                 self.player.gameObject.transform.position[1]))
            self.animator.flipX = True
        else:
            self.player.stateMachine.changeState(self.player.idleState)

        pass
    def exit(self):
        super().exit()

        # 停止之前的所有声音效果（包括下落音效）
        pygame.mixer.stop()  # 或者使用您游戏引擎的对应API
        pass

class WalkLoopState(StateBase):
    def __init__(self, animName, player, animator):
        super().__init__(animName, player, animator)
        # 设置图片路径
        base_path = "Assets/Sprites/Knight/Walk"
        Action = "WalkLoop"  # 可以改为其他动作如"Attack", "Dash"等
        # 获取该动作目录下所有图片文件
        ActionFrames = sorted([f for f in os.listdir(os.path.join(base_path, Action))
                             if f.startswith(Action) and f.endswith('.PNG')])
        # 加载所有图片到列表
        ActionFrameList = []
        for img_file in ActionFrames:
            img_path = os.path.join(base_path, Action, img_file)
            image = pygame.image.load(img_path).convert_alpha()  # convert_alpha保留透明度
            ActionFrameList.append(image)

        ActionAnim = cp.SpriteAnimation("WalkLoop", ActionFrameList, 0.05) 
        self.animator.addAnimation(ActionAnim)
        

    def enter(self):
        super().enter()
        self.animator.currentAnimation.finished = False

        # 播放
        self.play_sound("run")

        # 继承前一个状态的速度信息
        prev_state = self.player.stateMachine.previousState
        if isinstance(prev_state, WalkStartState):
            self.initial_walk_speed = prev_state.initial_walk_speed
            self.from_dash = prev_state.from_dash
            self.speed_decay_timer = prev_state.speed_decay_timer
            self.speed_decay_duration = prev_state.speed_decay_duration
        else:
            self.initial_walk_speed = 10
            self.from_dash = False
            self.speed_decay_timer = 0
            self.speed_decay_duration = 0.3

        # 添加一个变量来跟踪上一帧的朝向
        self.lastFacingRight = True
        pass

    def update(self):
        super().update()
 
        currentFacingRight = self.animator.flipX  # 当前朝向


        # 上劈
        if self.keys[pygame.K_w]:
            if self.keys[pygame.K_j]:
                self.player.stateMachine.changeState(self.player.attackTopState) 

        # 下劈
        elif self.keys[pygame.K_s]:
            if self.keys[pygame.K_j]:
                self.player.stateMachine.changeState(self.player.attackBottomState) 

         # 横批
        elif self.keys[pygame.K_j]:
            self.player.stateMachine.changeState(self.player.attackState) 

        # 冲刺
        if self.keys[pygame.K_k]:
            self.player.stateMachine.changeState(self.player.dashState)

        # 跳跃
        if self.keys[pygame.K_SPACE]:
            self.player.stateMachine.changeState(self.player.jumpStartState) 

        # 计算当前应用的速度
        if self.from_dash:
            self.speed_decay_timer += 0.016
            decay_factor = max(0, 1 - (self.speed_decay_timer / self.speed_decay_duration))
            current_speed = 10 + (self.initial_walk_speed - 10) * decay_factor
        else:
            current_speed = 10

        # 移动
        if self.keys[pygame.K_a]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] - current_speed, self.player.gameObject.transform.position[1]))
            self.animator.flipX=False
            # 检测是否转向
            if currentFacingRight != self.animator.flipX:
                self.player.stateMachine.changeState(self.player.walkStartState)

        elif self.keys[pygame.K_d]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] + current_speed, self.player.gameObject.transform.position[1]))
            self.animator.flipX=True
            # 检测是否转向
            if currentFacingRight != self.animator.flipX:
                self.player.stateMachine.changeState(self.player.walkStartState)
        else:
            self.player.stateMachine.changeState(self.player.idleState)



        # 更新上一帧朝向
        self.lastFacingRight = self.animator.flipX
        pass
    def exit(self):
        super().exit()
        pass


class JumpStartState(StateBase):
    def __init__(self, animName, player, animator):
        super().__init__(animName, player, animator)

        # 设置图片路径
        base_path = "Assets/Sprites/Knight/Jump"
        Action = "Jump"  # 可以改为其他动作如"Attack", "Dash"等

        # 获取该动作目录下所有图片文件
        ActionFrames = sorted([f for f in os.listdir(os.path.join(base_path, Action))
                                if f.startswith(Action) and f.endswith('.PNG')])

        # 加载所有图片到列表
        ActionFrameList = []
        for img_file in ActionFrames:
            img_path = os.path.join(base_path, Action, img_file)
            image = pygame.image.load(img_path).convert_alpha()  # convert_alpha保留透明度
            ActionFrameList.append(image)

        ActionAnim=cp.SpriteAnimation("Jump",ActionFrameList,0.05,loop=False)
        self.animator.addAnimation(ActionAnim)

    def enter(self):
        super().enter()
        self.animator.currentAnimation.finished = False

        # 播放跳跃音效
        self.play_sound("jump")

        # 施加向上的初始速度
        self.player.isGrounded = False
        self.player.velocity = -self.player.jumpForce  # 负值表示向上

        # 初始化跳跃相关变量
        self.player.jumpCurrentHoldTime = 0
        self.player.isJumpButtonHeld = True  # 开始时认为按钮处于按下状态

        # 允许二段跳
        self.player.canDoubleJump = True

        # 标记跳跃键已被使用（需要释放后才能再次使用）
        self.player.jumpKeyUsed = True
        self.player.spaceKeyReleased = False  # 重置释放标记
        pass

    def update(self):
        super().update()

        # 检查是否持续按住跳跃键
        if self.keys[pygame.K_SPACE] and self.player.isJumpButtonHeld:
            # 增加持续按住时间
            self.player.jumpCurrentHoldTime += 0.016  # 假设16ms每帧
            
            # 如果未超过最大持续时间，继续施加向上的力
            if self.player.jumpCurrentHoldTime <= self.player.jumpHoldMaxTime:
                # 额外向上力（负值表示向上）
                self.player.velocity -= self.player.jumpExtraForce
        else:
            # 如果释放了跳跃键，停止施加额外的向上力
            self.player.isJumpButtonHeld = False
        
        # 检测空格键释放
        if not self.keys[pygame.K_SPACE]:
            self.player.spaceKeyReleased = True
            self.player.isJumpButtonHeld = False  # 跳跃键被释放
        
        # 检测双段跳跃 - 必须先释放过空格键，然后再次按下
        if self.keys[pygame.K_SPACE] and self.player.canDoubleJump and self.player.spaceKeyReleased and self.player.jumpKeyUsed:
            self.player.canDoubleJump = False  # 使用后不能再次使用
            self.player.spaceKeyReleased = False  # 标记空格键已被使用
            self.player.jumpKeyUsed = True  # 标记此次跳跃周期已使用跳跃键
            self.player.stateMachine.changeState(self.player.doublejumpState)
            return

        # 检查动画是否播放完毕，如果完毕则切换到JumpLoop状态
        if self.animator.currentAnimation.finished:
            self.player.stateMachine.changeState(self.player.jumpLoopState)

        # 上劈
        elif self.keys[pygame.K_w]:
            if self.keys[pygame.K_j]:
                self.player.stateMachine.changeState(self.player.jumpattackTopState)

        # 下劈
        elif self.keys[pygame.K_s]:
            if self.keys[pygame.K_j]:
                self.player.stateMachine.changeState(self.player.jumpattackBottomState)

        # 横劈
        elif self.keys[pygame.K_j]:
            self.player.stateMachine.changeState(self.player.jumpattackState)

        # 冲刺
        if self.keys[pygame.K_k]:
            self.player.stateMachine.changeState(self.player.jumpdashState)

        # 左右横移
        if self.keys[pygame.K_a]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] - 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX=False
        elif self.keys[pygame.K_d]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] + 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX=True
        pass
    def exit(self):
        super().exit()
        pass

class JumpLoopState(StateBase):
    def __init__(self, animName, player, animator):
        super().__init__(animName, player, animator)

        # 设置图片路径
        base_path = "Assets/Sprites/Knight/Jump"
        Action = "JumpLoop"  # 可以改为其他动作如"Attack", "Dash"等

        # 获取该动作目录下所有图片文件
        ActionFrames = sorted([f for f in os.listdir(os.path.join(base_path, Action))
                                if f.startswith(Action) and f.endswith('.PNG')])

        # 加载所有图片到列表
        ActionFrameList = []
        for img_file in ActionFrames:
            img_path = os.path.join(base_path, Action, img_file)
            image = pygame.image.load(img_path).convert_alpha()  # convert_alpha保留透明度
            ActionFrameList.append(image)

        ActionAnim=cp.SpriteAnimation("JumpLoop",ActionFrameList,0.05)
        self.animator.addAnimation(ActionAnim)

    def enter(self):
        super().enter()
        self.animator.currentAnimation.finished = False

        # 播放跳跃音效
        self.play_sound("falling")

        pass
    def update(self):
        super().update()

        # 继续检查是否持续按住跳跃键
        if self.keys[pygame.K_SPACE] and self.player.isJumpButtonHeld:
            # 增加持续按住时间
            self.player.jumpCurrentHoldTime += 0.016  # 假设16ms每帧
            
            # 如果未超过最大持续时间，继续施加向上的力
            if self.player.jumpCurrentHoldTime <= self.player.jumpHoldMaxTime:
                # 额外向上力
                self.player.velocity -= self.player.jumpExtraForce
        else:
            # 如果释放了跳跃键，停止施加额外的向上力
            self.player.isJumpButtonHeld = False
        
        # 检测空格键是否释放
        if not self.keys[pygame.K_SPACE]:
            self.player.spaceKeyReleased = True
            self.player.isJumpButtonHeld = False  # 跳跃键被释放
        
        # 检测双段跳跃 - 必须先释放过空格键，然后再次按下
        if self.keys[pygame.K_SPACE] and self.player.canDoubleJump and self.player.spaceKeyReleased and self.player.jumpKeyUsed:
            self.player.canDoubleJump = False  # 使用后不能再次使用
            self.player.spaceKeyReleased = False  # 标记空格键已被使用
            self.player.jumpKeyUsed = True  # 标记此次跳跃周期已使用跳跃键
            self.player.stateMachine.changeState(self.player.doublejumpState)
            return

        # 上劈
        if self.keys[pygame.K_w]:
            if self.keys[pygame.K_j]:
                self.player.stateMachine.changeState(self.player.jumpattackTopState)

        # 下劈
        elif self.keys[pygame.K_s]:
            if self.keys[pygame.K_j]:
                self.player.stateMachine.changeState(self.player.jumpattackBottomState)

        # 横劈
        elif self.keys[pygame.K_j]:
            self.player.stateMachine.changeState(self.player.jumpattackState)

        # 冲刺
        if self.keys[pygame.K_k]:
            self.player.stateMachine.changeState(self.player.jumpdashState)

        # 左右横移
        if self.keys[pygame.K_a]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] - 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX=False
        elif self.keys[pygame.K_d]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] + 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX=True

        pass
    def exit(self):
        super().exit()
        # 停止之前的所有声音效果（包括下落音效）
        pygame.mixer.stop()  # 或者使用您游戏引擎的对应API
        pass

class JumpLandState(StateBase):
    def __init__(self, animName, player, animator):
        super().__init__(animName, player, animator)

        # 设置图片路径
        base_path = "Assets/Sprites/Knight/Jump"
        Action = "Land"  # 可以改为其他动作如"Attack", "Dash"等

        # 获取该动作目录下所有图片文件
        ActionFrames = sorted([f for f in os.listdir(os.path.join(base_path, Action))
                                if f.startswith(Action) and f.endswith('.PNG')])

        # 加载所有图片到列表
        ActionFrameList = []
        for img_file in ActionFrames:
            img_path = os.path.join(base_path, Action, img_file)
            image = pygame.image.load(img_path).convert_alpha()  # convert_alpha保留透明度
            ActionFrameList.append(image)

        ActionAnim=cp.SpriteAnimation("JumpLand",ActionFrameList,0.05,loop=False)
        self.animator.addAnimation(ActionAnim)

    def enter(self):
        super().enter()
        self.animator.currentAnimation.finished = False

        # 停止之前的所有声音效果（包括下落音效）
        pygame.mixer.stop()  # 或者使用您游戏引擎的对应API
    
        # 播放跳跃音效
        self.play_sound("land")

        # 添加一个短暂的落地缓冲时间，用于控制连续跳跃的感觉
        self.landBuffer = 0.05  # 50毫秒的缓冲时间
        self.timeInState = 0

        # 重置所有跳跃相关标志
        self.player.canDoubleJump = False
        self.player.spaceKeyReleased = True
        self.player.jumpKeyUsed = False  # 重置跳跃键使用标记
        pass

        pass
    def update(self):
        super().update()

        # if self.animator.currentAnimation.finished:
        #     self.player.stateMachine.changeState(self.player.idleState)

        self.timeInState += 0.016  # 假设每帧约16ms
        
        # 允许在落地缓冲期过后立即接受跳跃输入
        if self.timeInState > self.landBuffer:
            # 直接处理跳跃输入，不需等待动画结束
            if self.keys[pygame.K_SPACE]:
                self.player.stateMachine.changeState(self.player.jumpStartState)
                return
        
        # 检查动画是否完成
        if self.animator.currentAnimation.finished:
            # 如果此时按下了SPACE键，立即跳跃
            if self.keys[pygame.K_SPACE]:
                self.player.stateMachine.changeState(self.player.jumpStartState)
            else:
                # 或者切换到相应状态
                if self.keys[pygame.K_a] or self.keys[pygame.K_d]:
                    self.player.stateMachine.changeState(self.player.walkStartState)
                else:
                    self.player.stateMachine.changeState(self.player.idleState)

        # 冲刺
        if self.keys[pygame.K_k]:
            self.player.stateMachine.changeState(self.player.dashState)

        if self.keys[pygame.K_a]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] - 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX=False
        elif self.keys[pygame.K_d]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] + 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX=True
        pass
    def exit(self):
        super().exit()
        pass

class DoubleJumpState(StateBase):
    def __init__(self, animName, player, animator):
        super().__init__(animName, player, animator)

        # 设置图片路径
        base_path = "Assets/Sprites/Knight"
        Action = "DoubleJump"  # 可以改为其他动作如"Attack", "Dash"等

        # 获取该动作目录下所有图片文件
        ActionFrames = sorted([f for f in os.listdir(os.path.join(base_path, Action))
                                if f.startswith(Action) and f.endswith('.PNG')])

        # 加载所有图片到列表
        ActionFrameList = []
        for img_file in ActionFrames:
            img_path = os.path.join(base_path, Action, img_file)
            image = pygame.image.load(img_path).convert_alpha()  # convert_alpha保留透明度
            ActionFrameList.append(image)

        ActionAnim=cp.SpriteAnimation("DoubleJump",ActionFrameList,0.05,loop=False)
        self.animator.addAnimation(ActionAnim)


        # 添加特效相关的代码
        self.dashEffects = []  # 用于存储dounlejump特效帧
        self.dashEffectAlpha = 255  # 特效透明度(0-255)，调整为200更自然
        self.effectOffsetX = 0  # 特效的X偏移
        self.effectOffsetY = 0  # 特效的Y偏移
        
        # 特效控制变量
        self.last_rendered_frame = -1  # 记录上一次渲染的帧
        self.effect_scale = 0.9  # 特效缩放比例
        
        effect_path = "Assets/Sprites/Knight/DoubleJumpEffect"
        effect_frames = sorted([f for f in os.listdir(effect_path) 
                                if f.startswith("doublejump_effect") and f.endswith('.png')])
            
        for img_file in effect_frames:
            img_path = os.path.join(effect_path, img_file)
            effect_image = pygame.image.load(img_path).convert_alpha()
            self.dashEffects.append(effect_image)


    def enter(self):
        super().enter()
        self.animator.currentAnimation.finished = False

        # 播放跳跃音效
        self.play_sound("doublejump")

        # 施加向上的初始速度
        self.player.isGrounded = False
        self.player.velocity = -self.player.jumpForce * 0.9  # 负值表示向上，二段跳初始力略小
        
        # 初始化跳跃相关变量
        self.player.jumpCurrentHoldTime = 0
        self.player.isJumpButtonHeld = True  # 开始时认为按钮处于按下状态

        # 二段跳后不能再次二段跳
        self.player.canDoubleJump = False
        
        # 重置特效控制
        self.last_rendered_frame = -1  # 重置为未渲染状态
        
    def draw_effect_frame(self, frame_index, scale_factor=None):
        """绘制指定的特效帧，可传入缩放参数"""
        # 确保帧索引有效
        if frame_index < 0 or frame_index >= len(self.dashEffects):
            return
            
        # 获取当前角色位置
        pos_x, pos_y = self.player.gameObject.transform.position
        
        # 获取特效图像并缩放
        effect_image = self.dashEffects[frame_index]
        
        # 使用传入的缩放系数，如果没传则使用默认值
        actual_scale = scale_factor if scale_factor is not None else self.effect_scale
        
        # 缩放特效
        original_width = effect_image.get_width()
        original_height = effect_image.get_height()
        new_width = int(original_width * actual_scale)
        new_height = int(original_height * actual_scale)
        effect_image = pygame.transform.scale(effect_image, (new_width, new_height))
        
        
        # 根据朝向翻转特效
        if self.animator.flipX == True:  # 角色朝右
            flipped_effect = effect_image  # 不需要翻转
        else:  # 角色朝左
            flipped_effect = pygame.transform.flip(effect_image, True, False)
            
        # 制作一个带透明度的特效副本
        effect_copy = flipped_effect.copy()
        effect_copy.set_alpha(self.dashEffectAlpha)
        
        # 计算特效中心点 - 确保特效居中显示在角色周围
        effect_center_x = pos_x - effect_copy.get_width() // 2
        effect_center_y = pos_y - effect_copy.get_height() // 2
        
        # 从中心点应用偏移
        draw_x = effect_center_x + self.effectOffsetX
        draw_y = effect_center_y + self.effectOffsetY
        
        # 将特效绘制到游戏画布上，确保它在角色下方
        # 我们直接绘制到主画布上，但在所有游戏对象之前
        ufb.GameObjectManager.instance.canvas.blit(effect_copy, (draw_x, draw_y))

    def update(self):
        super().update()

        # 检查是否持续按住跳跃键
        if self.keys[pygame.K_SPACE] and self.player.isJumpButtonHeld:
            # 增加持续按住时间
            self.player.jumpCurrentHoldTime += 0.016  # 假设16ms每帧
            
            # 如果未超过最大持续时间，继续施加向上的力
            if self.player.jumpCurrentHoldTime <= self.player.jumpHoldMaxTime:
                # 额外向上力，二段跳的额外力可以稍微小一点
                self.player.velocity -= self.player.jumpExtraForce * 0.95
        else:
            # 如果释放了跳跃键，停止施加额外的向上力
            self.player.isJumpButtonHeld = False

        # 获取当前动画帧
        current_frame = self.animator.currentAnimation.currentFrame
        
        # 只在前4帧处理特效，并且只在帧变化时绘制特效
        if current_frame < len(self.dashEffects) and current_frame != self.last_rendered_frame:
            # 在游戏主循环的开始，特效会被画布清空，所以需要在每一帧都重新绘制
            self.draw_effect_frame(current_frame,scale_factor=0.7)
            self.last_rendered_frame = current_frame

        # 检查动画是否播放完毕，如果完毕则切换到JumpLoop状态
        if self.animator.currentAnimation.finished:
            self.player.stateMachine.changeState(self.player.jumpLoopState)

        # 上劈
        elif self.keys[pygame.K_w]:
            if self.keys[pygame.K_j]:
                self.player.stateMachine.changeState(self.player.jumpattackTopState)

        # 下劈
        elif self.keys[pygame.K_s]:
            if self.keys[pygame.K_j]:
                self.player.stateMachine.changeState(self.player.jumpattackBottomState)

        # 横劈
        elif self.keys[pygame.K_j]:
            self.player.stateMachine.changeState(self.player.jumpattackState)

        # 冲刺
        if self.keys[pygame.K_k]:
            self.player.stateMachine.changeState(self.player.jumpdashState)

        # 左右横移
        if self.keys[pygame.K_a]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] - 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX=False
        elif self.keys[pygame.K_d]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] + 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX=True

    def exit(self):
        super().exit()
        pass


class DashState(StateBase):
    def __init__(self, animName, player, animator):
        super().__init__(animName, player, animator)

        # 设置图片路径
        base_path = "Assets/Sprites/Knight"
        Action = "Dash"  # 可以改为其他动作如"Attack", "Dash"等

        # 获取该动作目录下所有图片文件
        ActionFrames = sorted([f for f in os.listdir(os.path.join(base_path, Action))
                                if f.startswith(Action) and f.endswith('.PNG')])

        # 加载所有图片到列表
        ActionFrameList = []
        for img_file in ActionFrames:
            img_path = os.path.join(base_path, Action, img_file)
            image = pygame.image.load(img_path).convert_alpha()  # convert_alpha保留透明度
            ActionFrameList.append(image)

        ActionAnim=cp.SpriteAnimation("Dash",ActionFrameList,0.05,loop=False)
        self.animator.addAnimation(ActionAnim)


 
 
        # 添加特效相关的代码
        self.dashEffects = []  # 用于存储dash特效帧
        self.dashEffectAlpha = 255  # 特效透明度(0-255)
        self.effectOffsetX = 0  # 特效的X偏移
        self.effectOffsetY = 0  # 特效的Y偏移
        

        effect_path = "Assets/Sprites/Knight/DashEffect"
        effect_frames = sorted([f for f in os.listdir(effect_path) 
                                if f.startswith("dash_effect") and f.endswith('.png')])
            
        for img_file in effect_frames:
            img_path = os.path.join(effect_path, img_file)
            effect_image = pygame.image.load(img_path).convert_alpha()
            self.dashEffects.append(effect_image)



        # Dash属性参数
        self.dashSpeed = 35  # 每帧移动速度
        self.dashDuration = 8  # 冲刺持续多少帧
        self.dashProgress = 0  # 记录冲刺进度
        self.dashDirection = 0  # 冲刺方向 (-1为左, 1为右)

    def enter(self):
        super().enter()
        self.animator.currentAnimation.finished = False
        # 播放跳跃音效
        self.play_sound("dash")        
        # 根据朝向设置冲刺方向
        if self.animator.flipX == True:  # flipX为True表示朝右
            self.dashDirection = 1
        else:
            self.dashDirection = -1
            
        self.dashProgress = 0  # 重置冲刺进度
        pass
        
    def update(self):
        super().update()
        
        # 如果冲刺还未完成，继续移动
        if self.dashProgress < self.dashDuration:
            # 计算当前帧的移动距离
            moveDistance = self.dashSpeed * self.dashDirection
            
            # 应用移动
            self.player.gameObject.transform.setPosition(
                (self.player.gameObject.transform.position[0] + moveDistance, 
                 self.player.gameObject.transform.position[1]))
            
            # 获取当前动画帧索引
            current_frame_index = self.animator.currentAnimation.currentFrame
            
            # 绘制dash特效 - 在角色当前位置留下残影
            self.draw_dash_effect(current_frame_index,scale_factor=0.6) # 可以传参数
                 
            # 增加冲刺进度
            self.dashProgress += 1
        
        # 判断冲刺是否接近结束，预先判断玩家按键状态
        if self.dashProgress >= self.dashDuration - 2 and not self.animator.currentAnimation.finished:
            # 预读取按键状态，为接下来的状态转换做准备
            if self.keys[pygame.K_a] or self.keys[pygame.K_d]:
                # 可以预先设置角色朝向
                self.animator.flipX = self.keys[pygame.K_d]
        
        # 如果动画已经播放完毕，切换到idle状态或其他合适的状态
        if self.animator.currentAnimation.finished:
            # 根据当前按键状态决定转换到哪个状态
            if self.keys[pygame.K_a] or self.keys[pygame.K_d]:
                self.player.stateMachine.changeState(self.player.walkLoopState)
            else:
                self.player.stateMachine.changeState(self.player.idleState)
        
    def exit(self):
        super().exit()
        
        # 提供更强的余势和更长的持续时间
        if self.dashDirection > 0:  # 向右冲刺
            self.player.dash_momentum = 15  # 增加余势强度
        else:  # 向左冲刺
            self.player.dash_momentum = -15
            
        self.player.dash_momentum_timer = 0
        self.player.dash_momentum_duration = 0.2  # 增加持续时间
        
        # 重要：记录最后一帧的速度，确保下一个状态可以继承
        self.player.last_dash_speed = self.dashSpeed * self.dashDirection

    def draw_dash_effect(self, frame_index, scale_factor=1.0):

        # 确保有足够的特效帧
        if not self.dashEffects or frame_index >= len(self.dashEffects):
            return
            
        # 获取当前角色位置
        pos_x, pos_y = self.player.gameObject.transform.position
        
        # 获取当前特效帧
        effect_image = self.dashEffects[frame_index]
        
        # 应用缩放 - 根据传入的缩放系数调整特效大小
        if scale_factor != 1.0:
            original_width = effect_image.get_width()
            original_height = effect_image.get_height()
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            effect_image = pygame.transform.scale(effect_image, (new_width, new_height))
        
         # 根据朝向翻转特效
        if self.animator.flipX == True:  # 角色朝右
            flipped_effect = pygame.transform.flip(effect_image, True, False)         
        else:  # 角色朝左
            flipped_effect = effect_image
            
        # 制作一个带透明度的特效副本
        effect_copy = flipped_effect.copy()
        # 应用透明度
        effect_copy.set_alpha(self.dashEffectAlpha)
        
        # 计算特效中心点
        effect_center_x = pos_x - effect_copy.get_width() // 2
        effect_center_y = pos_y - effect_copy.get_height() // 2
        
        # 从中心点应用偏移
        draw_x = effect_center_x + self.effectOffsetX
        draw_y = effect_center_y + self.effectOffsetY
        
        # 在冲刺路径上留下残影 - 根据冲刺方向调整位置
        for i in range(1, 4):  # 创建3个残影
            # 每个残影的透明度递减
            trail_alpha = self.dashEffectAlpha // (i + 1)
            effect_copy.set_alpha(trail_alpha)
            
            # 计算残影位置 - 在角色身后
            trail_offset = -self.dashDirection * i * 20  # 根据冲刺方向和距离调整
            trail_x = draw_x + trail_offset
            trail_y = draw_y
            
            # 绘制残影
            ufb.GameObjectManager.instance.canvas.blit(effect_copy, (trail_x, trail_y))

        # 设置回原透明度用于下次绘制
        effect_copy.set_alpha(self.dashEffectAlpha)

class JumpDashState(StateBase):
    def __init__(self, animName, player, animator):
        super().__init__(animName, player, animator)

        # 设置图片路径
        base_path = "Assets/Sprites/Knight"
        Action = "Dash"  # 可以改为其他动作如"Attack", "Dash"等

        # 获取该动作目录下所有图片文件
        ActionFrames = sorted([f for f in os.listdir(os.path.join(base_path, Action))
                                if f.startswith(Action) and f.endswith('.PNG')])

        # 加载所有图片到列表
        ActionFrameList = []
        for img_file in ActionFrames:
            img_path = os.path.join(base_path, Action, img_file)
            image = pygame.image.load(img_path).convert_alpha()  # convert_alpha保留透明度
            ActionFrameList.append(image)

        ActionAnim=cp.SpriteAnimation("JumpDash",ActionFrameList,0.05,loop=False)
        self.animator.addAnimation(ActionAnim)

        # 添加特效相关的代码
        self.dashEffects = []  # 用于存储dash特效帧
        self.dashEffectAlpha = 255  # 特效透明度(0-255)
        self.effectOffsetX = 0  # 特效的X偏移
        self.effectOffsetY = 0  # 特效的Y偏移
        

        effect_path = "Assets/Sprites/Knight/DashEffect"
        effect_frames = sorted([f for f in os.listdir(effect_path) 
                                if f.startswith("dash_effect") and f.endswith('.png')])
            
        for img_file in effect_frames:
            img_path = os.path.join(effect_path, img_file)
            effect_image = pygame.image.load(img_path).convert_alpha()
            self.dashEffects.append(effect_image)


        # Dash属性参数
        self.dashSpeed = 35  # 每帧移动速度
        self.dashDuration = 8  # 冲刺持续多少帧
        self.dashProgress = 0  # 记录冲刺进度
        self.dashDirection = 0  # 冲刺方向 (-1为左, 1为右)

    def enter(self):
        super().enter()
        self.animator.currentAnimation.finished = False

        # 播放音效
        self.play_sound("dash")  
        
        # 根据朝向设置冲刺方向
        if self.animator.flipX == True:  # flipX为True表示朝右
            self.dashDirection = 1
        else:
            self.dashDirection = -1
            
        self.dashProgress = 0  # 重置冲刺进度
        pass
        
    def update(self):
        super().update()
        
        # 如果冲刺还未完成，继续移动
        if self.dashProgress < self.dashDuration:
            # 计算当前帧的移动距离
            moveDistance = self.dashSpeed * self.dashDirection
            
            # 应用移动
            self.player.gameObject.transform.setPosition(
                (self.player.gameObject.transform.position[0] + moveDistance, 
                 self.player.gameObject.transform.position[1]))
            
            # 获取当前动画帧索引并绘制特效
            current_frame_index = self.animator.currentAnimation.currentFrame
            self.draw_dash_effect(current_frame_index,scale_factor=0.6)

            # 增加冲刺进度
            self.dashProgress += 1

        # 判断冲刺是否接近结束，预先判断玩家按键状态
        if self.dashProgress >= self.dashDuration - 2 and not self.animator.currentAnimation.finished:
            # 预读取按键状态，为接下来的状态转换做准备
            if self.keys[pygame.K_a] or self.keys[pygame.K_d]:
                # 可以预先设置角色朝向
                self.animator.flipX = self.keys[pygame.K_d]

        # 如果动画已经播放完毕，切换到jumpLoop状态
        if self.animator.currentAnimation.finished:
            self.player.stateMachine.changeState(self.player.jumpLoopState)
        pass
        
    def exit(self):
        super().exit()
        
        # 提供更强的余势和更长的持续时间
        if self.dashDirection > 0:  # 向右冲刺
            self.player.dash_momentum = 15  # 增加余势强度
        else:  # 向左冲刺
            self.player.dash_momentum = -15
            
        self.player.dash_momentum_timer = 0
        self.player.dash_momentum_duration = 0.2  # 增加持续时间
        
        # 重要：记录最后一帧的速度，确保下一个状态可以继承
        self.player.last_dash_speed = self.dashSpeed * self.dashDirection

    def draw_dash_effect(self, frame_index, scale_factor=1.0):

        # 确保有足够的特效帧
        if not self.dashEffects or frame_index >= len(self.dashEffects):
            return
            
        # 获取当前角色位置
        pos_x, pos_y = self.player.gameObject.transform.position
        
        # 获取当前特效帧
        effect_image = self.dashEffects[frame_index]
        
        # 应用缩放 - 根据传入的缩放系数调整特效大小
        if scale_factor != 1.0:
            original_width = effect_image.get_width()
            original_height = effect_image.get_height()
            new_width = int(original_width * scale_factor)
            new_height = int(original_height * scale_factor)
            effect_image = pygame.transform.scale(effect_image, (new_width, new_height))
        
        # 根据朝向翻转特效
        if self.animator.flipX == True:  # 角色朝右
            flipped_effect = pygame.transform.flip(effect_image, True, False)         
        else:  # 角色朝左
            flipped_effect = effect_image
            
        # 制作一个带透明度的特效副本
        effect_copy = flipped_effect.copy()
        # 应用透明度
        effect_copy.set_alpha(self.dashEffectAlpha)
        
        # 计算特效中心点
        effect_center_x = pos_x - effect_copy.get_width() // 2
        effect_center_y = pos_y - effect_copy.get_height() // 2
        
        # 从中心点应用偏移
        draw_x = effect_center_x + self.effectOffsetX
        draw_y = effect_center_y + self.effectOffsetY
        
        # 在冲刺路径上留下残影 - 根据冲刺方向调整位置
        for i in range(1, 4):  # 创建3个残影
            # 每个残影的透明度递减
            trail_alpha = self.dashEffectAlpha // (i + 1)
            effect_copy.set_alpha(trail_alpha)
            
            # 计算残影位置 - 在角色身后
            trail_offset = -self.dashDirection * i * 20  # 根据冲刺方向和距离调整
            trail_x = draw_x + trail_offset
            trail_y = draw_y
            
            # 绘制残影
            ufb.GameObjectManager.instance.canvas.blit(effect_copy, (trail_x, trail_y))

        # 设置回原透明度用于下次绘制
        effect_copy.set_alpha(self.dashEffectAlpha)


class AttackState(StateBase):
    def __init__(self, animName, player, animator):
        super().__init__(animName, player, animator)

        # 设置图片路径
        base_path = "Assets/Sprites/Knight/Attack/Attack"
        Action = "Attack"  # 可以改为其他动作如"Attack", "Dash"等

        # 获取该动作目录下所有图片文件
        ActionFrames = sorted([f for f in os.listdir(os.path.join(base_path, Action))
                             if f.startswith(Action) and f.endswith('.PNG')])

        # 加载所有图片到列表
        ActionFrameList = []
        for img_file in ActionFrames:
            img_path = os.path.join(base_path, Action, img_file)
            image = pygame.image.load(img_path).convert_alpha()  # convert_alpha保留透明度
            ActionFrameList.append(image)

        ActionAnim=cp.SpriteAnimation("Attack",ActionFrameList,0.05,loop=False)
        self.animator.addAnimation(ActionAnim)

        effect_path = os.path.join("Assets/Sprites/Knight/Attack/Attack/AttackEffect", "AttackEffect_01.PNG")
        self.effect_image = pygame.image.load(effect_path).convert_alpha()

        # 初始化攻击相关变量
        self.attackTriggered = False
        self.attackOffsetX = 70  # 攻击特效的X轴偏移量
        
        # 二段攻击相关变量
        self.combo_window_active = False     # 连击窗口是否激活
        self.combo_window_timer = 0          # 连击窗口计时器
        self.combo_window_duration = 0.3     # 连击窗口持续时间(秒)
        self.attack_key_released = False     # 攻击键是否释放（避免持续按住连击）


    def enter(self):
        super().enter()
        self.attackTriggered = False
        self.animator.currentAnimation.finished = False
        self.combo_window_active = False
        self.combo_window_timer = 0
        self.attack_key_released = False
        
        # 记录进入攻击状态时是否在地面上
        # 正确获取当前的地面状态
        self.was_grounded = self.player.isGrounded
        
        # 检查上一个状态，而不是当前状态
        prev_state = self.player.stateMachine.previousState
        if prev_state and (isinstance(prev_state, WalkStartState) or 
                        isinstance(prev_state, WalkLoopState) or 
                        isinstance(prev_state, IdleState)):
            self.was_grounded = True
        
        # 获取键盘状态
        self.keys = pygame.key.get_pressed()
        
        if self.keys[pygame.K_j]:
            self.attack_key_released = False
        else:
            self.attack_key_released = True

    def update(self):
        super().update()
        
        # 更新连击窗口计时器
        if self.combo_window_active:
            self.combo_window_timer += 0.016  # 假设16ms每帧
            
            # 检查是否已释放攻击键并再次按下（用于连击）
            if self.attack_key_released and self.keys[pygame.K_j]:
                self.player.stateMachine.changeState(self.player.attackTwiceState)
                return
            
            # 检查连击窗口是否已过期
            if self.combo_window_timer >= self.combo_window_duration:
                self.combo_window_active = False
        
        # 检测攻击键是否释放
        if not self.keys[pygame.K_j]:
            self.attack_key_released = True
        
        # 当攻击动画进行到一半时触发特效
        if not self.attackTriggered and self.animator.currentAnimation.currentFrame >= len(self.animator.currentAnimation.frames) // 2:
            self.attackTriggered = True

            # 播放攻击音效
            self.play_sound("sword")
            
            # 这个时候也激活连击窗口
            self.combo_window_active = True
            self.combo_window_timer = 0
            
            if self.effect_image:
                # 直接绘制特效，不使用动画系统
                offset = self.attackOffsetX if self.animator.flipX else -self.attackOffsetX
                effect_pos = (self.player.gameObject.transform.position[0] + offset, 
                            self.player.gameObject.transform.position[1])
                
                # 特效绘制
                flipped_effect = pygame.transform.flip(self.effect_image, self.animator.flipX, False)
                ufb.GameObjectManager.instance.canvas.blit(flipped_effect, 
                                                        (effect_pos[0] - self.effect_image.get_width()//2,
                                                        effect_pos[1] - self.effect_image.get_height()//2))
                
        # 当动画完成时返回到相应状态
        if self.animator.currentAnimation.finished:
            # 使用进入状态时记录的地面状态，而不是当前状态
            if self.was_grounded:
                if self.keys[pygame.K_a] or self.keys[pygame.K_d]:
                    self.player.stateMachine.changeState(self.player.walkLoopState)
                else:
                    self.player.stateMachine.changeState(self.player.idleState)
            else:
                self.player.stateMachine.changeState(self.player.jumpLoopState)
        
        # 可以在攻击时允许有限的移动
        if self.keys[pygame.K_a]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] - 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX = False
            # 播放音效
            self.play_sound("run")
        elif self.keys[pygame.K_d]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] + 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX = True
            # 播放音效
            self.play_sound("run")
    def exit(self):
        super().exit()

        # 停止之前的所有声音效果（包括下落音效）
        pygame.mixer.stop()  # 或者使用您游戏引擎的对应API
        pass

class AttackTwiceState(StateBase):
    def __init__(self, animName, player, animator):
        super().__init__(animName, player, animator)

        # 设置图片路径
        base_path = "Assets/Sprites/Knight/Attack/Attack"
        Action = "AttackTwice"  # 可以改为其他动作如"Attack", "Dash"等

        # 获取该动作目录下所有图片文件
        ActionFrames = sorted([f for f in os.listdir(os.path.join(base_path, Action))
                             if f.startswith(Action) and f.endswith('.PNG')])

        # 加载所有图片到列表
        ActionFrameList = []
        for img_file in ActionFrames:
            img_path = os.path.join(base_path, Action, img_file)
            image = pygame.image.load(img_path).convert_alpha()  # convert_alpha保留透明度
            ActionFrameList.append(image)

        ActionAnim=cp.SpriteAnimation("AttackTwice",ActionFrameList,0.05,loop=False)
        self.animator.addAnimation(ActionAnim)
        
        # 加载二段攻击特效

        effect_path = os.path.join("Assets/Sprites/Knight/Attack/Attack/AttackTwiceEffect", "AttackTwiceEffect_01.PNG")
        self.effect_image = pygame.image.load(effect_path).convert_alpha()

            
        # 初始化攻击相关变量
        self.attackTriggered = False
        self.attackOffsetX = 70  # 攻击特效的X轴偏移量，可以比第一段远一点

    # def enter(self):
    #     super().enter()
    #     self.attackTriggered = False  # 重置触发状态
    #     self.animator.currentAnimation.finished = False  # 确保动画状态正确

    def enter(self):
        super().enter()
        self.attackTriggered = False  # 重置触发状态
        self.animator.currentAnimation.finished = False  # 确保动画状态正确
        
        # 记录进入攻击状态时是否在地面上
        self.was_grounded = self.player.isGrounded
        
        # 检查上一个状态
        prev_state = self.player.stateMachine.previousState
        if prev_state and isinstance(prev_state, AttackState):
            # 如果是从一段攻击来的，继承一段攻击的地面状态
            self.was_grounded = prev_state.was_grounded
        
    def update(self):
        super().update()
        
        # 当攻击动画进行到一半时触发特效
        if not self.attackTriggered and self.animator.currentAnimation.currentFrame >= len(self.animator.currentAnimation.frames) // 2:
            self.attackTriggered = True

            # 播放攻击音效
            self.play_sound("sword")

            if self.effect_image:
                # 直接绘制特效，不使用动画系统
                offset = self.attackOffsetX if self.animator.flipX else -self.attackOffsetX
                effect_pos = (self.player.gameObject.transform.position[0] + offset, 
                            self.player.gameObject.transform.position[1])
                
                # 特效绘制
                flipped_effect = pygame.transform.flip(self.effect_image, self.animator.flipX, False)
                ufb.GameObjectManager.instance.canvas.blit(flipped_effect, 
                                                        (effect_pos[0] - self.effect_image.get_width()//2,
                                                        effect_pos[1] - self.effect_image.get_height()//2))
                
        # # 当动画完成时返回到相应状态
        # if self.animator.currentAnimation.finished:
        #     if self.player.isGrounded:
        #         if self.keys[pygame.K_a] or self.keys[pygame.K_d]:
        #             self.player.stateMachine.changeState(self.player.walkLoopState)
        #         else:
        #             self.player.stateMachine.changeState(self.player.idleState)
        #     else:
        #         self.player.stateMachine.changeState(self.player.jumpLoopState)

        # 当动画完成时返回到相应状态
        if self.animator.currentAnimation.finished:
            # 使用记录的地面状态而不是当前状态
            if self.was_grounded:
                if self.keys[pygame.K_a] or self.keys[pygame.K_d]:
                    self.player.stateMachine.changeState(self.player.walkLoopState)
                else:
                    self.player.stateMachine.changeState(self.player.idleState)
            else:
                self.player.stateMachine.changeState(self.player.jumpLoopState)
        
        # 可以在攻击时允许有限的移动
        if self.keys[pygame.K_a]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] - 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX = False
            # 播放音效
            self.play_sound("run")
        elif self.keys[pygame.K_d]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] + 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX = True
            # 播放音效
            self.play_sound("run")
    def exit(self):
        super().exit()
        # 停止之前的所有声音效果（包括下落音效）
        pygame.mixer.stop()  # 或者使用您游戏引擎的对应API
        pass

class AttackTopState(StateBase):
    def __init__(self, animName, player, animator):
        super().__init__(animName, player, animator)

        # 设置图片路径
        base_path = "Assets/Sprites/Knight/Attack"
        Action = "AttackTop"  # 可以改为其他动作如"Attack", "Dash"等

        # 获取该动作目录下所有图片文件
        ActionFrames = sorted([f for f in os.listdir(os.path.join(base_path, Action))
                             if f.startswith(Action) and f.endswith('.PNG')])

        # 加载所有图片到列表
        ActionFrameList = []
        for img_file in ActionFrames:
            img_path = os.path.join(base_path, Action, img_file)
            image = pygame.image.load(img_path).convert_alpha()  # convert_alpha保留透明度
            ActionFrameList.append(image)

        ActionAnim=cp.SpriteAnimation("AttackTop",ActionFrameList,0.05,loop=False)
        self.animator.addAnimation(ActionAnim)

        effect_path = os.path.join("Assets/Sprites/Knight/Attack/AttackTopEffect", "AttackTopEffect_01.PNG")
        self.effect_image = pygame.image.load(effect_path).convert_alpha()

        # 初始化攻击相关变量
        self.attackTriggered = False
        self.attackOffsetX = 10  # 攻击特效的Y轴偏移量
        self.attackOffsetY = -50  # 攻击特效的Y轴偏移量

    def enter(self):
        super().enter()
        self.attackTriggered = False  # 重置触发状态
        self.animator.currentAnimation.finished = False  # 确保动画状态正确

    def update(self):
        super().update()
        
        # 当攻击动画进行到一半时触发特效
        if not self.attackTriggered and self.animator.currentAnimation.currentFrame >= len(self.animator.currentAnimation.frames) // 2:
            self.attackTriggered = True

            # 播放攻击音效
            self.play_sound("sword")

            if self.effect_image:
                # 直接绘制特效，不使用动画系统
                offsetX = self.attackOffsetX if self.animator.flipX else -self.attackOffsetX
                offsetY = self.attackOffsetY
                effect_pos = (self.player.gameObject.transform.position[0] +offsetX, 
                            self.player.gameObject.transform.position[1] + offsetY)
                
                # 特效绘制 - 可以根据游戏引擎实现方式调整
                # 这里简单示例如何绘制
                flipped_effect = pygame.transform.flip(self.effect_image, self.animator.flipX, False)
                ufb.GameObjectManager.instance.canvas.blit(flipped_effect, 
                                                        (effect_pos[0] - self.effect_image.get_width()//2,
                                                        effect_pos[1] - self.effect_image.get_height()//2))
                
        # 当动画完成时返回到空闲状态
        if self.animator.currentAnimation.finished:
            self.player.stateMachine.changeState(self.player.idleState)
        
        # 可以在攻击时允许有限的移动
        if self.keys[pygame.K_a]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] - 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX = False
            # 播放音效
            self.play_sound("run")
        elif self.keys[pygame.K_d]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] + 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX = True
            # 播放音效
            self.play_sound("run")

    def exit(self):
        super().exit()
        # 停止之前的所有声音效果（包括下落音效）
        pygame.mixer.stop()  # 或者使用您游戏引擎的对应API
        pass

class AttackBottomState(StateBase):
    def __init__(self, animName, player, animator):
        super().__init__(animName, player, animator)

        # 设置图片路径
        base_path = "Assets/Sprites/Knight/Attack"
        Action = "AttackBottom"  # 可以改为其他动作如"Attack", "Dash"等

        # 获取该动作目录下所有图片文件
        ActionFrames = sorted([f for f in os.listdir(os.path.join(base_path, Action))
                             if f.startswith(Action) and f.endswith('.PNG')])

        # 加载所有图片到列表
        ActionFrameList = []
        for img_file in ActionFrames:
            img_path = os.path.join(base_path, Action, img_file)
            image = pygame.image.load(img_path).convert_alpha()  # convert_alpha保留透明度
            ActionFrameList.append(image)

        ActionAnim=cp.SpriteAnimation("AttackBottom",ActionFrameList,0.05,loop=False)
        self.animator.addAnimation(ActionAnim)
        effect_path = os.path.join("Assets/Sprites/Knight/Attack/AttackBottomEffect", "AttackBottomEffect_01.PNG")
        self.effect_image = pygame.image.load(effect_path).convert_alpha()

        # 初始化攻击相关变量
        self.attackTriggered = False
        self.attackOffsetY = 80  # 攻击特效的Y轴偏移量
        self.attackOffsetX = 10

    def enter(self):
        super().enter()
        self.attackTriggered = False  # 重置触发状态
        self.animator.currentAnimation.finished = False  # 确保动画状态正确

    def update(self):
        super().update()
        
        # 当攻击动画进行到一半时触发特效
        if not self.attackTriggered and self.animator.currentAnimation.currentFrame >= len(self.animator.currentAnimation.frames) // 2:
            self.attackTriggered = True

            # 播放攻击音效
            self.play_sound("sword")

            if self.effect_image:
                # 直接绘制特效，不使用动画系统
                offsetX = self.attackOffsetX if self.animator.flipX else -self.attackOffsetX
                offsetY = self.attackOffsetY
                effect_pos = (self.player.gameObject.transform.position[0] +offsetX, 
                            self.player.gameObject.transform.position[1] + offsetY)
                
                # 特效绘制 - 可以根据游戏引擎实现方式调整
                # 这里简单示例如何绘制
                flipped_effect = pygame.transform.flip(self.effect_image, self.animator.flipX, False)
                ufb.GameObjectManager.instance.canvas.blit(flipped_effect, 
                                                        (effect_pos[0] - self.effect_image.get_width()//2,
                                                        effect_pos[1] - self.effect_image.get_height()//2))
                
        # 当动画完成时返回到空闲状态
        if self.animator.currentAnimation.finished:
            self.player.stateMachine.changeState(self.player.walkLoopState)
        
        # 可以在攻击时允许有限的移动
        if self.keys[pygame.K_a]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] - 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX = False
            # 播放音效
            self.play_sound("run")
        elif self.keys[pygame.K_d]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] + 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX = True
            # 播放音效
            self.play_sound("run")

    def exit(self):
        super().exit()
        # 停止之前的所有声音效果（包括下落音效）
        pygame.mixer.stop()  # 或者使用您游戏引擎的对应API
        pass



class JumpAttackState(StateBase):
    def __init__(self, animName, player, animator):
        super().__init__(animName, player, animator)

        # 设置图片路径
        base_path = "Assets/Sprites/Knight/Attack/Attack"
        Action = "Attack"  # 可以改为其他动作如"Attack", "Dash"等

        # 获取该动作目录下所有图片文件
        ActionFrames = sorted([f for f in os.listdir(os.path.join(base_path, Action))
                             if f.startswith(Action) and f.endswith('.PNG')])

        # 加载所有图片到列表
        ActionFrameList = []
        for img_file in ActionFrames:
            img_path = os.path.join(base_path, Action, img_file)
            image = pygame.image.load(img_path).convert_alpha()  # convert_alpha保留透明度
            ActionFrameList.append(image)

        ActionAnim=cp.SpriteAnimation("JumpAttack",ActionFrameList,0.05,loop=False)
        self.animator.addAnimation(ActionAnim)

        effect_path = os.path.join("Assets/Sprites/Knight/Attack/Attack/AttackEffect", "AttackEffect_01.PNG")
        self.effect_image = pygame.image.load(effect_path).convert_alpha()

        # 初始化攻击相关变量
        self.attackTriggered = False
        self.attackOffsetX = 70  # 攻击特效的X轴偏移量
        
        # 添加二段攻击相关变量
        self.combo_window_active = False     # 连击窗口是否激活
        self.combo_window_timer = 0          # 连击窗口计时器
        self.combo_window_duration = 0.3     # 连击窗口持续时间(秒)
        self.attack_key_released = False     # 攻击键是否释放（避免持续按住连击）

    def enter(self):
        super().enter()
        self.attackTriggered = False  # 重置触发状态
        self.animator.currentAnimation.finished = False  # 确保动画状态正确
        self.combo_window_active = False     # 重置连击窗口
        self.combo_window_timer = 0
        self.attack_key_released = False     # 重置攻击键状态
        
        # 获取键盘状态
        self.keys = pygame.key.get_pressed()
        
        # 检查之前是否按住了J键
        if self.keys[pygame.K_j]:
            self.attack_key_released = False
        else:
            self.attack_key_released = True

    def update(self):
        super().update()
        
        # 更新连击窗口计时器
        if self.combo_window_active:
            self.combo_window_timer += 0.016  # 假设16ms每帧
            
            # 检查是否已释放攻击键并再次按下（用于连击）
            if self.attack_key_released and self.keys[pygame.K_j]:
                self.player.stateMachine.changeState(self.player.jumpattackTwiceState)
                return
            
            # 检查连击窗口是否已过期
            if self.combo_window_timer >= self.combo_window_duration:
                self.combo_window_active = False
        
        # 检测攻击键是否释放
        if not self.keys[pygame.K_j]:
            self.attack_key_released = True
        
        # 当攻击动画进行到一半时触发特效
        if not self.attackTriggered and self.animator.currentAnimation.currentFrame >= len(self.animator.currentAnimation.frames) // 2:
            self.attackTriggered = True

            # 播放攻击音效
            self.play_sound("sword")
            
            # 这个时候也激活连击窗口
            self.combo_window_active = True
            self.combo_window_timer = 0
            
            if self.effect_image:
                # 直接绘制特效，不使用动画系统
                offset = self.attackOffsetX if self.animator.flipX else -self.attackOffsetX
                effect_pos = (self.player.gameObject.transform.position[0] + offset, 
                            self.player.gameObject.transform.position[1])
                
                # 特效绘制
                flipped_effect = pygame.transform.flip(self.effect_image, self.animator.flipX, False)
                ufb.GameObjectManager.instance.canvas.blit(flipped_effect, 
                                                        (effect_pos[0] - self.effect_image.get_width()//2,
                                                        effect_pos[1] - self.effect_image.get_height()//2))
                
        # 当动画完成时返回到空闲状态
        if self.animator.currentAnimation.finished:
            self.player.stateMachine.changeState(self.player.jumpLoopState)
        
        # 可以在攻击时允许有限的移动
        if self.keys[pygame.K_a]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] - 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX = False
        elif self.keys[pygame.K_d]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] + 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX = True
        
    def exit(self):
        super().exit()
        pass

class JumpAttackTwiceState(StateBase):
    def __init__(self, animName, player, animator):
        super().__init__(animName, player, animator)

        # 设置图片路径
        base_path = "Assets/Sprites/Knight/Attack/Attack"
        Action = "AttackTwice"  # 可以改为其他动作如"Attack", "Dash"等

        # 获取该动作目录下所有图片文件
        ActionFrames = sorted([f for f in os.listdir(os.path.join(base_path, Action))
                             if f.startswith(Action) and f.endswith('.PNG')])

        # 加载所有图片到列表
        ActionFrameList = []
        for img_file in ActionFrames:
            img_path = os.path.join(base_path, Action, img_file)
            image = pygame.image.load(img_path).convert_alpha()  # convert_alpha保留透明度
            ActionFrameList.append(image)

        ActionAnim = cp.SpriteAnimation("JumpAttackTwice", ActionFrameList, 0.05, loop=False)
        self.animator.addAnimation(ActionAnim)
        
        # 加载二段攻击特效
        effect_path = os.path.join("Assets/Sprites/Knight/Attack/Attack/AttackTwiceEffect", "AttackTwiceEffect_01.PNG")
        self.effect_image = pygame.image.load(effect_path).convert_alpha()

        # 初始化攻击相关变量
        self.attackTriggered = False
        self.attackOffsetX = 70  # 攻击特效的X轴偏移量，可以比第一段远一点

    def enter(self):
        super().enter()
        self.attackTriggered = False  # 重置触发状态
        self.animator.currentAnimation.finished = False  # 确保动画状态正确
        
        # 记录来源状态
        prev_state = self.player.stateMachine.previousState
        # 检查是否来自空中攻击状态
        self.fromJumpAttack = isinstance(prev_state, JumpAttackState)
        
    def update(self):
        super().update()
        
        # 当攻击动画进行到一半时触发特效
        if not self.attackTriggered and self.animator.currentAnimation.currentFrame >= len(self.animator.currentAnimation.frames) // 2:
            self.attackTriggered = True

            # 播放攻击音效
            self.play_sound("sword")

            if self.effect_image:
                # 直接绘制特效，不使用动画系统
                offset = self.attackOffsetX if self.animator.flipX else -self.attackOffsetX
                effect_pos = (self.player.gameObject.transform.position[0] + offset, 
                            self.player.gameObject.transform.position[1])
                
                # 特效绘制
                flipped_effect = pygame.transform.flip(self.effect_image, self.animator.flipX, False)
                ufb.GameObjectManager.instance.canvas.blit(flipped_effect, 
                                                        (effect_pos[0] - self.effect_image.get_width()//2,
                                                        effect_pos[1] - self.effect_image.get_height()//2))
                
        # 当动画完成时根据情况返回到相应状态
        if self.animator.currentAnimation.finished:
            # 如果来自空中攻击，则返回到空中循环状态
            self.player.stateMachine.changeState(self.player.jumpLoopState)
        
        # 可以在攻击时允许有限的移动
        if self.keys[pygame.K_a]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] - 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX = False
        elif self.keys[pygame.K_d]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] + 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX = True
            
    def exit(self):
        super().exit()
        pass

class JumpAttackTopState(StateBase):
    def __init__(self, animName, player, animator):
        super().__init__(animName, player, animator)

        # 设置图片路径
        base_path = "Assets/Sprites/Knight/Attack"
        Action = "AttackTop"  # 可以改为其他动作如"Attack", "Dash"等

        # 获取该动作目录下所有图片文件
        ActionFrames = sorted([f for f in os.listdir(os.path.join(base_path, Action))
                             if f.startswith(Action) and f.endswith('.PNG')])

        # 加载所有图片到列表
        ActionFrameList = []
        for img_file in ActionFrames:
            img_path = os.path.join(base_path, Action, img_file)
            image = pygame.image.load(img_path).convert_alpha()  # convert_alpha保留透明度
            ActionFrameList.append(image)

        ActionAnim=cp.SpriteAnimation("JumpAttackTop",ActionFrameList,0.05,loop=False)
        self.animator.addAnimation(ActionAnim)

        effect_path = os.path.join("Assets/Sprites/Knight/Attack/AttackTopEffect", "AttackTopEffect_01.PNG")
        self.effect_image = pygame.image.load(effect_path).convert_alpha()

        # 初始化攻击相关变量
        self.attackTriggered = False
        self.attackOffsetX = 10  # 攻击特效的Y轴偏移量
        self.attackOffsetY = -50  # 攻击特效的Y轴偏移量

    def enter(self):
        super().enter()
        self.attackTriggered = False  # 重置触发状态
        self.animator.currentAnimation.finished = False  # 确保动画状态正确

    def update(self):
        super().update()
        
        # 当攻击动画进行到一半时触发特效
        if not self.attackTriggered and self.animator.currentAnimation.currentFrame >= len(self.animator.currentAnimation.frames) // 2:
            self.attackTriggered = True

            # 播放攻击音效
            self.play_sound("sword")

            if self.effect_image:
                # 直接绘制特效，不使用动画系统
                offsetX = self.attackOffsetX if self.animator.flipX else -self.attackOffsetX
                offsetY = self.attackOffsetY
                effect_pos = (self.player.gameObject.transform.position[0] +offsetX, 
                            self.player.gameObject.transform.position[1] + offsetY)
                
                # 特效绘制 - 可以根据游戏引擎实现方式调整
                # 这里简单示例如何绘制
                flipped_effect = pygame.transform.flip(self.effect_image, self.animator.flipX, False)
                ufb.GameObjectManager.instance.canvas.blit(flipped_effect, 
                                                        (effect_pos[0] - self.effect_image.get_width()//2,
                                                        effect_pos[1] - self.effect_image.get_height()//2))
                
        # 当动画完成时返回到空闲状态
        if self.animator.currentAnimation.finished:
            self.player.stateMachine.changeState(self.player.jumpLoopState)
        
        # 可以在攻击时允许有限的移动
        if self.keys[pygame.K_a]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] - 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX = False
        elif self.keys[pygame.K_d]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] + 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX = True

    def exit(self):
        super().exit()
        pass

class JumpAttackBottomState(StateBase):
    def __init__(self, animName, player, animator):
        super().__init__(animName, player, animator)

        # 设置图片路径
        base_path = "Assets/Sprites/Knight/Attack"
        Action = "AttackBottom"  # 可以改为其他动作如"Attack", "Dash"等

        # 获取该动作目录下所有图片文件
        ActionFrames = sorted([f for f in os.listdir(os.path.join(base_path, Action))
                             if f.startswith(Action) and f.endswith('.PNG')])

        # 加载所有图片到列表
        ActionFrameList = []
        for img_file in ActionFrames:
            img_path = os.path.join(base_path, Action, img_file)
            image = pygame.image.load(img_path).convert_alpha()  # convert_alpha保留透明度
            ActionFrameList.append(image)

        ActionAnim=cp.SpriteAnimation("JumpAttackBottom",ActionFrameList,0.05,loop=False)
        self.animator.addAnimation(ActionAnim)

        effect_path = os.path.join("Assets/Sprites/Knight/Attack/AttackBottomEffect", "AttackBottomEffect_01.PNG")
        self.effect_image = pygame.image.load(effect_path).convert_alpha()

        # 初始化攻击相关变量
        self.attackTriggered = False
        self.attackOffsetY = 80  # 攻击特效的Y轴偏移量
        self.attackOffsetX = 10

    def enter(self):
        super().enter()
        self.attackTriggered = False  # 重置触发状态
        self.animator.currentAnimation.finished = False  # 确保动画状态正确

    def update(self):
        super().update()
        
        # 当攻击动画进行到一半时触发特效
        if not self.attackTriggered and self.animator.currentAnimation.currentFrame >= len(self.animator.currentAnimation.frames) // 2:
            self.attackTriggered = True

            # 播放攻击音效
            self.play_sound("sword")

            if self.effect_image:
                # 直接绘制特效，不使用动画系统
                offsetX = self.attackOffsetX if self.animator.flipX else -self.attackOffsetX
                offsetY = self.attackOffsetY
                effect_pos = (self.player.gameObject.transform.position[0] +offsetX, 
                            self.player.gameObject.transform.position[1] + offsetY)
                
                # 特效绘制 - 可以根据游戏引擎实现方式调整
                # 这里简单示例如何绘制
                flipped_effect = pygame.transform.flip(self.effect_image, self.animator.flipX, False)
                ufb.GameObjectManager.instance.canvas.blit(flipped_effect, 
                                                        (effect_pos[0] - self.effect_image.get_width()//2,
                                                        effect_pos[1] - self.effect_image.get_height()//2))
                
        # 当动画完成时返回到空闲状态
        if self.animator.currentAnimation.finished:
            self.player.stateMachine.changeState(self.player.jumpLoopState)
        
        # 可以在攻击时允许有限的移动
        if self.keys[pygame.K_a]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] - 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX = False
        elif self.keys[pygame.K_d]:
            self.player.gameObject.transform.setPosition(
            (self.player.gameObject.transform.position[0] + 10, self.player.gameObject.transform.position[1]))
            self.animator.flipX = True

    def exit(self):
        super().exit()
        pass

class SitState(StateBase):
    def __init__(self, animName, player, animator):
        super().__init__(animName, player, animator)

        # 设置图片路径
        base_path = "Assets/Sprites/Knight"
        Action = "Sit"  # 坐下动作

        ActionFrames = sorted([f for f in os.listdir(os.path.join(base_path, Action))
                             if f.startswith(Action) and f.endswith('.png')])

        # 加载所有图片到列表
        ActionFrameList = []
        for img_file in ActionFrames:
            img_path = os.path.join(base_path, Action, img_file)
            image = pygame.image.load(img_path).convert_alpha()
            ActionFrameList.append(image)

        ActionAnim = cp.SpriteAnimation("Sit", ActionFrameList, 0.05, loop=False)
        self.animator.addAnimation(ActionAnim)
        
        # 椅子引用，用于固定位置
        self.bench = None
        self.sit_position = (0, -30)  # 默认相对椅子的坐下位置

    def enter(self):
        super().enter()
        # 播放坐下音效（如果有）
        # self.play_sound("sit")  # 确保有这个音效或先检查再播放
        
        # 设置玩家为静止状态
        self.player.velocity = 0
        self.player.isGrounded = True  # 确保不会应用重力
        self.player.gravity_disabled = True  # 添加一个标记以完全禁用重力
        
        # 取消任何冲刺的余势
        self.player.dash_momentum = 0
        self.player.dash_momentum_timer = 0
              
        # 如果有任何动作限制，可以在这里设置
        self.sit_time = 0  # 跟踪已坐时间

    def update(self):
        super().update()
        
        # 确保在坐下状态下保持位置稳定
        self.player.velocity = 0
        
        # 如果有关联的椅子对象，保持位置锚定
        if self.bench:
            # 计算相对于椅子的正确位置
            sit_pos_x = self.bench.gameObject.transform.position[0] + self.sit_position[0]
            sit_pos_y = self.bench.gameObject.transform.position[1] + self.sit_position[1]
            # 如果玩家位置偏离，重新设置
            current_pos = self.player.gameObject.transform.position
            if abs(current_pos[0] - sit_pos_x) > 1 or abs(current_pos[1] - sit_pos_y) > 1:
                self.player.gameObject.transform.setPosition((sit_pos_x, sit_pos_y))

    def exit(self):
        super().exit()
        self.player.gravity_disabled = False
        self.bench = None  # 清除椅子引用


# 交互基类
class Interactable(ufb.Component):
    def __init__(self, gameObject, interaction_radius=50):
        super().__init__(gameObject)
        self.interaction_radius = interaction_radius  # 交互半径
        self.can_interact = True  # 是否可以交互
        self.is_in_range = False  # 玩家是否在范围内
        self.interaction_message = "按E键交互"  # 默认提示信息
        
    def update(self, deltaTime):
        # 获取玩家位置
        player = ufb.GameObjectManager.instance.findGameObjectByName("Player")
        if not player:
            return
            
        # 计算与玩家的距离
        player_pos = player.transform.position
        self_pos = self.gameObject.transform.position
        dx = player_pos[0] - self_pos[0]
        dy = player_pos[1] - self_pos[1]
        distance = (dx * dx + dy * dy) ** 0.5
        
        # 检查玩家是否在交互范围内
        was_in_range = self.is_in_range
        self.is_in_range = distance <= self.interaction_radius
        
        # 范围状态变化时触发事件
        if self.is_in_range and not was_in_range:
            self.on_player_enter_range()
        elif not self.is_in_range and was_in_range:
            self.on_player_exit_range()
            
        # 检查交互键按下
        if self.is_in_range and self.can_interact:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_e]:
                self.interact(player)
                
    def on_player_enter_range(self):
        """当玩家进入交互范围时调用"""
        pass
        
    def on_player_exit_range(self):
        """当玩家离开交互范围时调用"""
        pass
        
    def interact(self, player):
        """执行交互，需要被子类重写"""
        pass

class BenchInteraction(Interactable):
    # 椅子交互
    def __init__(self, gameObject):
        super().__init__(gameObject, interaction_radius=80)
        self.interaction_message = "Put E to Sit"
        self.sit_position = (0, -30)  # 坐下时相对椅子的偏移
        self.player_sitting = False
        self.prompt_font = None
        self.prompt_alpha = 0  # 透明度
        self.fade_speed = 5  # 渐变速度
        
        # 添加按键状态追踪
        self.e_key_pressed = False  # 追踪E键是否已经按下
        self.interaction_cooldown = 0.1  # 交互冷却时间(秒)
        self.cooldown_timer = 0  # 冷却计时器
        
        # 尝试加载字体
        try:
            self.prompt_font = pygame.font.Font(None, 24)  # 使用默认字体，大小24
        except:
            print("无法加载字体")
    
    def on_player_enter_range(self):
        # 显示交互提示
        self.show_interaction_prompt(True)
        
    def on_player_exit_range(self):
        # 隐藏交互提示
        self.show_interaction_prompt(False)
    
    def show_interaction_prompt(self, show):
        """控制交互提示的显示状态"""
        if show:
            self.prompt_alpha = max(0, self.prompt_alpha)  # 确保初始alpha不为负
        else:
            self.prompt_alpha = 0
    
    def render_interaction_prompt(self):
        """渲染交互提示文本"""
        if not self.prompt_font:
            return
            
        # 创建提示文本表面
        text_surface = self.prompt_font.render(self.interaction_message, True, (255, 255, 255))
        
        # 设置文本透明度
        text_surface.set_alpha(self.prompt_alpha)
        
        # 计算文本位置（在物体上方居中）
        pos_x = self.gameObject.transform.position[0] - text_surface.get_width() // 2
        pos_y = self.gameObject.transform.position[1] - 120  # 在物体上方显示
        
        # 绘制文本
        ufb.GameObjectManager.instance.canvas.blit(text_surface, (pos_x, pos_y))
    
    def interact(self, player):
        """执行与椅子的交互"""
        # 获取玩家控制器组件
        player_controller = player.getComponent(PlayerController)
        if not player_controller:
            return
            
        # 处理坐下/站起逻辑
        if not self.player_sitting:
            # 玩家坐下
            self.player_sitting = True
            self.interaction_message = "Put E to Up"
            
            # 将玩家位置微调到椅子上
            sit_pos_x = self.gameObject.transform.position[0] + self.sit_position[0]
            sit_pos_y = self.gameObject.transform.position[1] + self.sit_position[1]
            player.transform.setPosition((sit_pos_x, sit_pos_y))
            
            # 切换到坐下状态
            player_controller.stateMachine.changeState(player_controller.sitState)
            
            # 传递椅子引用给坐下状态
            player_controller.sitState.bench = self
            player_controller.sitState.sit_position = self.sit_position
            
            # 取消玩家任何冲刺的余势
            player_controller.dash_momentum = 0
            player_controller.dash_momentum_timer = 0
        else:
            # 玩家站起
            self.player_sitting = False
            self.interaction_message = "Put E to Sit"
            
            # 切换到空闲状态并确保玩家站在稳定位置（略微上移，防止掉下）
            player_pos = player.transform.position
            player.transform.setPosition((player_pos[0], player_pos[1] - 10))  # 稍微上移，避免落下
            
            # 切换到空闲状态
            player_controller.stateMachine.changeState(player_controller.idleState)

    def update(self, deltaTime):
        # 更新冷却时间
        if self.cooldown_timer > 0:
            self.cooldown_timer -= deltaTime
        
        # 获取当前键盘状态
        keys = pygame.key.get_pressed()
        
        # 检测E键的按下状态变化（从未按下到按下的瞬间）
        e_key_just_pressed = keys[pygame.K_e] and not self.e_key_pressed
        # 更新E键状态
        self.e_key_pressed = keys[pygame.K_e]
        
        # 获取玩家位置
        player = ufb.GameObjectManager.instance.findGameObjectByName("Player")
        if not player:
            return
            
        # 计算与玩家的距离
        player_pos = player.transform.position
        self_pos = self.gameObject.transform.position
        dx = player_pos[0] - self_pos[0]
        dy = player_pos[1] - self_pos[1]
        distance = (dx * dx + dy * dy) ** 0.5
        
        # 检查玩家是否在交互范围内
        was_in_range = self.is_in_range
        self.is_in_range = distance <= self.interaction_radius
        
        # 范围状态变化时触发事件
        if self.is_in_range and not was_in_range:
            self.on_player_enter_range()
        elif not self.is_in_range and was_in_range:
            self.on_player_exit_range()
            
        # 渐变显示/隐藏提示
        if self.is_in_range and self.prompt_alpha < 255:
            self.prompt_alpha = min(255, self.prompt_alpha + self.fade_speed)
        elif not self.is_in_range and self.prompt_alpha > 0:
            self.prompt_alpha = max(0, self.prompt_alpha - self.fade_speed)
            
        # 仅当提示可见时渲染
        if self.prompt_alpha > 0:
            self.render_interaction_prompt()
            
        # 检查交互键按下 - 只在按键刚按下时触发一次，并且冷却时间结束
        if self.is_in_range and self.can_interact and e_key_just_pressed and self.cooldown_timer <= 0:
            self.interact(player)
            self.cooldown_timer = self.interaction_cooldown  # 设置冷却时间