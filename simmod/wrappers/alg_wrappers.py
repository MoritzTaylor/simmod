import gym
from gym import Env

from simmod.algorithms import UniformDomainRandomization
from simmod.modification.mujoco.mujoco_modifier import MujocoBaseModifier
from simmod.common.parametrization import Execution


class UDRMujocoWrapper(gym.Wrapper):
    """
    Implements the Uniform Domain Randomization algorithm for Mujoco simulations in an OpenAI Gym wrapper.
    """

    def __init__(self, env: Env, *modifiers: MujocoBaseModifier):
        super(UDRMujocoWrapper, self).__init__(env)
        assert env.unwrapped.sim is not None, "Assuming a Gym environment with a Mujoco simulation at variable 'sim'"
        self.sim = env.unwrapped.sim

        self.alg = UniformDomainRandomization(*modifiers)
        self._setup_env_metadata()

    def _setup_env_metadata(self):
        range_values = dict()
        for mod in self.alg.modifiers:
            for param in mod.instrumentation:
                range_values[f'{param.setter}:{param.object_name}'] = param.parameter_range
        self.metadata['randomization.parameter_range'] = range_values

    def _update_env_metadata(self):
        param_values = dict()
        for mod in self.alg.modifiers:
            for param in mod.instrumentation:
                param_values[f'{param.setter}:{param.object_name}'] = self.alg.get_current_val(mod, param)
        self.metadata['randomization.parameter_value'] = param_values

    def step(self, action):
        #action = self.alg.step(Execution.BEFORE_STEP, action=action)
        observation, reward, done, info = self.env.step(action)
        #observation, reward, done, info = self.alg.step(execution=Execution.RESET,
        #                                                observation=observation, reward=reward, done=done, info=info)
        return observation, reward, done, info

    def reset(self, **kwargs):
        self.alg.step(Execution.RESET)
        #self.metadata['randomization.parameter_value'] = {f'{param.setter}:{param.object_name}': param.range_val for
        #                                                  param in self.alg.modifiers}
        observation = self.env.reset(**kwargs)
        self._update_env_metadata()
        return observation
