import tensorflow as tf


SAME_PADDING = "SAME"


class ConvoModel(object):

    def __init__(self, config):

        self._config = config

    def initialize(self, x):

        # first convolution layer: output_shape (batch_size, 16, 16, 64)
        self._convo_1 = self._get_convo_layer(
            x,
            a_function=tf.sigmoid,
            size=5,
            in_channels=3,
            out_channels=64,
            stride=1,
            name="convo_1"
        )

        self._max_pool_1 = self._get_max_pool_layer(
            self._convo_1,
            size=3,
            stride=2,
            name="max_pool_1"
        )

        # second convolution layer: output_shape (batch_size, 8, 8, 64)
        self._convo_2 = self._get_convo_layer(
            self._max_pool_1,
            a_function=tf.sigmoid,
            size=2,
            in_channels=64,
            out_channels=64,
            stride=1,
            name="convo_2"
        )

        self._max_pool_2 = self._get_max_pool_layer(
            self._convo_2,
            size=2,
            stride=2,
            name="max_pool_2"
        )

        # densely-connected network
        self._dense_layer_1 = self._get_dense_layer(
            tf.reshape(self._max_pool_2, (100, -1)),
            input_size=8*8*64,
            hidden_units=2048,
            a_function=tf.sigmoid,
            name="dense_layer_1"
        )

        self._dense_layer_2 = self._get_dense_layer(
            self._dense_layer_1,
            input_size=2048,
            hidden_units=1024,
            a_function=tf.sigmoid,
            name="dense_layer_2"
        )

        # softmax layer
        self._softmax_logit, self._softmax_layer = self._get_softmax_layer(
            self._dense_layer_2,
            input_size=1024,
            output_size=10,
            name="softmax"
        )

    def train_op(self, y, global_step):

        self._softmax_loss_layer = tf.nn.sparse_softmax_cross_entropy_with_logits(
            self._softmax_logit,
            y
        )

        optimizer = tf.train.GradientDescentOptimizer(0.01)

        loss = tf.reduce_mean(self._softmax_loss_layer)

        tf.scalar_summary("loss", loss)

        return loss, optimizer.minimize(loss, global_step)

    def infer(self):

        return self._softmax_layer

    def _get_convo_layer(
            self,
            input,
            a_function,
            size,
            in_channels,
            out_channels,
            stride,
            padding_config=SAME_PADDING,
            name=""):

        weights = tf.get_variable(
            "%s_weights" % name,
            shape=(size, size, in_channels, out_channels),
            initializer=tf.truncated_normal_initializer(
                stddev=5e-2,
                dtype=tf.float32
            )
        )

        biases = tf.get_variable(
            "%s_biases" % name,
            shape=(out_channels),
            initializer=tf.constant_initializer(0.0)
        )

        convo = tf.nn.conv2d(
            input,
            weights,
            strides=(1, stride, stride, 1),
            padding=padding_config,
            name=name
        )

        convo = tf.nn.bias_add(convo, biases)

        return a_function(convo)

    def _get_max_pool_layer(
        self,
        input,
        size,
        stride,
        padding_config=SAME_PADDING,
        name=""
    ):

        return tf.nn.max_pool(
            input,
            ksize=[1, size, size, 1],
            strides=[1, stride, stride, 1],
            padding=padding_config,
            name=name
        )

    def _get_dense_layer(
        self,
        input,
        input_size,
        hidden_units,
        a_function,
        name=""
    ):

        weights = tf.get_variable(
            "%s_weights" % name,
            shape=(input_size, hidden_units),
            initializer=tf.truncated_normal_initializer(
                stddev=5e-2,
                dtype=tf.float32
            )
        )

        biases = tf.get_variable(
            "%s_biases" % name,
            shape=(hidden_units),
            initializer=tf.constant_initializer(0.0)
        )

        return a_function(tf.matmul(input, weights) + biases)

    def _get_softmax_layer(
        self,
        input,
        input_size,
        output_size,
        name=""
    ):

        weights = tf.get_variable(
            "%s_weights" % name,
            shape=(input_size, output_size),
            initializer=tf.truncated_normal_initializer(
                    stddev=5e-2,
                    dtype=tf.float32
            )
        )

        biases = tf.get_variable(
            "%s_biases" % name,
            shape=(output_size),
            initializer=tf.constant_initializer(0.0)
        )

        logits = tf.matmul(input, weights) + biases

        return logits, tf.nn.softmax(logits)
