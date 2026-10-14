# Floating-point Python reference (XOR): each class has its own group of rules.
import numpy as np

class rule:
    def __init__(self, n_attributes, target_class, memorize_prob, forget_prob):
        self.states = [5 for _ in range(2 * n_attributes)]
        self.target_class = target_class
        self.memorize_prob = memorize_prob
        self.forget_prob = forget_prob

    def evaluate(self, sample):

        for i in range(len(sample)):
            idx = 2 * i
            if not sample[i] and self.states[idx] >= 6: #x_i
                return False
            if sample[i] and self.states[idx + 1] >= 6: #not x_i
                return False
        return True

    def update_state(self, sample):
        for i in range(len(sample)):
            idx = 2 * i
            temp = sample[i]
            for j in range(2):
                if temp:
                    if np.random.rand() <= self.memorize_prob:
                        self.states[idx + j] = min(10, self.states[idx + j] + 1)
                else:
                    if np.random.rand() <= self.forget_prob:
                        self.states[idx + j] = max(1, self.states[idx + j] - 1)
                temp = not temp

    def erase(self):
        for i in range(len(self.states)):
            if np.random.rand() <= self.forget_prob:
                self.states[i] = max(1, self.states[i] - 1)

    def reject(self, sample):
        for i in range(len(sample)):
            idx = 2 * i
            if not sample[i] and self.states[idx] <= 5:
                self.states[idx] += 1
            if sample[i] and self.states[idx + 1] <= 5:
                self.states[idx + 1] += 1

    def __str__(self) -> str:
        rep = ""
        for i in range(len(self.states)):
            if self.states[i] >= 6:
                if i % 2 == 0:
                    rep += f' x_{i >> 1} ^'
                else:
                    rep += f' not x_{i >> 1} ^'
        return rep[:len(rep) - 1]

dataset = [[0, 0, 0], [1, 0, 1], [0, 1, 1], [1, 1, 0]]

first_class_rules = [ rule(2, 0, 0.7, 0.3) for _ in range(5)]
second_class_rules = [ rule(2, 1, 0.7, 0.3) for _ in range(5)]

def update_rules(rules, dataset, T = 2):
    for sample in dataset:
        row = sample[:-1]
        y = sample[-1]
        correct_ones = 0
        incorrect_ones = 0
        for curr_rule in rules:
            if curr_rule.target_class == y:
                if curr_rule.evaluate(row):
                    correct_ones += 1
                else:
                    incorrect_ones += 1
        v = correct_ones - incorrect_ones
        p = (T - v) / (2 * T)

        for curr_rule in rules:
            if np.random.rand() > p:
                continue
            if curr_rule.target_class == y:

                if curr_rule.evaluate(row):
                    curr_rule.update_state(row)
                else:
                    curr_rule.erase()
            else:
                if curr_rule.evaluate(row):
                    curr_rule.reject(row)

for _ in range(100):
    np.random.shuffle(dataset)
    update_rules(first_class_rules, dataset)
    update_rules(second_class_rules, dataset)
matched = 0
for sample in dataset:
    row = sample[:-1]

    first_class_cnt = 0
    second_class_cnt = 0
    for curr_rule in first_class_rules:
        if curr_rule.evaluate(row):
            first_class_cnt += 1
    for curr_rule in second_class_rules:
        if curr_rule.evaluate(row):
            second_class_cnt += 1
    predicted = 0 if first_class_cnt > second_class_cnt else 1
    if predicted == sample[-1]:
        matched += 1
print(matched / 4)
