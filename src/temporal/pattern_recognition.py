"""LSTM-based exercise pattern recognition"""
import torch
import torch.nn as nn

class ExerciseClassifier(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super().__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, batch_first=True)
        self.fc = nn.Linear(hidden_size, num_classes)
    
    def forward(self, x):
        _, (hidden, _) = self.lstm(x)
        return self.fc(hidden.squeeze(0))
