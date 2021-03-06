#This is the code that was used for cross validation. However it is not used in test.py .


import torch
from torch import nn
from torch.optim import SGD
import dlc_practical_prologue as prologue
# from plot import getMetrics, stats, plot_losses
from train import train_model_auxloss, train_model 
from helper_functions import normalize,computeAccuracy
from models import noWeightsharingnoAuxloss, weightsharingnoAuxloss, noWeightsharingAuxloss, weightsharingAuxloss, final_model, normalize



##description: CrossValidation function
##input: dictionary: a dictionary containing the various hyperparameter values with which we want to crossvalidate on.
##                    hyperparameters requires are: batch_size,lr,momentum and epochs
##                    example of dictionary: #hyperParam = dict()
                                            #hyperParam["lr"] = [0.1,0.01,0.001,0.0001]
                                            #hyperParam["batch_size"] = [16,32,50]#[5,8,10]
                                            #hyperParam["momentum"] = [0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9]
                                            #hyperParam["epochs"] = [25]
                                            #best_hyp_param = crossValidation(hyperParam,aux_loss = False)


         ##aux loss: a boolean specifying if the model uses auxiliary losses
##output: best_param: dictionary containing hyperparameters that had the highest average accuracy after training
def crossValidation(dictionary,aux_loss):
    #unpacking dictionary
    lrs = dictionary["lr"]
    batch_sizes = dictionary["batch_size"]
    momentums = dictionary["momentum"]
    epochs = dictionary["epochs"]
    #create variable containing best parameters
    best_param = {'lr': None,'batch_size': None,'momentum': None,'xavierGain': None, 'epochs': None ,'accuracy': 0.0}
    
    #create 3 folds
    fold1_input,fold1_target,fold1_classes,fold2_input,fold2_target,fold2_classes = prologue.generate_pair_sets(500)
    fold1_input = normalize(fold1_input).to(device)
    fold1_target = fold1_target.to(device)
    fold1_classes = fold1_classes.to(device)
    fold2_input = normalize(fold2_input).to(device)
    fold2_target = fold2_target.to(device)
    fold2_classes = fold2_classes.to(device)
    fold3_input,fold3_target,fold3_classes,_,_,_ = prologue.generate_pair_sets(500)
    fold3_input = normalize(fold3_input).to(device)
    fold3_target = fold3_target.to(device)
    fold3_classes = fold3_classes.to(device)
    
    #add folds in a list
    folds_inputs = [fold1_input,fold2_input,fold3_input]
    folds_targets = [fold1_target,fold2_target,fold3_target]
    folds_classes = [fold1_classes,fold2_classes,fold3_classes]
    train_input = torch.empty((folds_inputs[0].shape[0]*2,folds_inputs[0].shape[1],folds_inputs[0].shape[2],folds_inputs[0].shape[3])).to(device)

    #iterate through all possible combinations of hyper-parameters
    for epoch in epochs:
        for lr in lrs:
            for batch_size in batch_sizes:
                for momentum in momentums:
                    mean_accuracy = 0
                    k=0
                    print(f'epoch: {epoch}, lr:{lr} batch_size: {batch_size} momentum: {momentum}')
                    ## train and test 3 times (2 folds for train, 1 fold for test) 
                    for i in range(len(folds_inputs)):
                        for j in range(i+1,len(folds_inputs)):
                            #parameter to change within function (add model you want to cross validate on)
                            model = noWeightsharingnoAuxloss().to(device)
                            ##loading 2 folds to train data
                            train_input[:folds_inputs[i].shape[0]] = folds_inputs[i]
                            train_input[folds_inputs[i].shape[0]:] = folds_inputs[j]
                            train_input = normalize(train_input)
                            train_target = torch.cat((folds_targets[i],folds_targets[j]),dim =0).to(device)
                            train_classes = torch.cat((folds_classes[i],folds_classes[j]),dim = 0).to(device)
                            if i == 0 and j == 1:
                                k = 2
                            elif i==0 and j==2:
                                k = 1
                            else:
                                k = 0
                            #add last remaining fold to test data
                            test_input = folds_inputs[k].clone()
                            test_target = folds_targets[k].clone()
                            test_classes = folds_classes[k].clone()
                            criterion = nn.CrossEntropyLoss()
                            optimizer = torch.optim.SGD(model.parameters(), lr=lr,momentum=momentum,nesterov=False)
                            #if model uses aux_loss train with train_model_aux loss function otherwise train with train_model function
                            if aux_loss:
                                train_model_auxloss(model,train_input,train_target,train_classes,optimizer,criterion,test_input,test_target,mini_batch_size = batch_size,nb_epochs = epoch,print_progress= False)
                            else:
                                train_model(model ,train_input,train_target,optimizer,criterion,test_input,test_target,mini_batch_size = batch_size,nb_epochs = epoch,print_progress= False)
                            accuracy = computeAccuracy(model,test_input,test_target,aux_loss)
                            print("********************************************")
                            print(f'fold accuracy: {accuracy}')
                            print("********************************************")
                            mean_accuracy += accuracy
                        mean_accuracy = mean_accuracy/3
                        #if mean accuracy of 3 folds is better than previous mean accuracy, update best parameters
                        if mean_accuracy > best_param['accuracy']:
                            best_param = {'lr': lr,'batch_size': batch_size,'momentum': momentum, 'epochs': epoch ,'accuracy': mean_accuracy}
    return best_param




###hyper param that were used for cross validation##


