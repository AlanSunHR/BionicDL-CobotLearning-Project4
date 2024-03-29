
"""Train the google's grasp network.

This scrip uses google's TFRecords files containing tf.train.Example protocol buffers.
https://github.com/tensorflow/tensorflow/blob/master/tensorflow/examples/how_tos/reading_data/fully_connected_reader.py
https://github.com/tensorflow/models/blob/master/tutorials/image/cifar10/cifar10_train.py

By Fang Wan
"""
import time
import os

from graspNet import model as grasp_net
import tensorflow as tf

# 40, 10min/epoch;
batch_size = 128
num_epochs = 15
use_gpu_fraction = 1
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

max_learning_rate = 0.001
min_learning_rate = 0.0001
decay_speed = 1000

checkpoint_path = './checkpoint'
summary_path = './summary'
data_path = './croppedImage_tfrecord'

NUM_THETAS = 18
NUM_CLASSES = 2
def parse_examp(tf_record_serialized):
    tf_record_features = tf.parse_single_example(
        tf_record_serialized,
        features={
        'success': tf.FixedLenFeature([], tf.float32),
        'img_00': tf.FixedLenFeature([], tf.string),
        'rotate_angle': tf.FixedLenFeature([1], tf.float32)
        })
    img = tf_record_features['img_00']
    grasp = tf.decode_raw(img, tf.uint8)
    image = tf.reshape(grasp, [227, 227,3])
    image = tf.cast(image, tf.float32)
    image -= 164.0
    label = tf.cast(tf_record_features['success'], tf.float32)  #[size]
    theta = tf.cast(tf_record_features['rotate_angle'], tf.float32) + 3.14 #[size]
    T_index = tf.floordiv(theta, 2*3.14/NUM_THETAS)+1
    return image, T_index*100, tf.one_hot(tf.to_int32(label), NUM_CLASSES)

def run_training():
    # Tell TensorFlow that the model will be built into the default Graph.
    with tf.Graph().as_default():
        global_step = tf.Variable(0, name='global_step', trainable=False)

        # list of all the tfrecord files
        buffer_size = 1000
        TRAIN_FILES = ['./croppedImage_tfrecord/croppedImage_beta_%s.tfrecord'%i for i in range(10)]
        dataset = tf.data.TFRecordDataset(TRAIN_FILES)
        dataset = dataset.map(parse_examp)
        dataset = dataset.repeat(num_epochs).shuffle(buffer_size).batch(batch_size)
        iterator = dataset.make_one_shot_iterator()
        images_batch, thetas_batch, labels_batch = iterator.get_next()

        # Build a Graph that computes predictions from the inference model.
        model = grasp_net()
        model.initial_weights(weight_file='./bvlc_alexnet.npy')
        logits = model.inference(images_batch, thetas_batch)
        y = tf.nn.softmax(logits)
        # Add to the Graph the loss calculation.
        loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels = labels_batch, logits = logits), name='xentropy_mean')

        # accuracy of the trained model
        correct_prediction = tf.equal(tf.argmax(y, 1), tf.argmax(labels_batch, 1))
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))

        # Add GPU config, now maximun using 80% GPU memory to train
        config = tf.ConfigProto()
        config.gpu_options.per_process_gpu_memory_fraction = use_gpu_fraction

        # Add to the Graph operations that train the model.
        learning_rate = min_learning_rate + (max_learning_rate - min_learning_rate) * tf.exp(-tf.cast(global_step, tf.float32)/decay_speed)
        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS)
        with tf.control_dependencies(update_ops):
            optimizer = tf.train.AdamOptimizer(learning_rate)
            train_op = optimizer.minimize(loss, global_step=global_step)

        # The op for initializing the variables.
        init_op = tf.group(tf.global_variables_initializer(), tf.local_variables_initializer())
        sess = tf.Session(config=config)
        sess.run(init_op)

        # Add summary writer
        tf.summary.scalar('loss', loss)
        tf.summary.scalar('accuracy', accuracy)
        tf.summary.scalar('learning rate', learning_rate)
        for var in tf.trainable_variables():
            tf.summary.histogram(var.name,var)
        merged_summary_op = tf.summary.merge_all()
        if not os.path.isdir(summary_path):
            os.mkdir(summary_path)
        summary_writer = tf.summary.FileWriter(summary_path, graph=tf.get_default_graph())

        # Add saver
        saver = tf.train.Saver(max_to_keep=10)
        if not os.path.isdir(checkpoint_path):
            os.mkdir(checkpoint_path)
        checkpoint = tf.train.latest_checkpoint(checkpoint_path)
        if checkpoint:
            saver.restore(sess, checkpoint)

        coord = tf.train.Coordinator()
        threads = tf.train.start_queue_runners(sess=sess, coord=coord)

        try:
            step = 0
            while not coord.should_stop():
                start_time = time.time()
                # Run one step of the model
                _, loss_value, accuracy_value, global_step_value, summary = sess.run([train_op, loss, accuracy,global_step, merged_summary_op])
                # Use TensorBoard to record
                summary_writer.add_summary(summary, global_step_value)
                duration = time.time() - start_time
                if step % 10 == 0:
                    print('Step %d: loss = %.2f accuracy = %.2f (%.3f sec)' % (step, loss_value, accuracy_value, duration))
                if global_step_value % 100 == 0:
                    saver.save(sess, checkpoint_path + '/Network', global_step = global_step)
                step += 1
        except tf.errors.OutOfRangeError:
            print('Done training -- epoch limit reached')
        finally:
            # When done, ask the threads to stop.
            coord.request_stop()

        # Wait for threads to finish.
        coord.join(threads)
        saver.save(sess, checkpoint_path + '/Network', global_step = global_step)
        sess.close()

def main(_):
    run_training()

if __name__ == '__main__':
    tf.app.run()
