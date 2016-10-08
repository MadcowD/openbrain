# -----------------------------------
# Deep Deterministic Policy Gradient
# Author: William Guss
# Date: 2016.5.4
# -----------------------------------
import gym
import tensorflow as tf
import numpy as np
from ddpg import DDPG
from common.critic_network import CriticNetwork
from common.actor_network import ActorNetwork
from common.replay_buffer import ReplayBuffer

from polynomial_critic import PolynomialCritic

LEARNING_RATE=1e-3

class SubCritics:
    def __init__(self, ddpg_agent : DDPG, order=1, verbose=False):
        """
        Initializes the subcritics based on a particular ddpg agent.
        ORDER is currently unused.
        """
        self.agent = ddpg_agent
        self.sess = ddpg_agent.sess
        self.actor = ddpg_agent.actor_network
        self.critics = []
        self.activation_inputs = []
        self.t_activation_inputs = []

        self.reward_input =  tf.placeholder("float",[None], name="reward") 

        self.verbose = verbose

        #TODO Build the rest of the subcritic system.
        # actor.layers = [state, output_layer1, output_layer2, output_layer3, ..., action = output_layer[-1]]
        for l, layer in enumerate(self.actor.layers[:-1]):
            # This could be cleaned up.
            # Make the placeholders

            action_dim = self.actor.layers[l+1].get_shape()[1] # Only works for 1d
            state_dim = layer.get_shape()[1]
            if not self.activation_inputs:
                self.activation_inputs = [
                    tf.placeholder("float",[None,state_dim], name="activ_{}".format(l))]
            state_input = self.activation_inputs[-1] 
            action_input = tf.placeholder("float",[None,action_dim], name="activ_{}".format(l+1))


            self.activation_inputs += [action_input]

            if not self.t_activation_inputs:
                self.t_activation_inputs = [
                    tf.placeholder("float",[None,state_dim], name="t_activ_{}".format(l))]
            t_state_input = self.t_activation_inputs[-1]
            t_action_input = tf.placeholder("float",[None,action_dim], name="t_activ_{}".format(l+1))

            self.t_activation_inputs += [t_action_input]

            # Now make the sub critic laeyr.

            with tf.variable_scope("subcritic_layer{}".format(l)):

                # Make a true and target placeholders (This is an optimization)
                
                b_size = tf.shape(state_input)[0]
                #Create critics for each input
                for j in range(action_dim):
                    with tf.variable_scope("subcritic_n{}".format(l,j)):
                        self.critics.append(
                            PolynomialCritic(
                                self.sess,
                                state_input, tf.reshape(action_input[:,j], tf.pack([b_size, 1])),
                                t_state_input, tf.reshape(t_action_input[:,j], tf.pack([b_size, 1])),
                                self.reward_input,
                                order))

        # Create optimizer on all critics
        with tf.variable_scope("subcritic_training"):
            constituent_loss = [cn.loss for cn in self.critics]
            self.loss = tf.add_n(constituent_loss)
            self.optimizer = tf.train.AdamOptimizer(LEARNING_RATE).minimize(self.loss)

        self.target_update = [cn.target_update for cn in self.critics]

    def perceive(self, activations, reward, done):
        self.sess.run(self.target_update)

        # In here do exactly the same method as ddpg for training its critic except do it
        # for all critics.

        # Activations is the output of [state, output_layer1, output_layer2, output_layer3, ..., action = output_layer[-1]]

        # We need to make a replay buffer for the subcritics be a window of the last N time steps.
        # So do not use the replay buffer used for normal DDPG
        pass

    def q(self, activations):
        """
        Return the Q of every single subcritic for plotting
        """
        # alternative if we need target output in addtion to q_value
        # return [(sc.q_value_output, sc.target_q_value_output) for sc in self.critics]
        return [sc.q_value_output for sc in self.critics]
