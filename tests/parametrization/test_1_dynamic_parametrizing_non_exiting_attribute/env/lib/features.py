import balder
import random

class ProvidesANumberFeature(balder.Feature):

    the_number = 0

    def set_number(self, number):
        """user method that allows to set the number"""
        self.the_number = number

    def get_number(self):
        """returns the set number"""
        raise NotImplementedError("has to be implemented in subclass")

    def sends_the_number(self):
        """sends the set number"""
        raise NotImplementedError("has to be implemented in subclass")


class RandomNumberFeature(balder.Feature):

    def get_random_numbers(self):
        return [random.randint(1, 100) for _ in range(5)]


class AddCalculateFeature(balder.Feature):

    all_numbers = []

    def get_numbers(self):
        """this method get all the single numbers that should be calculated"""
        raise NotImplementedError("has to be implemented in subclass")

    def add_numbers(self):
        """this method adds all the numbers"""
        raise NotImplementedError("has to be implemented in subclass")
