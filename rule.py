# -*- coding:utf-8 -*-
import pandas as pd
import os
import collections


def write_to_csv(mapping_df, output_path):
    if not os.path.isfile(output_path):
        mapping_df.to_csv(output_path, encoding='utf8', mode='w', header=True, index=False)
    else:
        mapping_df.to_csv(output_path, encoding='utf8', mode='a', header=False, index=False)


class Rule(object):

    def __init__(self, brandname):
        self.brandname = brandname

    @property
    def brandname(self):
        return self._brandname

    @brandname.setter
    def brandname(self, value):
        if isinstance(value, str):
            raise ValueError("Standard brand name must be iterable")
        if not isinstance(value, collections.Iterable):
            raise ValueError("Standard brand name must be iterable")
        if not all([isinstance(item, str) for item in value]):
            raise ValueError("All brandname should be string")
        self._brandname = value

    @property
    def rule(self):
        rule = list(map(self._format_rule, self._brandname))
        result_rule = pd.DataFrame(rule)
        return result_rule

    @staticmethod
    def _format_rule(brand):
        split_brandname = [n for n in brand.split('/')]
        space_list = []
        for alias in split_brandname:
            if ' ' in alias:
                new_alias = alias.replace(' ', '')
                space_list.append(new_alias)
        rule = split_brandname + space_list
        return {'output': brand, 'include': '|'.join(rule), 'equal': '', 'exclude': ''}

    def to_csv(self, output_path):
        self.rule.to_csv(output_path, encoding='utf8', mode='w', header=True, index=False)


def main():
    dirname = os.path.dirname(__file__)
    input_path = os.path.join(dirname, 'test_file/brand_standard_name.csv')
    output_path = os.path.join(dirname, 'test_file/mapping_rule.csv')
    standard_brand = pd.read_csv(input_path)['standard_brandname']
    standard_rule = Rule(standard_brand).rule
    standard_rule.to_csv(output_path)


if __name__ == '__main__':
    main()
