from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader
from ursina.prefabs.ursfx import ursfx

app = Ursina()
Entity.default_shader = lit_with_shadows_shader
random.seed(0)

# Environment
ground = Entity(
    model='plane', collider='box', scale=64,
    texture='grass', texture_scale=(4, 4)
)

sun = DirectionalLight()
sun.look_at(Vec3(1, -1, -1))
Sky()

# Map
Entity(model='map', scale=1, collider='mesh')

# Player
editor_camera = EditorCamera(enabled=False, ignore_paused=True)
player = FirstPersonController(
    model='cube', z=-10, color=color.orange,
    origin_y=-.5, speed=8, collider='box'
)
player.collider = BoxCollider(player, Vec3(0, 1, 0), Vec3(1, 2, 1))

# Gun
gun = Entity(
    model='Beaumont', parent=camera,
    position=(.5, -0.4, 1), scale=0.1,
    origin_z=-.5,
    rotation=(0, 180, 0),
    on_cooldown=False
)

gun.muzzle_flash = Entity(
    parent=gun, z=1, world_scale=.5,
    model='quad', color=color.yellow,
    enabled=False
)

# Shootable targets
shootables_parent = Entity()
mouse.traverse_target = shootables_parent

# Enemy class
class Enemy(Entity):
    def __init__(self, **kwargs):
        super().__init__(
            parent=shootables_parent, model='zombie', rotation=0,
            scale=0.5, origin_y=-.5,
            collider='box', **kwargs
        )
        self.health_bar = Entity(
            parent=self, y=1.2, model='cube',
            color=color.red, world_scale=(1.5, .1, .1)
        )
        self.max_hp = 100
        self._hp = self.max_hp

    def update(self):
        dist = distance_xz(player.position, self.position)
        if dist > 40:
            return

        self.health_bar.alpha = max(0, self.health_bar.alpha - time.dt)
        self.look_at_2d(player.position, 'y')
        hit_info = raycast(
            self.world_position + Vec3(0, 1, 0),
            self.forward, 30, ignore=(self,)
        )
        if hit_info.entity == player and dist > 2:
            self.position += self.forward * time.dt * 5

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, value):
        self._hp = value
        if value <= 0:
            destroy(self)
            return
        self.health_bar.world_scale_x = (self._hp / self.max_hp) * 1.5
        self.health_bar.alpha = 1

# Spawn enemies
enemies = [Enemy(x=x * 8) for x in range(5)]

# Shooting
def shoot():
    if not gun.on_cooldown:
        gun.on_cooldown = True
        gun.muzzle_flash.enabled = True
        ursfx(
            [(0.0, 0.0), (0.1, 0.9), (0.15, 0.75),
             (0.3, 0.14), (0.6, 0.0)],
            volume=0.5, wave='noise',
            pitch=random.uniform(-13, -12),
            pitch_change=-12, speed=3.0
        )
        invoke(lambda: setattr(gun.muzzle_flash, 'enabled', False), delay=2.5)
        invoke(lambda: setattr(gun, 'on_cooldown', False), delay=.4)

        hit_info = raycast(camera.world_position, camera.forward, distance=100, ignore=(player,))
        if hit_info.hit:
            if hasattr(hit_info.entity, 'hp'):
                hit_info.entity.hp -= 30
            else:
                bullet_hole = Entity(
                    model='quad',
                    texture='images/bullet.jpg',  # Replace with your bullet hole texture
                    scale=0.1,
                    color=color.black,
                    position=hit_info.point + hit_info.normal * 0.01,
                    rotation=Vec3(0, 0, 0),
                    billboard=True
                )
                bullet_hole.look_at(hit_info.point + hit_info.normal)
                destroy(bullet_hole, delay=10)

# Input and pause
def update():
    if held_keys['left mouse']:
        shoot()

def pause_input(key):
    if key == 'tab':
        editor_camera.enabled = not editor_camera.enabled
        player.visible_self = editor_camera.enabled
        player.cursor.enabled = not editor_camera.enabled
        gun.enabled = not editor_camera.enabled
        mouse.locked = not editor_camera.enabled
        editor_camera.position = player.position
        application.paused = editor_camera.enabled
    elif key == 'escape':
        application.quit()

pause_handler = Entity(ignore_paused=True, input=pause_input)

app.run()