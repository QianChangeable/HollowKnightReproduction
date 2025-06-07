import pygame
import random
import os

class GameObjectManager:
    instance=None
    def __new__(cls, *args, **kwargs):
        if cls.instance==None:
            cls.instance=super(GameObjectManager,cls).__new__(cls)
        return cls.instance
    def __init__(self,target_fps=60,fixd_delta_time=0.02,canvasWeight=1000,canvasHeight=600):
        self.gameObjects=[]
        self.gameObjectDic={}
        self.started=False
        self.canvasWeight=canvasWeight
        self.canvasHeight=canvasHeight
        self.canvas=canvas=pygame.display.set_mode((canvasWeight,canvasHeight))

        # 帧率控制相关属性
        self.clock = pygame.time.Clock()  # Pygame时钟对象
        self.target_fps = target_fps  # 目标帧率
        self.delta_time = 0  # 每帧的时间间隔(秒)
        self.fixed_delta_time = fixd_delta_time # 固定物理更新时间间隔(秒)
        self.accumulated_time = 0  # 累积的时间(用于固定更新)
        self.current_fps = 0  # 当前实际帧率
        self.frame_count = 0  # 帧计数器
        self.fps_update_time = 0  # 上次FPS更新时间

        # 初始化碰撞管理器
        self.collision_manager = CollisionManager()

    def startGame(self):
        # 初始化FPS计算相关变量
        self.fps_update_time = pygame.time.get_ticks() / 1000

        for gameObjcet in self.gameObjects:
            gameObjcet.awake()
        for gameObjcet in self.gameObjects:
            if gameObjcet.active==True:
                gameObjcet.start()

    def gameLoopLogic(self):
        # 控制帧率并获取实际帧时间
        self.delta_time = self.clock.tick(self.target_fps) / 1000.0

        # 更新FPS计数
        self.frame_count += 1
        current_time = pygame.time.get_ticks() / 1000

        # 每秒更新一次FPS显示
        if current_time - self.fps_update_time >= 1.0:
            self.current_fps = self.frame_count
            self.frame_count = 0
            self.fps_update_time = current_time

        # 更新游戏状态
        self.update()

        # 累积时间用于固定更新
        self.accumulated_time += self.delta_time

        # 执行固定更新（可能多次）
        while self.accumulated_time >= self.fixed_delta_time:
            self.fixUpdate()
            self.accumulated_time -= self.fixed_delta_time

        # 碰撞检测和响应
        self.collision_manager.update()
        
    def update(self):
        for gameObject in self.gameObjects:
            if gameObject.active==True:
                gameObject.update(self.delta_time)
    def fixUpdate(self):
        for gameObject in self.gameObjects:
            if gameObject.active==True:
                gameObject.fixUpdate()
    def addGameobject(self,gameObject):
        if gameObject.name in self.gameObjectDic:
            print("添加物体失败！试图添加相同名称的物体")
            return
        else:
            self.gameObjectDic[gameObject.name]=gameObject
        if self.started==False:
            self.gameObjects.append(gameObject)
        else:
            gameObject.awake()
            if gameObject.active==True:
                gameObject.start()
    def findGameObjectByName(self,name):
        if name in self.gameObjectDic.keys():
            return self.gameObjectDic[name]
        print("没有找到名为{name}的物体")
        return None

    def setTargetFPS(self, fps):
        """设置目标帧率"""
        self.target_fps = fps

class GameObject:
    def __init__(self,name,active=True):
        self.name=name
        self.transform=None
        self.components=[]
        self.active=active
        self.started=False
        self.awaked=False
        GameObjectManager.instance.addGameobject(self)
    def awake(self):
        if self.awaked==True:
            return
        for component in self.components:
            if component.enable:
                component.awake()
        self.awaked=True
    def start(self):
        #如果物体没有被激活则直接不调用
        if self.active==False:
            return
        if self.started!=False:
            return
        for component in self.components:
            if component.enable:
                component.start()
        self.started=True

    def update(self,deltaTime):
        if self.active==False:
            return
        for component in self.components:
            if component.enable:
                component.update(deltaTime)

    def fixUpdate(self):
        if self.active==False:
            return
        for component in self.components:
            if component.enable:
                component.fixUpdate()
    def onEnable(self):
        if self.active==True:
            for component in self.components:
                component.onEnable()
    def onDisable(self):
        if self.active==False:
            for component in self.components:
                component.onDisable()
    def onDestroy(self):
        for component in self.components:
            component.onDestroy()
    def addComponent(self,componentType,*args,**kwargs):
        for component in self.components:
            if isinstance(component,componentType):
                print("添加组件失败： 尝试重复添加相同组件！")
                return
        component=componentType(self,*args,**kwargs)
        if component==None:
            print("实例化组件失败！")
            return
        if component.__class__.__name__=="Transform":
            self.transform=component
        self.components.append(component)
        print("添加 "+ str(componentType)+" 组件成功！")
        return component

    def getComponent(self,componentType):
        for component in self.components:
            if isinstance(component,componentType):
                return component
        else: return None

class Component:
    #所有组件的基类
    def __init__(self,gameObject):
        self.gameObject=gameObject
        self.enable=True
    def awake(self):
        print(self.__class__.__name__+"awake")
        pass
    def start(self):
        print(self.__class__.__name__ + "start")
        pass
    def onEnable(self):
        pass
    def update(self,deltaTime):
        pass
    def fixUpdate(self):
        pass
    def onDisable(self):
        pass
    def onDestroy(self):
        pass

class CollisionManager:
    def __init__(self):
        self.colliders = []
        self.collision_pairs = {}  # 跟踪已经发生碰撞的对象对
        self.debug_draw = False  # 是否绘制碰撞体的调试视图

    def add_collider(self, collider):
        """添加碰撞体到管理器"""
        if collider not in self.colliders:
            self.colliders.append(collider)

    def remove_collider(self, collider):
        """从管理器中移除碰撞体"""
        if collider in self.colliders:
            self.colliders.remove(collider)
            # 清理碰撞记录
            pairs_to_remove = []
            for pair in self.collision_pairs:
                if collider in pair:
                    pairs_to_remove.append(pair)
            
            for pair in pairs_to_remove:
                del self.collision_pairs[pair]

    def update(self):
        """更新所有碰撞检测"""
        # 创建当前帧的碰撞对集合
        current_collisions = set()
        
        # 检测所有碰撞体之间的碰撞
        for i, collider1 in enumerate(self.colliders):
            if not collider1.enabled or not collider1.gameObject.active:
                continue
                
            for collider2 in self.colliders[i+1:]:
                if not collider2.enabled or not collider2.gameObject.active:
                    continue
                    
                # 跳过同一游戏对象上的碰撞体之间的检测
                if collider1.gameObject == collider2.gameObject:
                    continue
                
                # 确保碰撞对的排序一致性
                collision_pair = tuple(sorted([collider1, collider2], key=id))
                
                # 检查碰撞
                is_colliding = collider1.check_collision(collider2)
                
                if is_colliding:
                    current_collisions.add(collision_pair)
                    
                    # 如果这是新的碰撞
                    if collision_pair not in self.collision_pairs:
                        self.collision_pairs[collision_pair] = True
                        
                        # 触发Enter事件
                        if collider1.isTrigger or collider2.isTrigger:
                            collider1.on_trigger_enter(collider2)
                            collider2.on_trigger_enter(collider1)
                        else:
                            collider1.on_collision_enter(collider2)
                            collider2.on_collision_enter(collider1)
                    else:
                        # 触发Stay事件
                        if collider1.isTrigger or collider2.isTrigger:
                            collider1.on_trigger_stay(collider2)
                            collider2.on_trigger_stay(collider1)
                        else:
                            collider1.on_collision_stay(collider2)
                            collider2.on_collision_stay(collider1)
                            
        # 检查结束的碰撞
        ended_collisions = set(self.collision_pairs.keys()) - current_collisions
        for collision_pair in ended_collisions:
            collider1, collider2 = collision_pair
            del self.collision_pairs[collision_pair]
            
            # 触发Exit事件
            if collider1.isTrigger or collider2.isTrigger:
                collider1.on_trigger_exit(collider2)
                collider2.on_trigger_exit(collider1)
            else:
                collider1.on_collision_exit(collider2)
                collider2.on_collision_exit(collider1)
        
        # 绘制碰撞体调试视图
        if self.debug_draw:
            for collider in self.colliders:
                if hasattr(collider, 'draw_debug') and collider.enabled:
                    collider.draw_debug()
    
    def toggle_debug_draw(self):
        """切换碰撞体调试视图的显示状态"""
        self.debug_draw = not self.debug_draw

class AudioManager:
    _instance = None
    
    def __init__(self):
        if AudioManager._instance is not None:
            raise Exception("AudioManager is a singleton class")
        else:
            AudioManager._instance = self
            
        pygame.mixer.init()  # 初始化音频系统
        self.sounds = {}     # 存储单个加载的音效
        self.sound_groups = {}  # 存储音效组，每个组包含多个相似音效
        self.volumes = {     # 音效类别的音量配置
            "Others": 0.5,
        }
        
        # 加载所有音效
        self._load_all_sounds()
    
    @staticmethod
    def get_instance():
        """获取单例实例"""
        if AudioManager._instance is None:
            AudioManager()
        return AudioManager._instance
    
    def _load_all_sounds(self):
        """加载所有音效文件"""
        # 单个音效
        sound_categories = {
            "Knight": ["run","dash", "land","jump","doublejump","falling"],
        }
        
        # 音效组 - 每个动作的多个变体
        sound_group_categories = {
            "Knight": {
                "sword": 3,      # sword_2 3 4
            }
        }
        
        # 加载单个音效
        for category, sound_names in sound_categories.items():
            for sound_name in sound_names:
                path = f"Assets/Audios/{category}/{sound_name}.wav"
                if os.path.exists(path):
                    sound = pygame.mixer.Sound(path)
                    sound.set_volume(self.volumes.get(category, 0.5))
                    self.sounds[sound_name] = sound
                    print(f"Loaded sound: {sound_name}")
        
        # 加载音效组
        for category, groups in sound_group_categories.items():
            for group_name, count in groups.items():
                self.sound_groups[group_name] = []
                
                for i in range(1, count + 1):
                    sound_name = f"{group_name}{i}"
                    path = f"Assets/Audios/{category}/{sound_name}.wav"
                    
                    if os.path.exists(path):
                        sound = pygame.mixer.Sound(path)
                        sound.set_volume(self.volumes.get(category, 0.5))
                        self.sound_groups[group_name].append(sound)
                        print(f"Loaded sound for group {group_name}: {sound_name}")
    
    def play_sound(self, sound_name):
        """播放指定名称的音效"""
        if sound_name in self.sounds:
            self.sounds[sound_name].play()
        elif sound_name in self.sound_groups:
            # 如果是音效组，随机选择一个播放
            if self.sound_groups[sound_name]:
                random.choice(self.sound_groups[sound_name]).play()
        else:
            print(f"Sound not found: {sound_name}")
    
    def set_volume(self, category, volume):
        """设置某个类别的音量 (0.0 to 1.0)"""
        if category in self.volumes:
            self.volumes[category] = max(0.0, min(1.0, volume))
            
            # 更新该类别下所有音效的音量
            for name, sound in self.sounds.items():
                if any(name.startswith(key) for key in self.volumes.keys() if key == category):
                    sound.set_volume(self.volumes[category])
            
            # 更新音效组的音量
            for group_name, sounds in self.sound_groups.items():
                if any(group_name.startswith(key) for key in self.volumes.keys() if key == category):
                    for sound in sounds:
                        sound.set_volume(self.volumes[category])

    def play_background_music(self, music_file, volume=0.5, loop=-1):
        """
        播放背景音乐
        
        参数:
            music_file: 音乐文件路径
            volume: 音量，范围0.0-1.0
            loop: 循环次数，-1表示无限循环
        """
        pygame.mixer.music.load(music_file)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loop)
        
    def stop_background_music(self):
        """停止背景音乐"""
        pygame.mixer.music.stop()
        
    def pause_background_music(self):
        """暂停背景音乐"""
        pygame.mixer.music.pause()
        
    def resume_background_music(self):
        """恢复播放背景音乐"""
        pygame.mixer.music.unpause()
        
    def set_music_volume(self, volume):
        """设置背景音乐音量"""
        pygame.mixer.music.set_volume(volume)