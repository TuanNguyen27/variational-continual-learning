import numpy as np
import tensorflow as tf
import utils
from cla_models_multihead import Vanilla_NN, MFVI_NN, CVI_NN
import pdb

def run_vcl(hidden_size, no_epochs, data_gen, coreset_method, coreset_size=0, batch_size=None, single_head=True):
    in_dim, out_dim = data_gen.get_dims()
    x_coresets, y_coresets = [], []
    x_testsets, y_testsets = [], []

    all_acc = np.array([])

    for task_id in list(range(data_gen.max_iter)):
        x_train, y_train, x_test, y_test = data_gen.next_task()
        x_testsets.append(x_test)
        y_testsets.append(y_test)

        # Set the readout head to train
        head = 0 if single_head else task_id
        bsize = x_train.shape[0] if (batch_size is None) else batch_size

        # Train network with maximum likelihood to initialize first model
        if task_id == 0:
            mf_variances = None
            mf_weights = None

        # Select coreset if needed
        if coreset_size > 0:
            x_coresets, y_coresets, x_train, y_train = coreset_method(x_coresets, y_coresets, x_train, y_train, coreset_size)

        # Train on non-coreset data
        mf_model = CVI_NN(in_dim, hidden_size, out_dim, x_train.shape[0], prev_means=mf_weights, prev_log_variances=mf_variances)
        no_epochs = 0 if task_id == 1 else 10
        mf_model.train(x_train, y_train, head, no_epochs, bsize)
        mf_weights, mf_variances = mf_model.create_weights()
        prev_mf_weights, prev_mf_variances = mf_weights, mf_variances
        # sess = mf_model.sess
        # with sess.as_default():
        #     if not (mf_weights and mf_variances):
        #         print(sess.run(mf_weights))
        #         print(sess.run(mf_variances))
        #         mf_weights = sess.run(mf_weights)
        #         mf_variances = sess.run(mf_variances)
        #import pdb; pdb.set_trace()


        # Incorporate coreset data and make prediction
        acc = utils.get_scores(mf_model, x_testsets, y_testsets, x_coresets, y_coresets, hidden_size, no_epochs, single_head, batch_size)
        all_acc = utils.concatenate_results(acc, all_acc)
        print(acc)
        mf_model.close_session()

    return all_acc
