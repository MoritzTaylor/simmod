"""
Modification Framework for the Mujoco simulator based on mujoco-py library.

Unadapted version from:
https://github.com/openai/mujoco-py/blob/master/mujoco_py/modder.py

Additional resource:
https://github.com/ARISE-Initiative/robosuite/blob/65d3b9ad28d6e7a006e9eef7c5a0330816483be4/robosuite/utils/mjmod.py

Copyright (c) 2021, Moritz Schneider
@Author: Moritz Schneider
"""

from collections import defaultdict
from enum import Enum
from typing import AnyStr, List, Union, Dict, Tuple

import numpy as np
from mujoco_py import cymj, functions

import warnings

from simmod.modification.base_modifier import BaseModifier, register_as_setter
from simmod.utils.typings_ import *
from simmod.utils import rotations


class MujocoBaseModifier(BaseModifier):

    def __init__(
            self,
            sim,
            *args,
            **kwargs
    ) -> None:
        self.sim = sim
        super().__init__(*args, **kwargs)

    @property
    def model(self):
        return self.sim.model

    def update(self):
        """
        Propagates the changes made up to this point through the simulation
        """
        self.sim.set_constants()
        self.sim.forward()


class MujocoLightModifier(MujocoBaseModifier):

    def __init__(self, *args, **kwargs):
        self._default_config_file_path = 'data/mujoco/default_light_config.yaml'
        super().__init__(*args, **kwargs)

    @property
    def names(self) -> List:
        return self.model.light_names

    @register_as_setter("pos")
    def set_pos(self, name: AnyStr, value: Array) -> None:
        lightid = self.get_lightid(name)
        assert lightid > -1, "Unknown light %s" % name

        value = list(value)
        assert len(value) == 3, "Expected 3-dim value, got %s" % value

        self.model.light_pos[lightid] = value

    @register_as_setter("dir")
    def set_dir(self, name: AnyStr, value: Array) -> None:
        lightid = self.get_lightid(name)
        assert lightid > -1, "Unknown light %s" % name

        value = list(value)
        assert len(value) == 3, "Expected 3-dim value, got %s" % value

        self.model.light_dir[lightid] = value

    # TODO: Bool instead of int-value?
    @register_as_setter("active")
    def set_active(self, name: AnyStr, value: int) -> None:
        lightid = self.get_lightid(name)
        assert lightid > -1, "Unknown light %s" % name
        assert value >= 0 or value <= 1, "Expected value in [0, 1], got %s" % value
        self.model.light_active[lightid] = round(value)

    @register_as_setter("specular")
    def set_specular(self, name: AnyStr, value: Array) -> None:
        lightid = self.get_lightid(name)
        assert lightid > -1, "Unknown light %s" % name

        value = list(value)
        assert len(value) == 3, "Expected 3-dim value, got %s" % value

        self.model.light_specular[lightid] = value

    @register_as_setter("ambient")
    def set_ambient(self, name: AnyStr, value: Array) -> None:
        lightid = self.get_lightid(name)
        assert lightid > -1, "Unknown light %s" % name

        value = list(value)
        assert len(value) == 3, "Expected 3-dim value, got %s" % value

        self.model.light_ambient[lightid] = value

    @register_as_setter("diffuse")
    def set_diffuse(self, name: AnyStr, value: Array) -> None:
        lightid = self.get_lightid(name)
        assert lightid > -1, "Unknown light %s" % name

        value = list(value)
        assert len(value) == 3, "Expected 3-dim value, got %s" % value

        self.model.light_diffuse[lightid] = value

    # TODO: Int instead of bool-value?
    @register_as_setter("castshadow")
    def set_castshadow(self, name: AnyStr, value: bool) -> None:
        lightid = self.get_lightid(name)
        assert lightid > -1, "Unkwnown light %s" % name
        self.model.light_castshadow[lightid] = value

    def get_lightid(self, name) -> int:
        return self.model.light_name2id(name)


class MujocoCameraModifier(MujocoBaseModifier):

    def __init__(self, *args, **kwargs):
        self._default_config_file_path = 'data/mujoco/default_camera_config.yaml'
        super().__init__(*args, **kwargs)

    @property
    def names(self) -> List:
        return self.model.camera_names

    @register_as_setter("fovy")
    def set_fovy(self, name: AnyStr, value: float) -> None:
        camid = self.get_camid(name)
        assert 0 < value < 180
        assert camid > -1, "Unknown camera %s" % name
        self.model.cam_fovy[camid] = value

    def set_ipd(self, name: AnyStr, value: float) -> None:
        camid = self.get_camid(name)
        assert 0 < value < 180
        assert camid > -1, "Unknown camera %s" % name
        self.model.cam_fovy[camid] = value

    def get_quat(self, name: AnyStr) -> None:
        camid = self.get_camid(name)
        assert camid > -1, "Unknown camera %s" % name
        return self.model.cam_quat[camid]

    @register_as_setter("euler")
    def set_euler(self, name: AnyStr, value: Array) -> None:
        value = list(value)
        assert len(value) == 3, "Expected value of length 3, instead got %s" % value
        value = rotations.euler2quat(value)
        self.set_quat(name, value)

    @register_as_setter("quat")
    def set_quat(self, name: AnyStr, value: Array) -> None:
        value = list(value)
        assert len(value) == 4, "Expected value of length 4, instead got %s" % value
        camid = self.get_camid(name)
        assert camid > -1, "Unknown camera %s" % name
        self.model.cam_quat[camid] = value

    def get_pos(self, name: AnyStr) -> None:
        camid = self.get_camid(name)
        assert camid > -1, "Unknown camera %s" % name
        return self.model.cam_pos[camid]

    @register_as_setter("pos")
    def set_pos(self, name: AnyStr, value: Array) -> None:
        value = list(value)
        assert len(value) == 3, "Expected value of length 3, instead got %s" % value
        camid = self.get_camid(name)
        assert camid > -1
        self.model.cam_pos[camid] = value

    def get_camid(self, name: AnyStr) -> int:
        return self.model.camera_name2id(name)


class MujocoMaterialModifier(MujocoBaseModifier):
    """
    Modify material properties of a model. Example use:

        sim = MjSim(...)
        modder = MaterialModifier(sim)
        modder.set_specularity('some_geom', 0.5)
        modder.rand_all('another_geom')

    """

    def __init__(self, *args, **kwargs) -> None:
        self._default_config_file_path = 'data/mujoco/default_material_config.yaml'
        super().__init__(*args, **kwargs)

    @property
    def names(self) -> List:
        return self.model.geom_names

    @register_as_setter("specular")
    def set_specularity(self, name: AnyStr, value: float) -> None:
        assert 0 <= value <= 1.0
        mat_id = self.get_mat_id(name)
        self.model.mat_specular[mat_id] = value

    @register_as_setter("shininess")
    def set_shininess(self, name: AnyStr, value: float) -> None:
        assert 0 <= value <= 1.0
        mat_id = self.get_mat_id(name)
        self.model.mat_shininess[mat_id] = value

    @register_as_setter("reflectance")
    def set_reflectance(self, name: AnyStr, value: float) -> None:
        assert 0 <= value <= 1.0
        mat_id = self.get_mat_id(name)
        self.model.mat_reflectance[mat_id] = value

    def set_texrepeat(self, name: AnyStr, repeat_x: int, repeat_y: int) -> None:
        mat_id = self.get_mat_id(name)
        # ensure the following is set to false, so that repeats are
        # relative to the extent of the body.
        self.model.mat_texuniform[mat_id] = 0
        self.model.mat_texrepeat[mat_id, :] = [repeat_x, repeat_y]

    def rand_texrepeat(self, name: AnyStr, max_repeat: int = 5) -> None:
        repeat_x = self.random_state.randint(0, max_repeat) + 1
        repeat_y = self.random_state.randint(0, max_repeat) + 1
        self.set_texrepeat(name, repeat_x, repeat_y)

    def get_mat_id(self, name: AnyStr) -> int:
        """ Returns the material id based on the geom name. """
        geom_id = self.model.geom_name2id(name)
        return self.model.geom_matid[geom_id]


# From mjtTexture
MJT_TEXTURE_ENUM = ['2d', 'cube', 'skybox']


class Texture:
    """
    Helper class for operating on the MuJoCo textures.
    """

    __slots__ = ['id', 'type', 'height', 'width', 'tex_adr', 'tex_rgb']

    def __init__(self, model, tex_id: int) -> None:
        self.id = tex_id
        self.type = MJT_TEXTURE_ENUM[model.tex_type[tex_id]]
        self.height = model.tex_height[tex_id]
        self.width = model.tex_width[tex_id]
        self.tex_adr = model.tex_adr[tex_id]
        self.tex_rgb = model.tex_rgb

    @property
    def bitmap(self):
        size = self.height * self.width * 3
        data = self.tex_rgb[self.tex_adr:self.tex_adr + size]
        return data.reshape((self.height, self.width, 3))


class MujocoTextureModifier(MujocoBaseModifier):
    """
    Modify textures in model. Example use:

        sim = MjSim(...)
        modder = TextureModifier(sim)
        modder.whiten_materials()  # ensures materials won't impact colors
        modder.set_checker('some_geom', (255, 0, 0), (0, 0, 0))
        modder.rand_all('another_geom')

    Note: in order for the textures to take full effect, you'll need to set
    the rgba values for all materials to [1, 1, 1, 1], otherwise the texture
    colors will be modulated by the material colors. Call the
    `whiten_materials` helper method to set all material colors to white.
    """

    def __init__(self, *args, **kwargs) -> None:
        self._default_config_file_path = 'data/mujoco/default_texture_config.yaml'
        super().__init__(*args, **kwargs)

        self.textures = [Texture(self.model, i)
                         for i in range(self.model.ntex)]
        self._build_tex_geom_map()

        # These matrices will be used to rapidly synthesize
        # checker pattern bitmaps
        self._cache_checker_matrices()

    @property
    def names(self) -> List:
        return self.model.geom_names

    def get_texture(self, name: AnyStr) -> Texture:
        if name == 'skybox':
            tex_id = -1
            for i in range(self.model.ntex):
                # TODO: Don't hardcode this
                skybox_textype = 2
                if self.model.tex_type[i] == skybox_textype:
                    tex_id = i
            assert tex_id >= 0, "Model has no skybox"
        else:
            geom_id = self.model.geom_name2id(name)
            mat_id = self.model.geom_matid[geom_id]
            assert mat_id >= 0, "Geom has no assigned material"
            tex_id = self.model.mat_texid[mat_id]
            assert tex_id >= 0, "Material has no assigned texture"

        texture = self.textures[tex_id]

        return texture

    def get_checker_matrices(self, name: AnyStr):
        if name == 'skybox':
            return self._skybox_checker_mat
        else:
            geom_id = self.model.geom_name2id(name)
            return self._geom_checker_mats[geom_id]

    @register_as_setter("checker")
    def set_checker(self, name: AnyStr, rgb1: RGB, rgb2: RGB):
        geom_id, mat_id, tex_id = self.get_ids(name)

        if tex_id < 0:
            warnings.warn("Setting checker texture only available for Textures. "
                          "Make sure to define Textures in the corresponding XML to use this feature.")
            return

        bitmap = self.get_texture(name).bitmap
        cbd1, cbd2 = self.get_checker_matrices(name)

        rgb1 = np.asarray(rgb1).reshape([1, 1, -1])
        rgb2 = np.asarray(rgb2).reshape([1, 1, -1])
        bitmap[:] = rgb1 * cbd1 + rgb2 * cbd2

        self.upload_texture(name)
        return bitmap

    def get_rgb(self, name) -> Array:
        """
        Grabs rgb color of a specific geom

        Args:
            name (str): Name of the geom
        Returns:
            np.array: (r,g,b) geom colors
        """
        geom_id, mat_id, tex_id = self.get_ids(name)

        if tex_id >= 0 or name == 'skybox':
            bitmap = self.get_texture(name).bitmap
            return bitmap[..., :]
        elif mat_id >= 0 and tex_id < 0:
            # Warn the user if changing mat_rgba has no effect!
            if self.model.geom_rgba[geom_id] != [0.5, 0.5, 0.5, 1]:
                return self.model.geom_rgba[geom_id, :3]
            return self.model.mat_rgba[geom_id, :3]
        else:
            geom_id = self.model.geom_name2id(name)
            return self.model.geom_rgba[geom_id, :3]

    @register_as_setter("gradient")
    def set_gradient(self, name: AnyStr, rgb1: RGB, rgb2: RGB, vertical: bool = True):
        """
        Creates a linear gradient from rgb1 to rgb2.

        Args:
        - rgb1 (array): start color
        - rgb2 (array): end color
        - vertical (bool): if True, the gradient in the positive
            y-direction, if False it's in the positive x-direction.
        """
        # NOTE: MuJoCo's gradient uses a sigmoid. Here we simplify
        # and just use a linear gradient... We could change this
        # to just use a tanh-sigmoid if needed.
        geom_id, mat_id, tex_id = self.get_ids(name)

        if tex_id < 0:
            warnings.warn("Setting gradient only available for Textures. "
                          "Make sure to define Textures in the corresponding XML to use this feature.")
            return

        bitmap = self.get_texture(name).bitmap
        h, w = bitmap.shape[:2]
        if vertical:
            p = np.tile(np.linspace(0, 1, h)[:, None], (1, w))
        else:
            p = np.tile(np.linspace(0, 1, w), (h, 1))

        for i in range(3):
            bitmap[..., i] = rgb2[i] * p + rgb1[i] * (1.0 - p)

        self.upload_texture(name)
        return bitmap

    def get_ids(self, name: AnyStr):
        geom_id = self.model.geom_name2id(name)
        mat_id = self.model.geom_matid[geom_id]
        tex_id = self.model.mat_texid[mat_id]
        return geom_id, mat_id, tex_id

    @register_as_setter("rgb")
    def set_rgb(self, name: AnyStr, rgb: RGB) -> Optional[Array]:
        geom_id, mat_id, tex_id = self.get_ids(name)

        rgb = np.round(rgb) / 255.

        if tex_id >= 0 or name == 'skybox':
            bitmap = self.get_texture(name).bitmap
            bitmap[..., :] = np.asarray(rgb)
            self.upload_texture(name)
            return bitmap
        else:
            if mat_id >= 0 and tex_id < 0:
                warnings.warn("Changing material rgba value does not effect the sim. "
                              "Changing corresponding geometry rgba value instead.")
                # TODO: One material can be used for multiple objects; should we change each one of them simultaneously?
            self.model.geom_rgba[geom_id, :3] = rgb

    @register_as_setter("noise")
    def set_noise(self, name: AnyStr, rgb1: RGB, rgb2: RGB, fraction: float = 0.9):
        """
        Args:
        - name (str): name of geom
        - rgb1 (array): background color
        - rgb2 (array): color of mod_func noise foreground color
        - fraction (float): fraction of pixels with foreground color
        """
        geom_id, mat_id, tex_id = self.get_ids(name)

        if tex_id < 0:
            warnings.warn("Setting noise only available for Textures. "
                          "Make sure to define Textures in the corresponding XML to use this feature.")
            return

        bitmap = self.get_texture(name).bitmap
        h, w = bitmap.shape[:2]
        mask = self.random_state.uniform(size=(h, w)) < fraction

        bitmap[..., :] = np.asarray(rgb1)
        bitmap[mask, :] = np.asarray(rgb2)

        self.upload_texture(name)
        return bitmap

    @register_as_setter("size")
    def set_size(self, name: AnyStr, value: Array):
        geom_id = self.model.geom_name2id(name)
        assert geom_id > -1, "Unknown geom from body %s" % name

        value = list(value)
        assert len(value) == 3, "Expected 3-dim value, got %s" % value

        self.model.geom_size[geom_id] = value
        self.sim.set_constants()

    def get_size(self, name: AnyStr):
        geom_id = self.model.geom_name2id(name)
        assert geom_id > -1, "Unknown geom from body %s" % name

        return self.model.geom_size[geom_id]

    def rand_checker(self, name: AnyStr):
        rgb1, rgb2 = self.get_rand_rgb(2)
        return self.set_checker(name, rgb1, rgb2)

    def rand_gradient(self, name: AnyStr):
        rgb1, rgb2 = self.get_rand_rgb(2)
        vertical = bool(self.random_state.uniform() > 0.5)
        return self.set_gradient(name, rgb1, rgb2, vertical=vertical)

    def rand_rgb(self, name: AnyStr) -> Optional[Array]:
        rgb = self.get_rand_rgb()
        return self.set_rgb(name, rgb)

    def rand_noise(self, name: AnyStr):
        fraction = 0.1 + self.random_state.uniform() * 0.8
        rgb1, rgb2 = self.get_rand_rgb(2)
        return self.set_noise(name, rgb1, rgb2, fraction)

    def upload_texture(self, name: AnyStr):
        """Uploads the texture to the GPU so it's available in the rendering."""
        texture = self.get_texture(name)
        if not self.sim.render_contexts:
            cymj.MjRenderContextOffscreen(self.sim)
        for render_context in self.sim.render_contexts:
            render_context.upload_texture(texture.id)

    def whiten_materials(self, geom_names=None) -> None:
        """
        Helper method for setting all material colors to white, otherwise
        the texture setters won't take full effect.

        Args:
        - geom_names (list): list of geom names whose materials should be
            set to white. If omitted, all materials will be changed.
        """
        geom_names = geom_names or []
        if geom_names:
            for name in geom_names:
                geom_id = self.model.geom_name2id(name)
                mat_id = self.model.geom_matid[geom_id]
                self.model.mat_rgba[mat_id, :] = 1.0
        else:
            self.model.mat_rgba[:] = 1.0

    def get_rand_rgb(self, n=1):
        def _rand_rgb():
            return np.array(self.random_state.uniform(size=3) * 255, dtype=np.uint8)

        if n == 1:
            return _rand_rgb()
        else:
            return tuple(_rand_rgb() for _ in range(n))

    def _build_tex_geom_map(self) -> None:
        # Build a map from tex_id to geom_ids, so we can check
        # for collisions.
        self._geom_ids_by_tex_id = defaultdict(list)
        for geom_id in range(self.model.ngeom):
            mat_id = self.model.geom_matid[geom_id]
            if mat_id >= 0:
                tex_id = self.model.mat_texid[mat_id]
                if tex_id >= 0:
                    self._geom_ids_by_tex_id[tex_id].append(geom_id)

    def _cache_checker_matrices(self) -> None:
        """
        Cache two matrices of the form [[1, 0, 1, ...],
                                        [0, 1, 0, ...],
                                        ...]
        and                            [[0, 1, 0, ...],
                                        [1, 0, 1, ...],
                                        ...]
        for each texture. To use for fast creation of checkerboard patterns
        """
        self._geom_checker_mats = []
        for geom_id in range(self.model.ngeom):
            mat_id = self.model.geom_matid[geom_id]
            tex_id = self.model.mat_texid[mat_id]
            texture = self.textures[tex_id]
            h, w = texture.bitmap.shape[:2]
            self._geom_checker_mats.append(self._make_checker_matrices(h, w))

        # add skybox
        skybox_tex_id = -1
        for tex_id in range(self.model.ntex):
            skybox_textype = 2
            if self.model.tex_type[tex_id] == skybox_textype:
                skybox_tex_id = tex_id
        if skybox_tex_id >= 0:
            texture = self.textures[skybox_tex_id]
            h, w = texture.bitmap.shape[:2]
            self._skybox_checker_mat = self._make_checker_matrices(h, w)
        else:
            self._skybox_checker_mat = None

    def _make_checker_matrices(self, h, w):
        re = np.r_[((w + 1) // 2) * [0, 1]]
        ro = np.r_[((w + 1) // 2) * [1, 0]]
        cbd1 = np.expand_dims(np.row_stack(((h + 1) // 2) * [re, ro]), -1)[:h, :w]
        cbd2 = np.expand_dims(np.row_stack(((h + 1) // 2) * [ro, re]), -1)[:h, :w]
        return cbd1, cbd2


class mjtJoint(Enum):
    mjJNT_FREE = 0
    mjJNT_BALL = 1
    mjJNT_SLIDE = 2
    mjJNT_HINGE = 3


class MujocoJointModifier(MujocoBaseModifier):

    def __init__(self, *args, **kwargs) -> None:
        self._default_config_file_path = 'data/mujoco/default_joint_config.yaml'
        super().__init__(*args, **kwargs)

    @property
    def names(self) -> List:
        return self.model.joint_names

    def _get_joint_type(self, name: AnyStr) -> mjtJoint:
        jointid = self._get_jointid(name)
        joint_type = self.model.jnt_type[jointid]
        return mjtJoint(joint_type)

    def _get_jointid(self, name: AnyStr) -> int:
        return self.model.joint_name2id(name)

    def _get_joint_dofadr(self, name: AnyStr):
        jointid = self._get_jointid(name)
        return self.model.jnt_dofadr[jointid]

    @register_as_setter("range")
    def set_range(self, name: AnyStr, value: Array) -> None:
        """
        Values should be in radian. If simulation assumes degree values
        this will be automatically converted. TODO
        """
        jointid = self._get_jointid(name)
        assert jointid > -1, "Unknown joint %s" % name
        value = list(value)
        assert len(value) == 2, "Expected 2-dim value, got %s" % value
        self.model.jnt_range[jointid] = value

    @register_as_setter("damping")
    def set_damping(self, name: AnyStr, value: float) -> None:
        jointid = self._get_jointid(name)
        assert jointid > -1, "Unknown joint %s" % name
        joint_type = self._get_joint_type(name)
        if joint_type == mjtJoint.mjJNT_FREE:
            pass  # TODO: Difference between different types of joints
        joint_dofadr = self._get_joint_dofadr(name)
        self.model.dof_damping[joint_dofadr] = value

    @register_as_setter("armature")
    def set_armature(self, name: AnyStr, value: float) -> None:
        jointid = self._get_jointid(name)
        assert jointid > -1, "Unknown joint %s" % name
        joint_dofadr = self._get_joint_dofadr(name)
        self.model.dof_armature[joint_dofadr] = value

    @register_as_setter("stiffness")
    def set_stiffness(self, name: AnyStr, value: float) -> None:
        jointid = self._get_jointid(name)
        assert jointid > -1, "Unknown joint %s" % name

        self.model.jnt_stiffness[jointid] = value

    @register_as_setter("frictionloss")
    def set_frictionloss(self, name: AnyStr, value: float) -> None:
        jointid = self._get_jointid(name)
        assert jointid > -1, "Unknown joint %s" % name
        joint_dofadr = self._get_joint_dofadr(name)
        self.model.dof_frictionloss[joint_dofadr] = value

    def get_quat(self, name: AnyStr) -> Array:
        jointid = self._get_jointid(name)
        assert jointid > -1, "Unknown joint %s" % name
        return self.model.jnt_quat[jointid]

    @register_as_setter("quat")
    def set_quat(self, name, value: Array) -> None:
        value = list(value)
        assert len(value) == 4, (
                "Expectd value of length 4, instead got %s" % value)
        jointid = self._get_jointid(name)
        assert jointid > -1, "Unknown joint %s" % name
        self.model.jnt_quat[jointid] = value

    def get_pos(self, name: AnyStr) -> Array:
        jointid = self._get_jointid(name)
        assert jointid > -1, "Unknown joint %s" % name
        return self.model.jnt_pos[jointid]

    @register_as_setter("pos")
    def set_pos(self, name: AnyStr, value: Array) -> None:
        value = list(value)
        assert len(value) == 3, (
                "Expected value of length 3, instead got %s" % value)
        jointid = self._get_jointid(name)
        assert jointid > -1
        self.model.jnt_pos[jointid] = value


class MujocoBodyModifier(MujocoBaseModifier):
    """Integrates attributes of XML references 'geom' and 'inertial' """

    def __init__(self, *args, **kwargs) -> None:
        self._default_config_file_path = 'data/mujoco/default_body_config.yaml'
        super().__init__(*args, **kwargs)

    @property
    def names(self) -> List:
        return self.model.body_names

    def _get_bodyid(self, name: AnyStr) -> int:
        assert self.model.body_name2id(name) > -1, "Unknown body %s" % name
        return self.model.body_name2id(name)

    def set_geom_type(self, name: AnyStr, value: int):
        bodyid = self._get_bodyid(name)

        if self.model.geom_type[bodyid] == 7:
            return
        self.model.geom_type[bodyid] = value

    @register_as_setter("pos")
    def set_pos(self, name: AnyStr, value: Array) -> None:
        value = list(value)
        assert len(value) == 3, (
                "Expected value of length 3, instead got %s" % value)
        bodyid = self._get_bodyid(name)
        self.model.body_pos[bodyid] = value
        self.update()

    @register_as_setter("mass")
    def set_mass(self, name: AnyStr, value: float) -> None:
        bodyid = self._get_bodyid(name)

        self.model.body_mass[bodyid] = value
        self.update()

    @register_as_setter("diaginerta")
    def set_diaginertia(self, name: AnyStr, value: Array) -> None:
        bodyid = self._get_bodyid(name)

        value = list(value)
        assert len(value) == 3, "Expected 3-dim value, got %s" % value

        self.model.body_inertia[bodyid] = value
        self.update()

    def set_fullinertia(self, name: AnyStr, value: Array) -> None:
        bodyid = self._get_bodyid(name)

        value = list(value)
        assert len(value) == 6, "Expected 6-dim value, got %s" % value

        # TODO: Transformation to principal inertias

        self.model.body_inertia[bodyid] = value
        self.update()

    @register_as_setter("friction")
    def set_friction(self, name: AnyStr, value: Array) -> None:
        bodyid = self._get_bodyid(name)
        geomid = self.model.body_geomadr[bodyid]
        assert geomid > -1, "Unknown geom from body %s" % name

        value = list(value)
        assert len(value) == 3, "Expected 3-dim value, got %s" % value

        self.model.geom_friction[geomid] = value
        self.update()

    def get_quat(self, name: AnyStr) -> Array:
        bodyid = self._get_bodyid(name)
        assert bodyid > -1, "Unknown joint %s" % name
        return self.model.body_quat[bodyid]

    @register_as_setter("quat")
    def set_quat(self, name: AnyStr, value: Array) -> None:
        value = list(value)
        assert len(value) == 4, "Expected value of length 4, instead got %s" % value
        bodyid = self._get_bodyid(name)
        assert bodyid > -1, "Unknown joint %s" % name
        self.model.body_quat[bodyid] = value
        self.update()


class MujocoActuatorModifier(MujocoBaseModifier):

    def __init__(self, *args, **kwargs) -> None:
        self._default_config_file_path = 'data/mujoco/default_actuator_config.yaml'
        super().__init__(*args, **kwargs)

    @property
    def names(self) -> List:
        return self.model.actuator_names

    def _get_actuatorid(self, name: AnyStr) -> int:
        assert self.model.actuator_name2id(name) > -1, "Unknown actuator %s" % name
        return self.model.actuator_name2id(name)

    @register_as_setter("gear")
    def set_gear(self, name: AnyStr, value: Union[float, Array]) -> None:
        actuatorid = self._get_actuatorid(name)

        if isinstance(value, float):
            value = [value, 0.0, 0.0, 0.0, 0.0, 0.0]
        elif len(value) < 6:
            assert len(value) <= 6, "Expected value of max. length 6, instead got %s" % value
            value = [value[i] if i < len(value) else 0.0 for i in range(6)]

        self.model.actuator_gear[actuatorid] = value
        self.sim.set_constants()

    @register_as_setter("forcerange")
    def set_forcerange(self, name: AnyStr, value: Array) -> None:
        actuatorid = self._get_actuatorid(name)

        assert len(value) == 2, "Expected value of length 2, instead got %s" % value

        self.model.actuator_forcerange[actuatorid] = value
        self.sim.set_constants()

    @register_as_setter("ctrlrange")
    def set_ctrlrange(self, name: AnyStr, value: Array) -> None:
        actuatorid = self._get_actuatorid(name)

        assert len(value) == 2, "Expected value of length 2, instead got %s" % value

        self.model.actuator_ctrlrange[actuatorid] = value
        self.sim.set_constants()


class MujocoOptionModifier(MujocoBaseModifier):

    def __init__(self, *args, **kwargs) -> None:
        self._default_config_file_path = 'data/mujoco/default_option_config.yaml'
        super().__init__(*args, **kwargs)

    @property
    def names(self) -> List:
        return self.model.options

    @register_as_setter("gravity")
    def set_gravity(self, name: AnyStr = None, value: Union[float, Array] = -9.81) -> None:
        if isinstance(value, float):
            value = [0, 0, value]
        elif len(value) < 3:
            assert len(value) <= 3, "Expected value of max. length 3, instead got %s" % value
            value = list(reversed([value[i] if i < len(value) else 0 for i in range(3)]))
        elif len(value) == 3:
            pass
        else:
            raise ValueError
        self.model.opt.gravity[:] = value[:]
        self.update()

    @register_as_setter("viscosity")
    def set_viscosity(self, name: AnyStr = None, value: float = 0.0):
        assert value >= 0., "Expected viscosity value >= 0, instead got %s" % value

        self.sim.model.opt.viscosity = value

    @register_as_setter("density")
    def set_density(self, name: AnyStr = None, value: float = 0.0):
        assert value >= 0., "Expected density value >= 0, instead got %s" % value

        self.sim.model.opt.density = value
        
    @register_as_setter("timestep")
    def set_density(self, name: AnyStr = None, value: float = 0.0):
        assert value >= 0., "Expected timestep value >= 0, instead got %s" % value

        self.sim.model.opt.timestep = value


