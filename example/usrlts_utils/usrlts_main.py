import os
import time
import json
import math
import numpy
import pandas
import argparse
import torch
from scipy.io import arff

from usrlts import scikit_wrappers


def get_config():

    parser = argparse.ArgumentParser(description='Classification tests for UCR/UEA repository datasets')

    parser.add_argument('--dataset', type=str, default='data', help='dataset name')
    parser.add_argument('--path', type=str, default='./', help='path where the dataset is located')
    parser.add_argument('--save_path', type=str, default='output', 
                        help='path where the estimator is/should be saved')
    
    parser.add_argument('--cuda', action='store_true', default=False, help='activate to use CUDA')
    parser.add_argument('--gpu', type=int, default=0, 
                        help='index of GPU used for computations (default: 0)')
    
    parser.add_argument('--hyper', type=str, default='example/usrlts_utils/default_hyperparameters.json', 
                        help='path of the file of hyperparameters to use; for training; must be a JSON file')
    parser.add_argument('--load', action='store_true', default=False, 
                        help='activate to load the estimator instead of training it')
    parser.add_argument('--fit_classifier', action='store_true', default=False, 
                        help='if not supervised, activate to load the model and retrain the classifier')

    # config = parser.parse_known_args()[0]
    config = parser.parse_args(args=[])
    # print(config)
    
    return config


def fit_hyperparameters(file, train, train_labels, cuda, gpu,
                        save_memory=False):
    """
    Creates a classifier from the given set of hyperparameters in the input
    file, fits it and return it.

    @param file Path of a file containing a set of hyperparemeters.
    @param train Training set.
    @param train_labels Labels for the training set.
    @param cuda If True, enables computations on the GPU.
    @param gpu GPU to use if CUDA is enabled.
    @param save_memory If True, save GPU memory by propagating gradients after
           each loss term, instead of doing it after computing the whole loss.
    """
    classifier = scikit_wrappers.CausalCNNEncoderClassifier()

    # Loads a given set of hyperparameters and fits a model with those
    hf = open(os.path.join(file), 'r')
    params = json.load(hf)
    hf.close()
    # Check the number of input channels
    params['in_channels'] = numpy.shape(train)[1]
    params['cuda'] = cuda
    params['gpu'] = gpu
    classifier.set_params(**params)
    return classifier.fit(
        train, train_labels, save_memory=save_memory, verbose=True
    )


def load_UCR_dataset(path, dataset):
    """
    Loads the UCR dataset given in input in numpy arrays.

    @param path Path where the UCR dataset is located.
    @param dataset Name of the UCR dataset.

    @return Quadruplet containing the training set, the corresponding training
            labels, the testing set and the corresponding testing labels.
    """
    train_file = os.path.join(path, dataset, dataset + "_TRAIN.tsv")
    test_file = os.path.join(path, dataset, dataset + "_TEST.tsv")
    train_df = pandas.read_csv(train_file, sep='\t', header=None)
    test_df = pandas.read_csv(test_file, sep='\t', header=None)
    train_array = numpy.array(train_df)
    test_array = numpy.array(test_df)

    # Move the labels to {0, ..., L-1}
    labels = numpy.unique(train_array[:, 0])
    transform = {}
    for i, l in enumerate(labels):
        transform[l] = i

    train = numpy.expand_dims(train_array[:, 1:], 1).astype(numpy.float64)
    train_labels = numpy.vectorize(transform.get)(train_array[:, 0])
    test = numpy.expand_dims(test_array[:, 1:], 1).astype(numpy.float64)
    test_labels = numpy.vectorize(transform.get)(test_array[:, 0])

    # Normalization for non-normalized datasets
    # To keep the amplitude information, we do not normalize values over
    # individual time series, but on the whole dataset
    if dataset not in [
        'AllGestureWiimoteX',
        'AllGestureWiimoteY',
        'AllGestureWiimoteZ',
        'BME',
        'Chinatown',
        'Crop',
        'EOGHorizontalSignal',
        'EOGVerticalSignal',
        'Fungi',
        'GestureMidAirD1',
        'GestureMidAirD2',
        'GestureMidAirD3',
        'GesturePebbleZ1',
        'GesturePebbleZ2',
        'GunPointAgeSpan',
        'GunPointMaleVersusFemale',
        'GunPointOldVersusYoung',
        'HouseTwenty',
        'InsectEPGRegularTrain',
        'InsectEPGSmallTrain',
        'MelbournePedestrian',
        'PickupGestureWiimoteZ',
        'PigAirwayPressure',
        'PigArtPressure',
        'PigCVP',
        'PLAID',
        'PowerCons',
        'Rock',
        'SemgHandGenderCh2',
        'SemgHandMovementCh2',
        'SemgHandSubjectCh2',
        'ShakeGestureWiimoteZ',
        'SmoothSubspace',
        'UMD'
    ]:
        return train, train_labels, test, test_labels
    # Post-publication note:
    # Using the testing set to normalize might bias the learned network,
    # but with a limited impact on the reported results on few datasets.
    # See the related discussion here: https://github.com/White-Link/UnsupervisedScalableRepresentationLearningTimeSeries/pull/13.
    mean = numpy.nanmean(numpy.concatenate([train, test]))
    var = numpy.nanvar(numpy.concatenate([train, test]))
    train = (train - mean) / math.sqrt(var)
    test = (test - mean) / math.sqrt(var)
    return train, train_labels, test, test_labels


def load_UEA_dataset(path, dataset):
    """
    Loads the UEA dataset given in input in numpy arrays.

    @param path Path where the UCR dataset is located.
    @param dataset Name of the UCR dataset.

    @return Quadruplet containing the training set, the corresponding training
            labels, the testing set and the corresponding testing labels.
    """
    # Initialization needed to load a file with Weka wrappers
    train_file = os.path.join(path, dataset, dataset + "_TRAIN.arff")
    test_file = os.path.join(path, dataset, dataset + "_TEST.arff")
    train_weka = pandas.DataFrame(arff.loadarff(train_file)[0])
    test_weka = pandas.DataFrame(arff.loadarff(test_file)[0])

    train_size = train_weka.shape[0]
    test_size = test_weka.shape[0]
    nb_dims = train_weka.iloc[0, 0].shape[0]
    length = len(train_weka.iloc[0, 0][0])

    train = numpy.empty((train_size, nb_dims, length))
    test = numpy.empty((test_size, nb_dims, length))
    train_labels = numpy.empty(train_size, dtype=numpy.int)
    test_labels = numpy.empty(test_size, dtype=numpy.int)

    labels_list = train_weka.iloc[:, 1].drop_duplicates()
    labels_dict = dict(zip(labels_list, range(labels_list.shape[0])))
    print(labels_dict)

    for i in range(train_size):
        train_labels[i] = labels_dict[train_weka.iloc[i, 1]]
        for j in range(nb_dims):
            train[i, j] = list(train_weka.iloc[i, 0][j])

    for i in range(test_size):
        test_labels[i] = labels_dict[test_weka.iloc[i, 1]]
        for j in range(nb_dims):
            test[i, j] = list(test_weka.iloc[i, 0][j])

    # Normalizing dimensions independently
    for j in range(nb_dims):
        # Post-publication note:
        # Using the testing set to normalize might bias the learned network,
        # but with a limited impact on the reported results on few datasets.
        # See the related discussion here: https://github.com/White-Link/UnsupervisedScalableRepresentationLearningTimeSeries/pull/13.
        mean = numpy.mean(numpy.concatenate([train[:, j], test[:, j]]))
        var = numpy.var(numpy.concatenate([train[:, j], test[:, j]]))
        train[:, j] = (train[:, j] - mean) / math.sqrt(var)
        test[:, j] = (test[:, j] - mean) / math.sqrt(var)

    # Move the labels to {0, ..., L-1}
    labels = numpy.unique(train_labels)
    transform = {}
    for i, l in enumerate(labels):
        transform[l] = i
    train_labels = numpy.vectorize(transform.get)(train_labels)
    test_labels = numpy.vectorize(transform.get)(test_labels)

    return train, train_labels, test, test_labels


def run_usrlts(data_type, **kwargs):
    
    # start time
    start_time = time.time()
    print('Start: ', time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

    # get config
    args = get_config()
    for k in kwargs:
        args.__dict__[k] = kwargs[k]
    print(args)

    # create output dir
    args.save_path = args.save_path + '/' + args.dataset
    if not os.path.exists(args.save_path):
        os.mkdir(args.save_path)

    if args.cuda and not torch.cuda.is_available():
        print("CUDA is not available, proceeding without it...")
        args.cuda = False

    if data_type == 'ucr':
        train, train_labels, test, test_labels = load_UCR_dataset(args.path, args.dataset)
    elif data_type == 'uea':
        train, train_labels, test, test_labels = load_UEA_dataset(args.path, args.dataset)
    print('train:', train.shape, 'test:', test.shape, '.')

    if not args.load and not args.fit_classifier:
        classifier = fit_hyperparameters(
            args.hyper, train, train_labels, args.cuda, args.gpu, save_memory=True)
    else:
        classifier = scikit_wrappers.CausalCNNEncoderClassifier()
        hf = open(os.path.join(args.save_path, args.dataset + '_hyperparameters.json'), 'r')
        hp_dict = json.load(hf)
        hf.close()
        hp_dict['cuda'] = args.cuda
        hp_dict['gpu'] = args.gpu
        classifier.set_params(**hp_dict)
        classifier.load(os.path.join(args.save_path, args.dataset))

    if not args.load:
        if args.fit_classifier:
            classifier.fit_classifier(classifier.encode(train), train_labels)
        classifier.save(
            os.path.join(args.save_path, args.dataset)
        )
        with open(
            os.path.join(
                args.save_path, args.dataset + '_hyperparameters.json'
            ), 'w'
        ) as fp:
            json.dump(classifier.get_params(), fp)

    print("Test accuracy: " + str(classifier.score(test, test_labels)))

    # end time
    end_time = time.time()
    print('End: ', time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
    # time consumed
    print('Took %f seconds' % (end_time - start_time))
