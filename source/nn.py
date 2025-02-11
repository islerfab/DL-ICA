#!C:\Users\jakob\Anaconda3\pythonw.exe
# -*- coding: utf-8 -*-

"""
FILE DESCRIPTION:

This file implements the class NN (Neural Network) that has the following functionalities:
    0.CONSTRUCTOR:  __init__(self, model_parameters, X_train, Y_train, scaler)
        model_parameters = the parameters specifying the neural network:
        *(X_train,Y_train) is the training set of bundle-value pairs*.
        X_train = The bundles of items
        Y_train = The corresponding values for the bundles from a specific bidder. If alreday scaled to a vertai range than you also have to set the scaler variable in teh folowing.
        scaler =  A scaler instance from sklearn.preprocessing.*, e.g., sklearn.preprocessing.MinMaxScaler(), which was used to scale the Y_train variables before creating a NN instance.
                  This instance ins used in the class NN for rescaling errors to the original scale, i.e., it is used as scaler.inverse_transform().
    1. METHOD: initialize_model(self, regularization_type=None)
        regularization_type = The regularization for the affine transofrmation between layers. 'l1': L1-Regularization, 'l2': L2-Regularization, 'l1_l2': Convex Combination of both L1 and L2- Regularization.
        This method initializes the attribute model in the class NN by defining the architecture and the parameters of the neural network.
    2. METHOD: fit(self, epochs, batch_size, X_valid=None, Y_valid=None, sample_weight=None)
        epochs = Number of epochs the neural network is trained
        batch_size = Batch size used in training
        X_valid = Test set of bundles
        Y_valid = Values for X_valid.
        sample_weight = weights vector for datapoints of bundle-value pairs.
        This method fits a neural network to data and returns loss numbers.
    3. METHOD: loss_info(self, batch_size, plot=True, scale=None)
        batch_size = Batch size used in training
        plot = boolean parameter if a plots for the goodness of fit should be executed.
        scale = either None or 'log' defining the scaling of the y-axis for the plots
        This method calculates losses on the training set and the test set (if specified) and plots a goodness of fit plot.

See test_nn.py for an example of how to use the class NN.

"""

# Libs
import numpy as np
import logging
import matplotlib.pyplot as plt
from keras import regularizers, optimizers
from keras.models import Model
from keras.layers import Input, Dense, Dropout


__author__ = 'Jakob Weissteiner'
__copyright__ = 'Copyright 2019, Deep Learning-powered Iterative Combinatorial Auctions: Jakob Weissteiner and Sven Seuken'
__license__ = 'AGPL-3.0'
__version__ = '0.1.0'
__maintainer__ = 'Jakob Weissteiner'
__email__ = 'weissteiner@ifi.uzh.ch'
__status__ = 'Dev'

# %% NN Class for each bidder


class NN:

    def __init__(self, model_parameters, X_train, Y_train, scaler):

        self.M = X_train.shape[1]  # number of items
        self.X_train = X_train  # training set of bundles
        self.Y_train = Y_train  # bidder's values for the bundels in X_train
        self.X_valid = None   # test/validation set of bundles
        self.Y_valid = None  # bidder's values for the bundels in X_valid
        self.model_parameters = model_parameters  # neural network parameters
        self.model = None  # keras model, i.e., the neural network
        self.scaler = scaler  # the scaler used fro initially scaling the Y_train values
        self.history = None  # return value of the model.fit() method from keras
        self.loss = None  # return value of the model.fit() method from keras

    def initialize_model(self, regularization_type=None):
        r, lr, dim, dropout, dp = self.model_parameters  # model parameters is a tuple:(r=regularization_parameters,lr=learning rate for ADAM, dim=number and dimension of hidden layers, dropout=boolean if dropout is used in trainig, dp=dropout rate)
        dim = [int(d) for d in dim]
        number_of_hidden_layers = len(dim)
        dropout = bool(dropout)
        # -------------------------------------------------- NN Architecture -------------------------------------------------#
        # define input layer
        inputs = Input(shape=(self.X_train.shape[1], ))
        # set regularization
        if regularization_type == 'l2' or regularization_type is None:
            REG = regularizers.l2(r)
            logging.debug('l2 regularization')
        if regularization_type == 'l1':
            REG = regularizers.l1(r)
            logging.debug('l1 regularization')
        if regularization_type == 'l1_l2':
            logging.debug('l1&l2 regularization')
            REG = regularizers.l1_l2(r)
        # first hidden layer
        x = Dense(dim[0], kernel_regularizer=REG, bias_regularizer=REG, activation='relu')(inputs)
        if dropout is True:
            x = Dropout(rate=dp)(x)
        # remaining hidden layer
        for k in range(1, number_of_hidden_layers):
            x = Dense(dim[k], kernel_regularizer=REG, bias_regularizer=REG, activation='relu')(x)
            if dropout is True:
                x = Dropout(rate=dp)(x)
        # final output layer
        predictions = Dense(1, activation='relu')(x)
        model = Model(inputs=inputs, outputs=predictions)
        # ADAM = adaptive moment estimation a first-order gradient-based optimization algorithm
        ADAM = optimizers.Adam(lr=lr, beta_1=0.9, beta_2=0.999, epsilon=None, decay=0.0, amsgrad=False)
        # compile the model and define the loss function
        model.compile(optimizer=ADAM, loss='mean_absolute_error')
        # -------------------------------------------------- NN Architecture -------------------------------------------------#
        self.model = model
        logging.debug('Neural Net initialized')

    def fit(self, epochs, batch_size, X_valid=None, Y_valid=None, sample_weight=None):
        # set test set if desired
        self.X_valid = X_valid
        self.Y_valid = Y_valid
        # fit model and validate on test set
        if (self.X_valid is not None) and (self.Y_valid is not None):
            self.history = self.model.fit(self.X_train, self.Y_train, sample_weight=sample_weight, verbose=0, epochs=epochs, batch_size=batch_size, validation_data=(self.X_valid, self.Y_valid))
            # get loss infos
            loss = self.loss_info(batch_size, plot=False)
        # fit model without validating on test set
        else:
            self.history = self.model.fit(self.X_train, self.Y_train, sample_weight=sample_weight, verbose=0, epochs=epochs, batch_size=batch_size)
            # get loss infos
            loss = self.loss_info(batch_size, plot=False)
        return(loss)

    def loss_info(self, batch_size, plot=True, scale=None):
        logging.debug('Model Parameters: %s', self.model_parameters)
        tr = None
        tr_orig = None
        val = None
        val_orig = None
        # if scaler attribute was specified
        if self.scaler is not None:
            # errors on the training set
            tr = self.model.evaluate(self.X_train, self.Y_train, verbose=0)
            tr_orig = float(self.scaler.inverse_transform([[tr]]))
            if (self.X_valid is not None) and (self.Y_valid is not None):
                # errors on the test set
                val = self.model.evaluate(self.X_valid, self.Y_valid, verbose=0)
                val_orig = float(self.scaler.inverse_transform([[val]]))
        # data has not been scaled by scaler, i.e., scaler == None
        else:
            tr_orig = self.model.evaluate(self.X_train, self.Y_train, verbose=0)
            if (self.X_valid is not None) and (self.Y_valid is not None):
                val_orig = self.model.evaluate(self.X_valid, self.Y_valid, verbose=0)
        # print errors
        if tr is not None:
            logging.debug('Train Error Scaled %s', tr)
        if val is not None:
            logging.debug('Validation Error Scaled %s', val)
        if tr_orig is not None:
            logging.debug('Train Error Orig. %s', tr_orig)
        if val_orig is not None:
            logging.debug('Validation Error Orig %s', val_orig)

        # plot results
        if plot is True:
            # recalculate predicted values for the training set and test set, which are used for the true vs. predicted plot.
            Y_hat_train = self.model.predict(self.X_train, batch_size=batch_size).flatten()
            if (self.X_valid is not None) and (self.Y_valid is not None):
                Y_hat_valid = self.model.predict(self.X_valid, batch_size=batch_size).flatten()
            fig, ax = plt.subplots(1, 2)
            plt.subplots_adjust(hspace=0.3)
            if scale == 'log':
                ax[0].set_yscale('log')
            ax[0].plot(self.history.history['loss'])
            if (self.X_valid is not None) and (self.Y_valid is not None):
                ax[0].plot(self.history.history['val_loss'])
            ax[0].set_title('Training vs. Test Loss DNN', fontsize=30)
            ax[0].set_ylabel('Mean Absolute Error', fontsize=25)
            ax[0].set_xlabel('Number of Epochs', fontsize=25)
            ax[0].legend(['Train', 'Test'], loc='upper right', fontsize=20)
            ax[1].plot(Y_hat_train, self.Y_train, 'bo')
            ax[1].set_ylabel('True Values', fontsize=25)
            ax[1].set_xlabel('Predicted Values', fontsize=25)
            ax[1].set_title('Prediction Accuracy', fontsize=30)

            if (self.X_valid is not None) and (self.Y_valid is not None):
                ax[1].plot(Y_hat_valid, self.Y_valid, 'go')
            ax[1].legend(['Training Points', 'Test Points'], loc='upper left', fontsize=20)
            lims = [
                np.min([ax[1].get_xlim(), ax[1].get_ylim()]),  # min of both axes
                np.max([ax[1].get_xlim(), ax[1].get_ylim()]),  # max of both axes
            ]
            ax[1].plot(lims, lims, 'k-')
            ax[1].set_aspect('equal')
            ax[1].set_xlim(lims)
            ax[1].set_ylim(lims)
        return((tr, val, tr_orig, val_orig))
# %%


print('NN Class imported')
